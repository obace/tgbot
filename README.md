# TG 激活码分发机器人

通过 Telegram 机器人自动分发激活码，每个用户限领一个。

## 功能

- 🔐 密码保护的管理后台
- 🤖 配置 Telegram Bot Token
- 📋 批量导入激活码
- 👤 每个 TG 用户限领一个激活码
- 📊 激活码状态查看

## 一键部署

```bash
git clone https://github.com/你的用户名/tg-activation-bot.git
cd tg-activation-bot
chmod +x deploy.sh
sudo ./deploy.sh
```

## 使用步骤

1. 在 [@BotFather](https://t.me/BotFather) 创建机器人，获取 Token
2. 访问 `http://你的IP:5000/login`，默认密码 `admin`
3. 登录后修改密码
4. 填入 Bot Token 并保存
5. 批量粘贴激活码
6. 用户向机器人发送 `/start` 即可领取

## 用户交互

- `/start` - 领取激活码
- `/help` - 查看帮助
