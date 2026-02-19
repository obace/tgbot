import os, sqlite3, threading
from flask import Flask, request, redirect, url_for, render_template, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from bot import start_bot, stop_bot

app = Flask(__name__)
app.secret_key = os.urandom(24)
DB = "data.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY, value TEXT
            );
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                tg_user_id TEXT DEFAULT NULL,
                claimed_at TIMESTAMP DEFAULT NULL
            );
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY, password_hash TEXT NOT NULL
            );
        """)
        if not db.execute("SELECT 1 FROM admin LIMIT 1").fetchone():
            db.execute("INSERT INTO admin VALUES (1, ?)", (generate_password_hash("admin"),))

init_db()

def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        row = get_db().execute("SELECT password_hash FROM admin WHERE id=1").fetchone()
        if row and check_password_hash(row["password_hash"], pw):
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        flash("密码错误")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    db = get_db()
    token = db.execute("SELECT value FROM config WHERE key='bot_token'").fetchone()
    total = db.execute("SELECT COUNT(*) c FROM codes").fetchone()["c"]
    claimed = db.execute("SELECT COUNT(*) c FROM codes WHERE tg_user_id IS NOT NULL").fetchone()["c"]
    codes = db.execute("SELECT * FROM codes ORDER BY id DESC LIMIT 100").fetchall()
    return render_template("dashboard.html", token=token["value"] if token else "",
                           total=total, claimed=claimed, codes=codes)

@app.route("/save_token", methods=["POST"])
@login_required
def save_token():
    token = request.form.get("token", "").strip()
    if not token:
        flash("Token不能为空")
        return redirect(url_for("dashboard"))
    with get_db() as db:
        db.execute("INSERT OR REPLACE INTO config VALUES ('bot_token', ?)", (token,))
    stop_bot()
    threading.Thread(target=start_bot, args=(token, DB), daemon=True).start()
    flash("Token已保存，机器人已启动")
    return redirect(url_for("dashboard"))

@app.route("/add_codes", methods=["POST"])
@login_required
def add_codes():
    raw = request.form.get("codes", "")
    codes = [c.strip() for c in raw.replace(",", "\n").split("\n") if c.strip()]
    added = 0
    with get_db() as db:
        for c in codes:
            try:
                db.execute("INSERT INTO codes (code) VALUES (?)", (c,))
                added += 1
            except sqlite3.IntegrityError:
                pass
    flash(f"成功添加 {added} 个激活码，跳过 {len(codes)-added} 个重复")
    return redirect(url_for("dashboard"))

@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    pw = request.form.get("new_password", "").strip()
    if len(pw) < 4:
        flash("密码至少4位")
        return redirect(url_for("dashboard"))
    with get_db() as db:
        db.execute("UPDATE admin SET password_hash=? WHERE id=1", (generate_password_hash(pw),))
    flash("密码已修改")
    return redirect(url_for("dashboard"))

@app.route("/delete_unclaimed", methods=["POST"])
@login_required
def delete_unclaimed():
    with get_db() as db:
        r = db.execute("DELETE FROM codes WHERE tg_user_id IS NULL")
        flash(f"已删除 {r.rowcount} 个未领取的激活码")
    return redirect(url_for("dashboard"))

def auto_start_bot():
    row = get_db().execute("SELECT value FROM config WHERE key='bot_token'").fetchone()
    if row and row["value"]:
        threading.Thread(target=start_bot, args=(row["value"], DB), daemon=True).start()

auto_start_bot()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5099)
