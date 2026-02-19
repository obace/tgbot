#!/bin/bash
set -e

echo "=== TG 激活码机器人 一键部署 ==="

# 检测系统
if [ -f /etc/debian_version ]; then
    PKG="apt-get"
    sudo $PKG update -y
    sudo $PKG install -y python3 python3-pip python3-venv git
elif [ -f /etc/redhat-release ]; then
    PKG="yum"
    sudo $PKG install -y python3 python3-pip git
else
    echo "不支持的系统，请手动安装 python3 和 pip"
    exit 1
fi

# 项目目录
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# 虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# systemd 服务
SERVICE_FILE="/etc/systemd/system/tg-activation-bot.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=TG Activation Bot
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn -w 1 --threads 4 -b 0.0.0.0:5099 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable tg-activation-bot
sudo systemctl restart tg-activation-bot

echo ""
echo "=== 部署完成 ==="
echo "访问地址: http://$(hostname -I | awk '{print $1}'):5099/login"
echo "默认密码: admin"
echo "请登录后立即修改密码！"
