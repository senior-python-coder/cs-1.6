#!/usr/bin/env python3
# =============================================
# CS 1.6 Server Status Bot + Web Sayt
# pip install python-telegram-bot python-a2s flask
# =============================================

import asyncio
import threading
import a2s
import logging
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ──────────────────────────────────────────────
# SOZLAMALAR
# ──────────────────────────────────────────────
TOKEN   = "8754991264:AAEfB2HfIAwxmbc1pP3RTMUMcUOR18UQOO0"
CS_HOST = "198.163.207.220"
CS_PORT = 27015

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# HTML BELGILARINI TOZALASH (< > & → xavfsiz)
# ──────────────────────────────────────────────
def esc(text: str) -> str:
    """Oyinchi nomidagi < > & belgilarini Telegram HTML uchun xavfsiz qiladi."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

# ──────────────────────────────────────────────
# FLASK — WEB SAHIFA
# ──────────────────────────────────────────────
flask_app = Flask(__name__)

HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ServerPulse Bot</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      background: #0b0b10;
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .bg { position:fixed; inset:0; z-index:0; }
    .bg span {
      position:absolute; border-radius:50%;
      filter:blur(80px); opacity:0.15;
      animation:float 8s ease-in-out infinite;
    }
    .bg span:nth-child(1){width:400px;height:400px;background:#ff6b35;top:-100px;left:-100px;animation-delay:0s;}
    .bg span:nth-child(2){width:300px;height:300px;background:#3b82f6;bottom:-80px;right:-80px;animation-delay:3s;}
    .bg span:nth-child(3){width:200px;height:200px;background:#8b5cf6;top:50%;left:50%;animation-delay:5s;}
    @keyframes float {
      0%,100%{transform:translateY(0) scale(1);}
      50%{transform:translateY(-30px) scale(1.05);}
    }
    .card {
      position:relative; z-index:1;
      background:rgba(255,255,255,0.04);
      border:1px solid rgba(255,255,255,0.08);
      backdrop-filter:blur(20px);
      border-radius:24px;
      padding:56px 48px;
      max-width:520px; width:90%;
      text-align:center;
      box-shadow:0 32px 80px rgba(0,0,0,0.5);
    }
    .dot-wrap{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:32px;}
    .dot{width:14px;height:14px;border-radius:50%;background:#2ecc71;box-shadow:0 0 0 0 rgba(46,204,113,0.6);animation:ping 1.5s ease-out infinite;}
    @keyframes ping{0%{box-shadow:0 0 0 0 rgba(46,204,113,0.6);}70%{box-shadow:0 0 0 12px rgba(46,204,113,0);}100%{box-shadow:0 0 0 0 rgba(46,204,113,0);}}
    .dot-label{font-size:0.8em;color:#2ecc71;letter-spacing:2px;text-transform:uppercase;font-weight:700;}
    .logo{font-size:4em;margin-bottom:16px;display:block;}
    h1{font-size:2.4em;font-weight:900;color:#fff;letter-spacing:-1px;margin-bottom:8px;}
    h1 span{background:linear-gradient(135deg,#ff6b35,#f7931e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}
    .subtitle{color:#555;font-size:0.95em;margin-bottom:40px;line-height:1.6;}
    .info-box{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:20px 24px;margin-bottom:28px;text-align:left;}
    .info-row{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.88em;}
    .info-row:last-child{border-bottom:none;}
    .info-row .lbl{color:#555;}
    .info-row .val{color:#ccc;font-family:monospace;}
    .info-row .val.green{color:#2ecc71;}
    .info-row .val.orange{color:#f7931e;}
    .tg-btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;background:linear-gradient(135deg,#2196F3,#1565C0);color:#fff;text-decoration:none;font-weight:700;font-size:1em;padding:16px 36px;border-radius:50px;letter-spacing:0.5px;transition:transform 0.2s,box-shadow 0.2s;box-shadow:0 8px 32px rgba(33,150,243,0.3);margin-bottom:20px;width:100%;}
    .tg-btn:hover{transform:translateY(-2px);box-shadow:0 12px 40px rgba(33,150,243,0.4);}
    .tg-btn svg{width:22px;height:22px;fill:white;}
    .commands{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:20px;}
    .cmd{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:10px 12px;font-size:0.8em;color:#666;text-align:left;}
    .cmd code{color:#f7931e;font-size:0.95em;}
    .footer{margin-top:32px;color:#333;font-size:0.75em;}
  </style>
</head>
<body>
  <div class="bg"><span></span><span></span><span></span></div>
  <div class="card">
    <div class="dot-wrap">
      <div class="dot"></div>
      <span class="dot-label">Bot ishga tushdi!</span>
    </div>
    <span class="logo">🎮</span>
    <h1>Server<span>Pulse</span></h1>
    <p class="subtitle">CS 1.6 server holatini real-time kuzatish uchun<br>Telegram bot</p>
    <div class="info-box">
      <div class="info-row">
        <span class="lbl">🌐 Server IP</span>
        <span class="val orange">198.163.207.220:27015</span>
      </div>
      <div class="info-row">
        <span class="lbl">🤖 Bot holati</span>
        <span class="val green">✅ Ishlayapti</span>
      </div>
      <div class="info-row">
        <span class="lbl">🎮 O'yin</span>
        <span class="val">Counter-Strike 1.6</span>
      </div>
    </div>
    <a href="https://t.me/cs_status_online_bot" class="tg-btn">
      <svg viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.248-1.97 9.289c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.833.932z"/></svg>
      Telegram Botga o'tish
    </a>
    <div class="commands">
      <div class="cmd"><code>Online</code><br>Server holati</div>
      <div class="cmd"><code>/status</code><br>Server holati</div>
      <div class="cmd"><code>/top</code><br>TOP o'yinchilar</div>
      <div class="cmd"><code>/help</code><br>Yordam</div>
    </div>
    <div class="footer">ServerPulse © 2026 — CS 1.6 Community</div>
  </div>
</body>
</html>"""

@flask_app.route("/")
def index():
    return HTML

@flask_app.route("/health")
def health():
    return {"status": "ok"}, 200

# ──────────────────────────────────────────────
# SERVER SO'ROVI
# ──────────────────────────────────────────────
def query_server():
    addr = (CS_HOST, CS_PORT)
    try:
        info    = a2s.info(addr, timeout=5)
        players = a2s.players(addr, timeout=5)
        return {"online": True, "info": info, "players": players}
    except Exception as e:
        return {"online": False, "error": str(e)}

# ──────────────────────────────────────────────
# YORDAMCHI FUNKSIYALAR
# ──────────────────────────────────────────────
def format_time(seconds: float) -> str:
    s = int(seconds)
    m = s // 60
    h = m // 60
    if h > 0:  return f"{h}h {m % 60}m"
    if m > 0:  return f"{m}m {s % 60}s"
    return f"{s}s"

def medal(index: int) -> str:
    return {0:"🥇", 1:"🥈", 2:"🥉"}.get(index, f"{index+1}.")

def star_bar(value: float, max_value: float, length: int = 5) -> str:
    if max_value == 0: return "☆" * length
    filled = max(0, min(round((value / max_value) * length), length))
    return "★" * filled + "☆" * (length - filled)

# ──────────────────────────────────────────────
# XABARLAR
# ──────────────────────────────────────────────
def build_status_message(result: dict) -> str:
    if not result["online"]:
        return (
            "🔴 <b>SERVER OFFLINE</b>\n\n"
            f"🌐 <b>IP:</b> <code>{CS_HOST}:{CS_PORT}</code>\n"
            "❌ Server hozir javob bermayapti."
        )

    info         = result["info"]
    players      = result["players"]
    server_name  = esc(info.server_name  or "CS 1.6 Server")
    map_name     = esc(info.map_name     or "Noma'lum")
    player_count = info.player_count or 0
    max_players  = info.max_players  or 32
    ping         = round(info.ping * 1000) if info.ping else 0
    filled       = round(player_count / max_players * 10) if max_players else 0
    bar          = "█" * filled + "░" * (10 - filled)

    real_players = [p for p in players if p.name and p.name.strip()]
    if not real_players:
        player_list = "  <i>Hozir hech kim yo'q</i>"
    else:
        lines = []
        for i, p in enumerate(real_players, 1):
            name  = esc(p.name.strip())   # ← < > & tozalanadi
            score = p.score or 0
            time  = format_time(p.duration) if p.duration else "—"
            lines.append(f"  {i}. 🎮 <b>{name}</b>  💀 {score}  ⏱ {time}")
        player_list = "\n".join(lines)

    return (
        "🟢 <b>SERVER ONLINE</b>\n\n"
        f"🖥 <b>{server_name}</b>\n"
        f"🌐 <b>IP:</b> <code>{CS_HOST}:{CS_PORT}</code>\n"
        f"🗺 <b>Xarita:</b> <code>{map_name}</code>\n"
        f"📶 <b>Ping:</b> {ping} ms\n\n"
        f"👥 <b>Oyinchilar:</b> {player_count} / {max_players}\n"
        f"[{bar}]\n\n"
        f"📋 <b>Oyinchilar:</b>\n{player_list}"
    )

def build_top_message(result: dict, mode: str = "kills") -> str:
    if not result["online"]:
        return "🔴 <b>Server offline</b> — TOP ko'rish mumkin emas."

    players      = result["players"]
    real_players = [p for p in players if p.name and p.name.strip()]

    if not real_players:
        return (
            "📊 <b>TOP LIST</b>\n\n"
            f"😴 <i>Hozir serverda hech kim yo'q</i>\n\n"
            f"🌐 <code>{CS_HOST}:{CS_PORT}</code>"
        )

    total = len(real_players)

    if mode == "kills":
        srt   = sorted(real_players, key=lambda p: p.score or 0, reverse=True)
        mx    = srt[0].score or 1
        title = "💀 <b>TOP — ENG KO'P KILL</b>"
        lines = [
            f"{medal(i)} <b>{esc(p.name.strip())}</b>\n"
            f"    {star_bar(p.score or 0, mx)}  💀 <b>{p.score or 0}</b> kill  ⏱ {format_time(p.duration) if p.duration else '—'}"
            for i, p in enumerate(srt)
        ]
    else:
        srt   = sorted(real_players, key=lambda p: p.duration or 0, reverse=True)
        mx    = srt[0].duration or 1
        title = "⏱ <b>TOP — ENG KO'P O'YNAGAN</b>"
        lines = [
            f"{medal(i)} <b>{esc(p.name.strip())}</b>\n"
            f"    {star_bar(p.duration or 0, mx)}  ⏱ <b>{format_time(p.duration) if p.duration else '—'}</b>  💀 {p.score or 0} kill"
            for i, p in enumerate(srt)
        ]

    return (
        f"{title}\n"
        f"🌐 <code>{CS_HOST}:{CS_PORT}</code>  👥 {total} oyinchi\n"
        f"{'─' * 24}\n\n"
        + "\n\n".join(lines)
    )

# ──────────────────────────────────────────────
# KLAVIATURALAR
# ──────────────────────────────────────────────
def status_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_status"),
        InlineKeyboardButton("🏆 TOP 10",    url="https://arenacs.uz/stats"),
    ]])

def top_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🏆 TOP 10 ni ko'rish", url="https://arenacs.uz/stats"),
    ]])

# ──────────────────────────────────────────────
# TELEGRAM HANDLERLAR
# ──────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "🎮 <b>CS 1.6 Server Status Bot</b>\n\n"
        f"🌐 Server: <code>{CS_HOST}:{CS_PORT}</code>\n\n"
        "📌 <b>Buyruqlar:</b>\n"
        "🔹 <code>Online</code> — Server holati\n"
        "🔹 /status — Server holati\n"
        "🔹 /top — TOP o'yinchilar\n"
        "🔹 /help — Yordam"
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "❓ <b>Yordam</b>\n\n"
        "<b>Online</b> yoki /status — server holati\n"
        "/top — kill va vaqt bo'yicha TOP\n\n"
        "📊 <b>TOP listda:</b>\n"
        "★★★★★ — yulduzlar (1-o'ringa nisbatan)\n"
        "💀 — kill soni\n"
        "⏱ — o'ynalgan vaqt"
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_html(
        f"⏳ <b>So'ralmoqda...</b> <code>{CS_HOST}:{CS_PORT}</code>"
    )
    result = await asyncio.get_event_loop().run_in_executor(None, query_server)
    await msg.edit_text(
        build_status_message(result),
        parse_mode="HTML",
        reply_markup=status_keyboard()
    )

async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "🏆 <b>TOP 10 — <a href='https://arenacs.uz/stats'>arenacs.uz/stats</a></b>\n\n"
        "👆 Yuqoridagi linkni yoki quyidagi tugmani bosing:",
        reply_markup=top_keyboard()
    )

async def on_online_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_html(
        "⏳ <b>So'ralmoqda...</b>",
        reply_to_message_id=update.message.message_id
    )
    result = await asyncio.get_event_loop().run_in_executor(None, query_server)
    await msg.edit_text(
        build_status_message(result),
        parse_mode="HTML",
        reply_markup=status_keyboard()
    )

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query  = update.callback_query
    data   = query.data
    loop   = asyncio.get_event_loop()

    if data in ("refresh_status", "back_to_status"):
        await query.answer("🔄 Yangilanmoqda..." if data == "refresh_status" else "")
        result = await loop.run_in_executor(None, query_server)
        try:
            await query.edit_message_text(
                build_status_message(result),
                parse_mode="HTML",
                reply_markup=status_keyboard()
            )
        except Exception: pass

    elif data in ("show_top_kills", "refresh_top_kills"):
        pass

    elif data in ("show_top_time", "refresh_top_time"):
        pass

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def run_flask():
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

def main():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    print("🌐 Web sayt: http://0.0.0.0:8080")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("top",    cmd_top))
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^online$"), on_online_message))
    app.add_handler(CallbackQueryHandler(on_callback))

    print("🎮 CS 1.6 Status Bot ishga tushdi!")
    print(f"📡 Server: {CS_HOST}:{CS_PORT}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
