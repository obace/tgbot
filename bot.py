import sqlite3, asyncio, logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
_app = None

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db_path = ctx.bot_data["db"]
    conn = sqlite3.connect(db_path)
    # Check if user already claimed
    row = conn.execute("SELECT code FROM codes WHERE tg_user_id=?", (uid,)).fetchone()
    if row:
        await update.message.reply_text(f"你已经领取过激活码了：\n`{row[0]}`", parse_mode="Markdown")
        conn.close()
        return
    # Claim next available code
    code_row = conn.execute("SELECT id, code FROM codes WHERE tg_user_id IS NULL LIMIT 1").fetchone()
    if not code_row:
        await update.message.reply_text("抱歉，激活码已发完。")
        conn.close()
        return
    conn.execute("UPDATE codes SET tg_user_id=?, claimed_at=datetime('now') WHERE id=?", (uid, code_row[0]))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🎉 你的激活码：\n`{code_row[1]}`\n\n每人限领一个，请妥善保管。", parse_mode="Markdown")

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("发送 /start 获取激活码\n每位用户限领一个。")

def start_bot(token, db_path):
    global _app
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _app = ApplicationBuilder().token(token).build()
    _app.bot_data["db"] = db_path
    _app.add_handler(CommandHandler("start", start_cmd))
    _app.add_handler(CommandHandler("help", help_cmd))
    logging.info("Bot starting...")
    _app.run_polling(drop_pending_updates=True)

def stop_bot():
    global _app
    if _app:
        try:
            _app.stop_running()
        except Exception:
            pass
        _app = None
