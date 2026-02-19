import sqlite3, asyncio, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
_app = None
_loop = None

WELCOME = (
    "👋 Hi {name}! Welcome to the Office 365 Activation Service\n"
    "\n"
    "━━━━━━━━━━━━━━━━\n"
    "📌 How it works:\n"
    "1️⃣ Tap the button below to get your activation code\n"
    "2️⃣ Visit the registration site 👉 https://od.obagg.com/\n"
    "3️⃣ Use the code to register your account\n"
    "4️⃣ Sign in to activate Office 365 Desktop\n"
    "━━━━━━━━━━━━━━━━\n"
    "\n"
    "Tap /get to claim your code now 🎟️"
)

ALREADY_CLAIMED = (
    "📦 You've already claimed a code\n"
    "\n"
    "Your activation code: `{code}`\n"
    "\n"
    "━━━━━━━━━━━━━━━━\n"
    "📖 How to use:\n"
    "1. Go to https://od.obagg.com/\n"
    "2. Enter the code to complete registration\n"
    "3. Sign in to Office 365 Desktop with your new account\n"
    "\n"
    "⚠️ Important: This account is for activating Office 365 Desktop only. Do NOT use OneDrive to store important files!"
)

CODE_SENT = (
    "🎉 Activation code claimed!\n"
    "\n"
    "Your code: `{code}`\n"
    "\n"
    "━━━━━━━━━━━━━━━━\n"
    "📖 How to use:\n"
    "1. Go to https://od.obagg.com/\n"
    "2. Enter the code to register your account\n"
    "3. Sign in to Office 365 Desktop to activate\n"
    "\n"
    "⚠️ Important:\n"
    "• One code per user — keep it safe\n"
    "• This account is for Office 365 Desktop activation only\n"
    "• Do NOT use OneDrive to store important files!\n"
    "\n"
    "Need help? Contact the admin 💬"
)

NO_CODE = (
    "😔 Sorry, all activation codes have been claimed\n"
    "\n"
    "Please try again later or contact the admin for more codes."
)

HELP_TEXT = (
    "🤖 Office 365 Activation Code Bot\n"
    "\n"
    "Commands:\n"
    "/start - Welcome & instructions\n"
    "/get   - Claim your activation code\n"
    "/help  - Show this help\n"
    "\n"
    "Registration site: https://od.obagg.com/\n"
    "⚠️ This account is for Office 365 Desktop activation only. Do NOT use OneDrive to store important files!"
)

async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "朋友"
    keyboard = [
        [InlineKeyboardButton("🎟️ Get Activation Code", callback_data="get_code")],
        [InlineKeyboardButton("📖 Tutorial", callback_data="tutorial"),
         InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("🌐 Registration Site", url="https://od.obagg.com/")],
    ]
    await update.message.reply_text(WELCOME.format(name=name), reply_markup=InlineKeyboardMarkup(keyboard))

async def get_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    msg = update.message or update.callback_query.message
    db_path = ctx.bot_data["db"]
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT code FROM codes WHERE tg_user_id=?", (uid,)).fetchone()
    if row:
        keyboard = [[InlineKeyboardButton("🌐 Register Now", url="https://od.obagg.com/")],
                     [InlineKeyboardButton("🔙 Main Menu", callback_data="back")]]
        await msg.reply_text(ALREADY_CLAIMED.format(code=row[0]), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        conn.close()
        return
    code_row = conn.execute("SELECT id, code FROM codes WHERE tg_user_id IS NULL LIMIT 1").fetchone()
    if not code_row:
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="back")]]
        await msg.reply_text(NO_CODE, reply_markup=InlineKeyboardMarkup(keyboard))
        conn.close()
        return
    conn.execute("UPDATE codes SET tg_user_id=?, claimed_at=datetime('now','localtime') WHERE id=?", (uid, code_row[0]))
    user = update.effective_user
    conn.execute("INSERT INTO logs (tg_user_id, tg_username, tg_fullname, code) VALUES (?,?,?,?)",
                 (uid, user.username or '', user.full_name, code_row[1]))
    conn.commit()
    conn.close()
    logging.info(f"[领取] TG用户: {user.full_name} (ID: {uid}, @{user.username or '无'}) 领取激活码: {code_row[1]}")
    keyboard = [[InlineKeyboardButton("🌐 Register Now", url="https://od.obagg.com/")],
                 [InlineKeyboardButton("📖 Tutorial", callback_data="tutorial")],
                 [InlineKeyboardButton("🔙 Main Menu", callback_data="back")]]
    await msg.reply_text(CODE_SENT.format(code=code_row[1]), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    keyboard = [[InlineKeyboardButton("🎟️ Get Activation Code", callback_data="get_code")],
                 [InlineKeyboardButton("🔙 Main Menu", callback_data="back")]]
    await msg.reply_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup(keyboard))

TUTORIAL = (
    "📖 Step-by-Step Guide\n"
    "\n"
    "━━━━━━━━━━━━━━━━\n"
    "Step 1: Get your code\n"
    "Tap \"🎟️ Get Activation Code\" to claim your code\n"
    "\n"
    "Step 2: Register your account\n"
    "Go to https://od.obagg.com/ and enter the code to register\n"
    "\n"
    "Step 3: Activate Office\n"
    "Open Word, Excel or any Office app on your computer and sign in with your new account to activate\n"
    "━━━━━━━━━━━━━━━━\n"
    "\n"
    "⚠️ Please note:\n"
    "• This account is for Office 365 Desktop activation only\n"
    "• Do NOT use OneDrive to store important files!\n"
    "• One code per user"
)

async def button_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "get_code":
        await get_cmd(update, ctx)
    elif data == "help":
        await help_cmd(update, ctx)
    elif data == "tutorial":
        keyboard = [[InlineKeyboardButton("🎟️ Get Activation Code", callback_data="get_code")],
                     [InlineKeyboardButton("🌐 Registration Site", url="https://od.obagg.com/")],
                     [InlineKeyboardButton("🔙 Main Menu", callback_data="back")]]
        await query.message.reply_text(TUTORIAL, reply_markup=InlineKeyboardMarkup(keyboard))
    elif data == "back":
        name = update.effective_user.first_name or "朋友"
        keyboard = [
            [InlineKeyboardButton("🎟️ Get Activation Code", callback_data="get_code")],
            [InlineKeyboardButton("📖 Tutorial", callback_data="tutorial"),
             InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("🌐 Registration Site", url="https://od.obagg.com/")],
        ]
        await query.message.reply_text(WELCOME.format(name=name), reply_markup=InlineKeyboardMarkup(keyboard))

async def _run_bot(token, db_path):
    global _app
    _app = ApplicationBuilder().token(token).build()
    _app.bot_data["db"] = db_path
    _app.add_handler(CommandHandler("start", start_cmd))
    _app.add_handler(CommandHandler("get", get_cmd))
    _app.add_handler(CommandHandler("help", help_cmd))
    _app.add_handler(CallbackQueryHandler(button_callback))
    logging.info("Bot starting...")
    async with _app:
        await _app.updater.start_polling(drop_pending_updates=True)
        await _app.start()
        while _app.running:
            await asyncio.sleep(1)

def start_bot(token, db_path):
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    try:
        _loop.run_until_complete(_run_bot(token, db_path))
    except Exception as e:
        logging.error(f"Bot error: {e}")
    finally:
        _loop.close()

def stop_bot():
    global _app, _loop
    if _app and _loop:
        async def _stop():
            try:
                await _app.updater.stop()
                await _app.stop()
                await _app.shutdown()
            except Exception:
                pass
        try:
            asyncio.run_coroutine_threadsafe(_stop(), _loop).result(timeout=5)
        except Exception:
            pass
    _app = None
    _loop = None
