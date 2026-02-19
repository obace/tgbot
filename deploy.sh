#!/bin/bash
set -e

echo "=== Office 365 Activation Bot - One-Click Deploy ==="

# Detect system
if [ -f /etc/debian_version ]; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git
elif [ -f /etc/redhat-release ]; then
    sudo yum install -y python3 python3-pip git
else
    echo "Unsupported system. Please install python3 and pip manually."
    exit 1
fi

# Project directory
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Port config
PORT=${1:-5600}

# systemd service
SERVICE_FILE="/etc/systemd/system/tg-activation-bot.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=TG Activation Bot
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn -w 1 --threads 4 --timeout 120 --preload -b 0.0.0.0:$PORT app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable tg-activation-bot
sudo systemctl restart tg-activation-bot

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=== Deploy Complete ==="
echo "URL: http://$IP:$PORT/login"
echo "Default password: admin"
echo "Please change your password after login!"
