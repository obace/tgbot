# Office 365 Activation Code Bot

Telegram bot for distributing Office 365 activation codes with a web admin panel.

## Features

- 🤖 Telegram bot with inline buttons
- 🔐 Password-protected admin dashboard
- 📋 Bulk import activation codes
- 👤 One code per Telegram user
- 📝 Claim logs with user details
- 📊 Real-time statistics

## One-Click Install

```bash
git clone https://github.com/obace/tgbot.git && cd tgbot && chmod +x deploy.sh && sudo ./deploy.sh
```

Custom port (default 5600):

```bash
sudo ./deploy.sh 8080
```

## Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) and get the Token
2. Visit `http://YOUR_IP:5600/login`, default password: `admin`
3. Change your password after login
4. Enter Bot Token and save
5. Paste activation codes in bulk
6. Users send `/start` to the bot to claim codes

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with inline buttons |
| `/get` | Claim an activation code |
| `/help` | Show help info |

## Service Management

```bash
sudo systemctl status tg-activation-bot    # Status
sudo systemctl restart tg-activation-bot   # Restart
sudo systemctl stop tg-activation-bot      # Stop
sudo journalctl -u tg-activation-bot -f    # Logs
```
