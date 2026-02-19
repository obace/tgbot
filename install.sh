#!/bin/bash
set -e

echo "=== Office 365 Activation Bot - One-Click Deploy ==="

# Install dependencies
if [ -f /etc/debian_version ]; then
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git curl
elif [ -f /etc/redhat-release ]; then
    yum install -y python3 python3-pip git curl
else
    echo "Unsupported system. Please install python3, pip and git manually."
    exit 1
fi

# Clone project
APP_DIR="/opt/tgbot"
rm -rf "$APP_DIR"
git clone https://github.com/obace/tgbot.git "$APP_DIR"
cd "$APP_DIR"

# Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Port config
PORT=${1:-5600}

# systemd service
tee /etc/systemd/system/tg-activation-bot.service > /dev/null <<EOF
[Unit]
Description=TG Activation Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn -w 1 --threads 4 --timeout 120 --preload -b 0.0.0.0:$PORT app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tg-activation-bot
systemctl restart tg-activation-bot

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=== Deploy Complete ==="
echo "URL: http://$IP:$PORT/login"
echo "Default password: admin"
echo "Please change your password after login!"
