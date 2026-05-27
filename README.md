# 🎭 Phantom-Whisper

![Phantom Whisper Banner](phantom_whisper_banner.png)

> **"Invisibility is the ultimate weapon."**

**Phantom-Whisper** is the ultimate Android Red Team Framework for 2026, designed for authorized penetration testing and educational purposes. It integrates AI-powered social engineering with a multi-vector Command & Control (C2) infrastructure to simulate advanced persistent threats (APTs) in mobile environments.

## 🚀 Quick Install (Termux)

Run this one-liner to install, configure autostart, and start the framework in Termux:

```bash
pkg update && pkg upgrade -y && pkg install git python -y && git clone https://github.com/masterfrequency/Phantom-Whisper.git && cd Phantom-Whisper && pip install rich requests cryptography dnspython && python phantom_whisper.py --setup && python phantom_whisper.py
```

> **Note:** The `--setup` flag automatically configures the framework to start whenever you open Termux.


## 🚀 Key Features

### 🎭 AI-Powered Social Engineering
- **Personality Matching:** LLM-generated phishing content tailored to target profiles.
- **Voice Clone SMS:** Integration for sophisticated pretexting.
- **Context-Awareness:** Automated OSINT-based social engineering scenarios.

### 🌐 Covert C2 Channels
- **DNS Tunneling:** Communication over legitimate DNS resolvers.
- **Social Steganography:** Data hiding within social media image uploads.
- **Protocol Mimicry:** HTTP traffic disguised as legitimate CDN requests.
- **QUIC Encryption:** Secure channels with certificate pinning bypass.

### 📱 Android Persistence (No Root)
- **Accessibility Abuse:** Silent operation via accessibility services.
- **Hybrid Persistence:** Combination of Job Schedulers and Foreground Services.
- **PWA Hijacking:** Stealthy installation through Chrome for legitimacy.

### 🔓 Credential Harvesting
- **Clipboard Monitoring:** Smart filtering for sensitive data.
- **Screenshot OCR:** Extraction of 2FA codes from screen captures.
- **WebView Injection:** OAuth token theft via injected interfaces.

### 🕵️ Advanced Reconnaissance
- **Device Mapping:** Permissionless Bluetooth and WiFi mapping.
- **Contact Graphing:** Relationship scoring and social network analysis.
- **Usage Profiling:** App pattern analysis for optimized engagement.

## 🛠️ Technical Overview

The framework is built on a modular Python architecture, utilizing asynchronous operations for high performance and low footprint.

| Component | Description |
|-----------|-------------|
| **Core** | Asyncio-based event loop for concurrent task management. |
| **Encryption** | Military-grade PBKDF2 + Fernet (AES-128-CBC) encryption. |
| **UI** | Cyberpunk-themed terminal interface using the `rich` library. |
| **Transport** | Pluggable transport layers (DNS, HTTP, QUIC). |

## ⚠️ Disclaimer

**FOR EDUCATIONAL AND AUTHORIZED PENETRATION TESTING ONLY.**
Unauthorized access to computer systems is illegal. Always obtain proper written authorization before using this framework. The developers assume no liability for misuse or damage caused by this tool.
