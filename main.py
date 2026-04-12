#!/usr/bin/env python3
# =============================================
# CS 1.6 Server Status Bot + Web Sayt + TOP 10 Rasm
# pip install python-telegram-bot python-a2s flask Pillow requests beautifulsoup4
# =============================================

import asyncio
import threading
import io
import re
import logging
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

import a2s
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

STATS_URL   = "https://arenacs.uz/modules_extra/site_stats/ajax/actions.php"
SITE_URL    = "https://arenacs.uz/stats"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# SHRIFT YO'LLARI
# ──────────────────────────────────────────────
try:
    FONT_BOLD   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   24)
    FONT_BOLD_S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   13)
    FONT_NORMAL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        14)
    FONT_SMALL  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",        12)
    FONT_MONO   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",    14)
except Exception:
    FONT_BOLD   = ImageFont.load_default()
    FONT_BOLD_S = ImageFont.load_default()
    FONT_NORMAL = ImageFont.load_default()
    FONT_SMALL  = ImageFont.load_default()
    FONT_MONO   = ImageFont.load_default()

# ──────────────────────────────────────────────
# HTML TOZALASH
# ──────────────────────────────────────────────
def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

def clean(text: str) -> str:
    """HTML entity larni oddiy matnга aylantiradi."""
    return (
        str(text)
        .replace("&#39;", "'")
        .replace("&amp;", "&")
        .replace("&lt;",  "<")
        .replace("&gt;",  ">")
        .replace("&quot;","\"")
    )

# ──────────────────────────────────────────────
# FLASK
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
    *{margin:0;padding:0;box-sizing:border-box;}
    body{background:#0b0b10;font-family:'Inter',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden;}
    .bg{position:fixed;inset:0;z-index:0;}
    .bg span{position:absolute;border-radius:50%;filter:blur(80px);opacity:0.15;animation:float 8s ease-in-out infinite;}
    .bg span:nth-child(1){width:400px;height:400px;background:#ff6b35;top:-100px;left:-100px;}
    .bg span:nth-child(2){width:300px;height:300px;background:#3b82f6;bottom:-80px;right:-80px;animation-delay:3s;}
    .bg span:nth-child(3){width:200px;height:200px;background:#8b5cf6;top:50%;left:50%;animation-delay:5s;}
    @keyframes float{0%,100%{transform:translateY(0) scale(1);}50%{transform:translateY(-30px) scale(1.05);}}
    .card{position:relative;z-index:1;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);backdrop-filter:blur(20px);border-radius:24px;padding:56px 48px;max-width:520px;width:90%;text-align:center;box-shadow:0 32px 80px rgba(0,0,0,0.5);}
    .dot-wrap{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:32px;}
    .dot{width:14px;height:14px;border-radius:50%;background:#2ecc71;animation:ping 1.5s ease-out infinite;}
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
    .tg-btn{display:inline-flex;align-items:center;justify-content:center;gap:10px;background:linear-gradient(135deg,#2196F3,#1565C0);color:#fff;text-decoration:none;font-weight:700;padding:16px 36px;border-radius:50px;transition:transform 0.2s;box-shadow:0 8px 32px rgba(33,150,243,0.3);margin-bottom:20px;width:100%;}
    .tg-btn:hover{transform:translateY(-2px);}
    .tg-btn svg{width:22px;height:22px;fill:white;}
    .commands{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:20px;}
    .cmd{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:10px 12px;font-size:0.8em;color:#666;text-align:left;}
    .cmd code{color:#f7931e;}
    .footer{margin-top:32px;color:#333;font-size:0.75em;}
  </style>
</head>
<body>
  <div class="bg"><span></span><span></span><span></span></div>
  <div class="card">
    <div class="dot-wrap"><div class="dot"></div><span class="dot-label">Bot ishga tushdi!</span></div>
    <span class="logo">🎮</span>
    <h1>Server<span>Pulse</span></h1>
    <p class="subtitle">CS 1.6 server holatini real-time kuzatish uchun<br>Telegram bot</p>
    <div class="info-box">
      <div class="info-row"><span class="lbl">🌐 Server IP</span><span class="val orange">198.163.207.220:27015</span></div>
      <div class="info-row"><span class="lbl">🤖 Bot holati</span><span class="val green">✅ Ishlayapti</span></div>
      <div class="info-row"><span class="lbl">🎮 O'yin</span><span class="val">Counter-Strike 1.6</span></div>
    </div>
    <a href="https://t.me/cs_status_online_bot" class="tg-btn">
      <svg viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.248-1.97 9.289c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.833.932z"/></svg>
      Telegram Botga o'tish
    </a>
    <div class="commands">
      <div class="cmd"><code>Online</code><br>Server holati</div>
      <div class="cmd"><code>/status</code><br>Server holati</div>
      <div class="cmd"><code>/top</code><br>TOP 10 rasm</div>
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
# ARENACS.UZ — TOP 10 MA'LUMOTLARINI OLISH
# ──────────────────────────────────────────────
def fetch_top10():
    """
    arenacs.uz/stats sahifasidan translateHtml orqali TOP 10 ma'lumot oladi.
    """
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer":    SITE_URL,
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        # 1. Cookie olish uchun avval sahifani ochamiz
        session.get(SITE_URL, headers=headers, timeout=10)

        # 2. translateHtml so'rovi
        resp = session.post(
            "https://arenacs.uz/modules_extra/site_stats/ajax/actions.php",
            data={
                "phpaction": "1",
                "site_stats": "1",
                "token": "",
                "type": "1",
            },
            headers=headers,
            timeout=10
        )

        # 3. HTML ni parse qilib TOP jadvalini topamiz
        soup = BeautifulSoup(resp.text, "html.parser")

        # TOP jadval qatorlari
        rows = soup.select("tr.player_row, .top_row, tr[class*='top'], .stats_row")

        # Agar topilmasa — boshqa usul bilan
        if not rows:
            # Jadval qidirish
            tables = soup.find_all("table")
            for table in tables:
                trows = table.find_all("tr")
                if len(trows) >= 5:
                    rows = trows[1:]  # Header ni o'tkazib yuboramiz
                    break

        players = []
        for row in rows[:10]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                try:
                    rank   = len(players) + 1
                    name   = clean(cols[1].get_text(strip=True)) if len(cols) > 1 else "—"
                    kills  = int(re.sub(r'\D', '', cols[2].get_text(strip=True)) or 0)
                    deaths = int(re.sub(r'\D', '', cols[3].get_text(strip=True)) or 0) if len(cols) > 3 else 0
                    kdr    = round(kills / deaths, 2) if deaths > 0 else kills
                    players.append({"rank": rank, "name": name, "kills": kills, "deaths": deaths, "kdr": kdr})
                except Exception:
                    continue

        if players:
            return {"ok": True, "players": players}
        else:
            return {"ok": False, "error": "Ma'lumot topilmadi"}

    except Exception as e:
        return {"ok": False, "error": str(e)}

# ──────────────────────────────────────────────
# TOP 10 RASM YASASH
# ──────────────────────────────────────────────
def make_top10_image(players: list) -> bytes:
    W      = 780
    ROW_H  = 50
    HDR_H  = 88
    FTR_H  = 36
    H      = HDR_H + 28 + ROW_H * len(players) + FTR_H

    img  = Image.new("RGB", (W, H), (13, 13, 20))
    draw = ImageDraw.Draw(img)

    # ── Header ──
    draw.rectangle([0, 0, W, HDR_H], fill=(19, 19, 31))
    draw.text((W//2, 20), "TOP 10 OYINCHILAR", font=FONT_BOLD, fill=(247, 147, 30), anchor="mt")
    draw.text((W//2, 54), "arenacs.uz/stats  •  CS 1.6", font=FONT_SMALL, fill=(68, 68, 68), anchor="mt")
    draw.line([(0, HDR_H), (W, HDR_H)], fill=(34, 34, 34), width=2)

    # ── Column headers ──
    cy = HDR_H + 6
    draw.text((28,  cy), "#",      font=FONT_BOLD_S, fill=(85, 85, 85))
    draw.text((68,  cy), "NICK",   font=FONT_BOLD_S, fill=(85, 85, 85))
    draw.text((458, cy), "KILLS",  font=FONT_BOLD_S, fill=(85, 85, 85))
    draw.text((545, cy), "DEATHS", font=FONT_BOLD_S, fill=(85, 85, 85))
    draw.text((645, cy), "K/D",    font=FONT_BOLD_S, fill=(85, 85, 85))
    draw.line([(16, cy+20), (W-16, cy+20)], fill=(30, 30, 46), width=1)

    RANK_C = {1:(255,215,0), 2:(192,192,192), 3:(205,127,50)}
    max_kills = max((p["kills"] for p in players), default=1) or 1

    for i, p in enumerate(players):
        y  = HDR_H + 28 + i * ROW_H
        bg = (15, 15, 26) if i % 2 == 0 else (13, 13, 20)
        draw.rectangle([0, y, W, y+ROW_H-1], fill=bg)

        # Kill progress bar
        bw = int((p["kills"] / max_kills) * 155)
        draw.rectangle([458, y+ROW_H-6, 458+155, y+ROW_H-3], fill=(20, 20, 35))
        draw.rectangle([458, y+ROW_H-6, 458+bw,  y+ROW_H-3], fill=(180, 50, 40))

        # Rank badge
        rc = RANK_C.get(p["rank"], (60, 60, 80))
        draw.rectangle([18, y+10, 50, y+34], fill=(rc[0]//6, rc[1]//6, rc[2]//6))
        draw.text((34, y+22), str(p["rank"]), font=FONT_BOLD_S, fill=rc, anchor="mm")

        # Name
        nc   = rc if p["rank"] <= 3 else (200, 200, 200)
        name = p["name"][:26] + "…" if len(p["name"]) > 26 else p["name"]
        draw.text((68, y+22), name, font=FONT_NORMAL, fill=nc, anchor="lm")

        # Kills
        draw.text((458, y+22), f"{p['kills']:,}", font=FONT_MONO, fill=(231, 76, 60), anchor="lm")

        # Deaths
        draw.text((545, y+22), f"{p['deaths']:,}", font=FONT_MONO, fill=(52, 152, 219), anchor="lm")

        # KDR
        kc = (46,204,113) if p["kdr"] >= 2 else (243,156,18) if p["kdr"] >= 1.5 else (231,76,60)
        draw.text((645, y+22), f"{p['kdr']:.2f}", font=FONT_MONO, fill=kc, anchor="lm")

        draw.line([(16, y+ROW_H-1), (W-16, y+ROW_H-1)], fill=(25, 25, 40), width=1)

    # ── Footer ──
    fy = HDR_H + 28 + ROW_H * len(players) + 10
    draw.text((W//2, fy), "@cs_status_online_bot", font=FONT_SMALL, fill=(51, 51, 51), anchor="mt")

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf.read()

# ──────────────────────────────────────────────
# CS 1.6 SERVER SO'ROVI
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
# YORDAMCHI
# ──────────────────────────────────────────────
def format_time(seconds: float) -> str:
    s = int(seconds)
    m = s // 60
    h = m // 60
    if h > 0:  return f"{h}h {m%60}m"
    if m > 0:  return f"{m}m {s%60}s"
    return f"{s}s"

def medal(i: int) -> str:
    return {0:"🥇", 1:"🥈", 2:"🥉"}.get(i, f"{i+1}.")

def star_bar(v, mx, n=5):
    if mx == 0: return "☆"*n
    f = max(0, min(round(v/mx*n), n))
    return "★"*f + "☆"*(n-f)

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
    bar          = "█"*filled + "░"*(10-filled)
    real_players = [p for p in players if p.name and p.name.strip()]
    if not real_players:
        player_list = "  <i>Hozir hech kim yo'q</i>"
    else:
        lines = [
            f"  {i}. 🎮 <b>{esc(p.name.strip())}</b>  💀 {p.score or 0}  ⏱ {format_time(p.duration) if p.duration else '—'}"
            for i, p in enumerate(real_players, 1)
        ]
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

def status_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_status"),
        InlineKeyboardButton("🏆 TOP 10",    url="https://arenacs.uz/stats"),
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
        "🔹 /top — TOP 10 oyinchilar (rasm)\n"
        "🔹 /help — Yordam"
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "❓ <b>Yordam</b>\n\n"
        "<b>Online</b> yoki /status — server holati\n"
        "/top — arenacs.uz dan TOP 10 rasm ko'rinishida\n\n"
        "💀 — kill soni  💙 — o'lim  📊 — K/D nisbat"
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
    msg = await update.message.reply_html("⏳ <b>TOP 10 yuklanmoqda...</b>")
    loop = asyncio.get_event_loop()

    top_result = await loop.run_in_executor(None, fetch_top10)

    if top_result["ok"] and top_result["players"]:
        # Rasm yasaymiz
        img_bytes = await loop.run_in_executor(None, make_top10_image, top_result["players"])
        await msg.delete()
        await update.message.reply_photo(
            photo=io.BytesIO(img_bytes),
            caption=(
                "🏆 <b>TOP 10 Oyinchilar</b>\n"
                "📊 <i>arenacs.uz/stats dan olingan</i>\n\n"
                "💀 Kills  💙 Deaths  📈 K/D"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Yangilash",     callback_data="refresh_top"),
                InlineKeyboardButton("🌐 Saytda ko'rish", url="https://arenacs.uz/stats"),
            ]])
        )
    else:
        # Saytdan olmasa — link beramiz
        await msg.edit_text(
            "🏆 <b>TOP 10 Oyinchilar</b>\n\n"
            "⚠️ Hozir ma'lumot olib bo'lmadi.\n"
            "Quyidagi tugma orqali to'g'ridan ko'ring 👇",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🌐 arenacs.uz/stats", url="https://arenacs.uz/stats")
            ]])
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
        await query.answer("🔄 Yangilanmoqda...")
        result = await loop.run_in_executor(None, query_server)
        try:
            await query.edit_message_text(
                build_status_message(result),
                parse_mode="HTML",
                reply_markup=status_keyboard()
            )
        except Exception: pass

    elif data == "refresh_top":
        await query.answer("🔄 Yangilanmoqda...")
        top_result = await loop.run_in_executor(None, fetch_top10)
        if top_result["ok"] and top_result["players"]:
            img_bytes = await loop.run_in_executor(None, make_top10_image, top_result["players"])
            try:
                await query.edit_message_media(
                    media=__import__("telegram").InputMediaPhoto(
                        media=io.BytesIO(img_bytes),
                        caption=(
                            "🏆 <b>TOP 10 Oyinchilar</b>\n"
                            "📊 <i>arenacs.uz/stats dan olingan</i>\n\n"
                            "💀 Kills  💙 Deaths  📈 K/D"
                        ),
                        parse_mode="HTML"
                    ),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Yangilash",      callback_data="refresh_top"),
                        InlineKeyboardButton("🌐 Saytda ko'rish", url="https://arenacs.uz/stats"),
                    ]])
                )
            except Exception: pass

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
