# 🎭 Phantom Whisper v2.0 — MONOLITHIC ULTIMATE EDITION

![Phantom Whisper Banner](phantom_whisper_banner.png)

> **"One file to rule them all."**

**Phantom Whisper v2.0** is the ultimate Android Red Team Framework — now in a **single self-installing Python file**. No dependencies to install manually. No separate modules. No configuration. Just run it.

---

## 🚀 Quick Start (Noob Level)

### Termux / Android — One-Liner

Copy-paste this into **Termux**:

```bash
pkg update -y && pkg install git python -y && git clone https://github.com/masterfrequency/Phantom-Whisper.git && cd Phantom-Whisper && python phantom_whisper.py --set-up && python phantom_whisper.py
```

This one command:
1. Updates Termux packages
2. Installs Python
3. Downloads Phantom Whisper
4. Launches the framework

**First run** auto-detects your OS, installs all Python dependencies, creates config, and starts the interactive menu. Zero manual steps.

### Linux / macOS

```bash
# Download and run in one step:
curl -sL https://raw.githubusercontent.com/masterfrequency/Phantom-Whisper/main/phantom_whisper.py -o phantom_whisper.py && python3 phantom_whisper.py
```

---

## 📋 Commands

| Command | What It Does |
|---|---|
| `python phantom_whisper.py` | Interactive Red Team Framework (17 modules) |
| `python phantom_whisper.py --server` | Start C2 server with web dashboard |
| `python phantom_whisper.py --install` | Install dependencies only |
| `python phantom_whisper.py --recon` | One-shot reconnaissance scan |
| `python phantom_whisper.py --help` | Show help |

---

## 🔥 Features (17 Built-In Modules)

### 🛡️ Encryption & Stealth
| Module | Description |
|---|---|
| **XChaCha20-Poly1305 Encryption** | AEAD cipher, 10x faster than AES. Falls back to Fernet (AES-128-CBC) |
| **PNG Steganography** | LSB hide/extract data in PNG/JPG images |
| **Code Obfuscation** | XOR + base64 string encoding against casual inspection |

### 🌐 Command & Control
| Module | Description |
|---|---|
| **DNS Tunnel C2** | Full-duplex beacon + exfil via base32-encoded DNS TXT queries |
| **HTTP CDN-Mimic C2** | Traffic disguised as CDN image loads with randomized UAs/referers |
| **WebSocket C2** | Persistent bidirectional real-time channel |
| **C2 Server** | Built-in async HTTP + WebSocket server with live dashboard |

### 🕵️ Reconnaissance
| Module | Description |
|---|---|
| **Port Scanner** | Multi-threaded TCP scanner with banner grabbing + service fingerprinting |
| **Network Scanner** | ICMP ping sweep + subnet auto-discovery |
| **Device Recon** | Interfaces, WiFi networks, ARP table, Bluetooth devices, running processes |
| **Geo-IP Resolver** | IP → country, city, ISP, GPS coordinates via 3 APIs |

### 🎭 Attack Modules (Authorized Testing Only)
| Module | Description |
|---|---|
| **AI Phishing Engine** | Template-based SMS + email generator (8 scenarios: bank, Netflix, Google, Apple, PayPal, security, shipping, crypto) |
| **Clipboard Monitor** | Real clipboard reader (5 backends) with 9 pattern detectors: BTC, ETH, API keys, private keys, seeds, emails, passwords, phones, 2FA codes |
| **Screenshot Capture** | Screen capture via 6 backends (scrot, ImageMagick, gnome-screenshot, screencapture, MSS, PIL) |
| **File Browser** | Remote file listing/read/write with path traversal protection |

### 📱 Persistence & Automation
| Module | Description |
|---|---|
| **Android Persistence** | .bashrc injection, Termux:Boot service, alarm scheduling |
| **Plugin Loader** | Hot-reload plugins/ directory — drop `.py` files, they auto-load |
| **Auto-Updater** | GitHub release checker with one-click update |

---

## 🖥️ C2 Server Dashboard

```bash
python phantom_whisper.py --server
```

Starts a full C2 server on `http://0.0.0.0:8080` with:

| Endpoint | Description |
|---|---|
| `/api/v1/dashboard` | Live HTML dashboard with Chart.js graphs |
| `/api/v1/agents` | JSON list of connected agents |
| `/api/v1/status` | Server status stats |
| `/api/v1/beacon` | Agent beacon endpoint |
| `/api/v1/command/<id>` | Queue commands for agents |
| `/api/v1/exfil` | Receive exfiltrated data |
| `ws://host:8081/ws` | WebSocket real-time feed |

Dashboard features: real-time agent feed, activity chart, live exfil stream, auto-refresh every 5 seconds.

---

## 🔧 Screenshots

*(Insert screenshots of the menu, C2 dashboard)*

---

## 🏗️ Architecture

```
phantom_whisper.py (77 KB)
├── Auto-Installer (detects OS, installs deps, creates config)
├── Crypto Layer (XChaCha20-Poly1305 + PBKDF2 x600k)
├── C2 Clients (DNS tunnel, HTTP mimic, WebSocket)
├── Recon Modules (ports, network, WiFi, BT, ARP, processes)
├── Attack Modules (phishing, clipboard, screenshots, stego)
├── C2 Server (HTTP + WebSocket + live dashboard)
├── Plugin System (hot-reloadable .py files)
└── Interactive UI (Rich-powered cyberpunk terminal)
```

---

## ⚠️ Disclaimer

**FOR EDUCATIONAL AND AUTHORIZED PENETRATION TESTING ONLY.**
Unauthorized access to computer systems is illegal. Always obtain proper written authorization before using this framework. The developers assume no liability for misuse or damage caused by this tool.

---

## 👾 Credits

- **Author:** masterfrequency / PhonkAlphabet 🇭🇷
- **Version:** 2.0.0 — Monolithic Ultimate Edition
