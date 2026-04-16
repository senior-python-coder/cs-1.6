#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import io
import logging
import os
import re
import threading
from collections import defaultdict
from html import escape

import a2s
import requests
from bs4 import BeautifulSoup
from flask import Flask
from PIL import Image, ImageDraw, ImageFont
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    MessageEntity,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
TOKEN = "8754991264:AAEMfS7pLSBieHnuunCCz5Jl4I9SZylqCic"  # siz aytgan token
CS_HOST = "198.163.207.220"
CS_PORT = 27015
SITE_URL = "https://arenacs.uz/stats"
SERVER_NAME = "ARENACS.UZ | PUBLIC 18+"

# 1..10 rank custom emoji id
CUSTOM_EMOJI_IDS = {
    1: "5280618627794502101",
    2: "5350673031905692048",
    3: "5341460631998471430",
    4: "5341491624482477633",
    5: "5341548090417519735",
    6: "5343880511062315407",
    7: "5341511205238381063",
    8: "5341750026894877670",
    9: "5281024828621488140",
    10: "5280704793428397747",
}

# custom emoji chiqmasa avtomatik oddiy raqamga tushadi
USE_CUSTOM_EMOJI = True

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("cs_status_bot")

# =========================
# FLASK APP
# =========================
web_app = Flask(__name__)

@web_app.get("/")
def home():
    return "CS Status Bot is running", 200

@web_app.get("/health")
def health():
    return {"ok": True}, 200

def run_flask():
    port = int(os.getenv("PORT", "8080"))
    web_app.run(host="0.0.0.0", port=port)

# =========================
# MESSAGE CLEANUP
# =========================
user_messages = defaultdict(list)  # {user_id: [(chat_id, msg_id)]}

async def delete_old_messages(bot, user_id: int):
    for chat_id, msg_id in user_messages[user_id]:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass
    user_messages[user_id] = []

def save_message(user_id: int, chat_id: int, msg_id: int):
    user_messages[user_id].append((chat_id, msg_id))

# =========================
# IMAGE FONTS
# =========================
try:
    FONT_BOLD = ImageFont.truetype("arialbd.ttf", 24)
    FONT_BOLD_S = ImageFont.truetype("arialbd.ttf", 13)
    FONT_NORMAL = ImageFont.truetype("arial.ttf", 14)
    FONT_SMALL = ImageFont.truetype("arial.ttf", 12)
    FONT_MONO = ImageFont.truetype("cour.ttf", 14)
except Exception:
    FONT_BOLD = FONT_BOLD_S = FONT_NORMAL = FONT_SMALL = FONT_MONO = ImageFont.load_default()

# =========================
# HELPERS
# =========================
def clean(text: str) -> str:
    return (
        str(text or "")
        .replace("&#39;", "'")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
    )

def fmt_time(seconds: float) -> str:
    s = int(seconds or 0)
    m = s // 60
    h = m // 60
    if h > 0:
        return f"{h}:{m % 60:02d}:{s % 60:02d}"
    return f"{m}:{s % 60:02d}"

def query_server():
    try:
        info = a2s.info((CS_HOST, CS_PORT), timeout=5)
        players = a2s.players((CS_HOST, CS_PORT), timeout=5)
        return {"online": True, "info": info, "players": players}
    except Exception as e:
        return {"online": False, "error": str(e)}

def status_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_status"),
        InlineKeyboardButton("🏆 TOP 10", url=SITE_URL),
    ]])

# =========================
# STATUS PAYLOAD
# =========================
def build_status_payload(result: dict):
    """
    Returns: (text, entities)
    entities -> custom emoji for rank 1..10 (optional)
    """
    lines = []
    entities = []

    if not result.get("online"):
        lines.append("ℹ️ Информация о сервере")
        lines.append(f"📝 {SERVER_NAME}")
        lines.append(f"🌐 {CS_HOST}:{CS_PORT}")
        lines.append("")
        lines.append("🔴 Сервер оффлайн")
        lines.append("❌ Сервер не отвечает.")
        return "\n".join(lines), entities

    info = result["info"]
    players = result["players"]

    map_name = clean(getattr(info, "map_name", "") or "Noma'lum")
    player_count = int(getattr(info, "player_count", 0) or 0)
    max_players = int(getattr(info, "max_players", 32) or 32)
    percent = round(player_count / max_players * 100) if max_players else 0

    # kill(score) bo'yicha saralash: ko'pdan kamga
    real_players = sorted(
        [p for p in players if getattr(p, "name", None) and str(p.name).strip()],
        key=lambda p: getattr(p, "score", 0) or 0,
        reverse=True
    )

    lines.append("ℹ️ Информация о сервере")
    lines.append(f"📝 {SERVER_NAME}")
    lines.append(f"🌐 {CS_HOST}:{CS_PORT}")
    lines.append(f"🗺 Карта: {map_name}")
    lines.append(f"👥 Онлайн: {player_count}/{max_players} ({percent}%)")
    lines.append("👤 Игроки онлайн:")

    if not real_players:
        lines.append("Нет игроков онлайн")
    else:
        for i, p in enumerate(real_players, 1):
            name = clean(str(p.name).strip())
            score = int(getattr(p, "score", 0) or 0)
            time_str = fmt_time(getattr(p, "duration", 0) or 0)

            # placeholder belgisi keyin custom emoji entity bilan almashtiriladi
            if USE_CUSTOM_EMOJI and i <= 10:
                lines.append(f"• {name} — {score} фрагов — {time_str}")
            else:
                lines.append(f"{i}) {name} — {score} фрагов — {time_str}")

    # 2 qator pastga
    lines.append("\u200b")
    lines.append("\u200b")
    lines.append(f"📋 Всего игроков онлайн: {player_count}")

    text = "\n".join(lines)

    # custom emoji entity offsetlarni hisoblash
    if USE_CUSTOM_EMOJI and real_players:
        offset = 0
        player_line_index = 0
        for line in lines:
            if line.startswith("• "):
                player_line_index += 1
                emoji_id = CUSTOM_EMOJI_IDS.get(player_line_index)
                if emoji_id:
                    entities.append(
                        MessageEntity(
                            type=MessageEntity.CUSTOM_EMOJI,
                            offset=offset,  # line boshidagi "•"
                            length=1,
                            custom_emoji_id=emoji_id
                        )
                    )
            offset += len(line) + 1  # + '\n'

    return text, entities

# =========================
# TOP 10
# =========================
def fetch_top10():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": SITE_URL,
        "X-Requested-With": "XMLHttpRequest",
    }
    try:
        session.get(SITE_URL, headers=headers, timeout=10)
        resp = session.post(
            "https://arenacs.uz/modules_extra/site_stats/ajax/actions.php",
            data={"phpaction": "1", "site_stats": "1", "token": "", "type": "1"},
            headers=headers,
            timeout=10
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("tr.player_row, .top_row, tr[class*='top'], .stats_row")

        if not rows:
            for table in soup.find_all("table"):
                trows = table.find_all("tr")
                if len(trows) >= 5:
                    rows = trows[1:]
                    break

        players = []
        for row in rows[:10]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                try:
                    name = clean(cols[1].get_text(strip=True)) if len(cols) > 1 else "—"
                    kills = int(re.sub(r"\D", "", cols[2].get_text(strip=True)) or 0)
                    deaths = int(re.sub(r"\D", "", cols[3].get_text(strip=True)) or 0) if len(cols) > 3 else 0
                    kdr = round(kills / deaths, 2) if deaths > 0 else float(kills)
                    players.append(
                        {"rank": len(players) + 1, "name": name, "kills": kills, "deaths": deaths, "kdr": kdr}
                    )
                except Exception:
                    continue

        return {"ok": bool(players), "players": players}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def make_top10_image(players: list) -> bytes:
    W, ROW_H, HDR_H, FTR_H = 780, 50, 88, 36
    H = HDR_H + 28 + ROW_H * len(players) + FTR_H

    img = Image.new("RGB", (W, H), (13, 13, 20))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, HDR_H], fill=(19, 19, 31))
    draw.text((W // 2, 20), "TOP 10 OYINCHILAR", font=FONT_BOLD, fill=(247, 147, 30), anchor="mt")
    draw.text((W // 2, 54), "arenacs.uz/stats  •  CS 1.6", font=FONT_SMALL, fill=(68, 68, 68), anchor="mt")
    draw.line([(0, HDR_H), (W, HDR_H)], fill=(34, 34, 34), width=2)

    cy = HDR_H + 6
    for x, lbl in [(28, "#"), (68, "NICK"), (458, "KILLS"), (545, "DEATHS"), (645, "K/D")]:
        draw.text((x, cy), lbl, font=FONT_BOLD_S, fill=(85, 85, 85))
    draw.line([(16, cy + 20), (W - 16, cy + 20)], fill=(30, 30, 46), width=1)

    rank_colors = {1: (255, 215, 0), 2: (192, 192, 192), 3: (205, 127, 50)}
    max_kills = max((p["kills"] for p in players), default=1) or 1

    for i, p in enumerate(players):
        y = HDR_H + 28 + i * ROW_H
        draw.rectangle([0, y, W, y + ROW_H - 1], fill=(15, 15, 26) if i % 2 == 0 else (13, 13, 20))

        bw = int((p["kills"] / max_kills) * 155)
        draw.rectangle([458, y + ROW_H - 6, 613, y + ROW_H - 3], fill=(20, 20, 35))
        draw.rectangle([458, y + ROW_H - 6, 458 + bw, y + ROW_H - 3], fill=(180, 50, 40))

        rc = rank_colors.get(p["rank"], (60, 60, 80))
        draw.rectangle([18, y + 10, 50, y + 34], fill=(rc[0] // 6, rc[1] // 6, rc[2] // 6))
        draw.text((34, y + 22), str(p["rank"]), font=FONT_BOLD_S, fill=rc, anchor="mm")

        nc = rc if p["rank"] <= 3 else (200, 200, 200)
        name = p["name"][:26] + "…" if len(p["name"]) > 26 else p["name"]

        draw.text((68, y + 22), name, font=FONT_NORMAL, fill=nc, anchor="lm")
        draw.text((458, y + 22), f"{p['kills']:,}", font=FONT_MONO, fill=(231, 76, 60), anchor="lm")
        draw.text((545, y + 22), f"{p['deaths']:,}", font=FONT_MONO, fill=(52, 152, 219), anchor="lm")

        kd_color = (46, 204, 113) if p["kdr"] >= 2 else (243, 156, 18) if p["kdr"] >= 1.5 else (231, 76, 60)
        draw.text((645, y + 22), f"{p['kdr']:.2f}", font=FONT_MONO, fill=kd_color, anchor="lm")
        draw.line([(16, y + ROW_H - 1), (W - 16, y + ROW_H - 1)], fill=(25, 25, 40), width=1)

    draw.text((W // 2, HDR_H + 28 + ROW_H * len(players) + 10), "@cs_status_online_bot", font=FONT_SMALL, fill=(51, 51, 51), anchor="mt")

    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf.read()

# =========================
# HANDLERS
# =========================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "CS 1.6 Server Status Bot\n\n"
        f"Server: {CS_HOST}:{CS_PORT}\n\n"
        "Buyruqlar:\n"
        "/status yoki /ststus\n"
        "Online / Онлайн / Online botlar\n"
        "/top\n"
        "/help"
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Yordam:\n"
        "- /status yoki /ststus\n"
        "- Online / Онлайн / Online botlar\n"
        "- /top"
    )

async def send_status(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_to_message_id=None):
    if not update.message:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    await delete_old_messages(context.bot, user_id)

    msg = await update.message.reply_text("⏳ So'ralmoqda...", reply_to_message_id=reply_to_message_id)

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, query_server)
        text, entities = build_status_payload(result)

        # custom emoji entities xato bersa fallback
        try:
            await msg.edit_text(text=text, entities=entities, reply_markup=status_keyboard())
        except Exception:
            plain_text = text.replace("• ", "")
            await msg.edit_text(text=plain_text, reply_markup=status_keyboard())

        save_message(user_id, chat_id, msg.message_id)

    except Exception as e:
        logger.exception("send_status error")
        await msg.edit_text(f"❌ Xatolik: {e}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_status(update, context)

async def on_online_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_status(update, context, reply_to_message_id=update.message.message_id if update.message else None)

async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ TOP 10 yuklanmoqda...")
    try:
        loop = asyncio.get_running_loop()
        top_result = await loop.run_in_executor(None, fetch_top10)

        if top_result["ok"] and top_result["players"]:
            img_bytes = await loop.run_in_executor(None, make_top10_image, top_result["players"])
            await msg.delete()
            await update.message.reply_photo(
                photo=io.BytesIO(img_bytes),
                caption="🏆 TOP 10 Oyinchilar\n📊 arenacs.uz/stats dan olingan\n\n💀 Kills  💙 Deaths  📈 K/D",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_top"),
                    InlineKeyboardButton("🌐 Saytda ko'rish", url=SITE_URL),
                ]]),
            )
        else:
            await msg.edit_text(
                "⚠️ TOP 10 olib bo'lmadi.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Stats", url=SITE_URL)]])
            )
    except Exception as e:
        logger.exception("cmd_top error")
        await msg.edit_text(f"❌ Xatolik: {e}")

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    try:
        if query.data == "refresh_status":
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, query_server)
            text, entities = build_status_payload(result)

            try:
                await query.edit_message_text(text=text, entities=entities, reply_markup=status_keyboard())
            except Exception:
                plain_text = text.replace("• ", "")
                await query.edit_message_text(text=plain_text, reply_markup=status_keyboard())

        elif query.data == "refresh_top":
            loop = asyncio.get_running_loop()
            top_result = await loop.run_in_executor(None, fetch_top10)
            if top_result["ok"] and top_result["players"]:
                img_bytes = await loop.run_in_executor(None, make_top10_image, top_result["players"])
                await query.edit_message_media(
                    media=InputMediaPhoto(
                        media=io.BytesIO(img_bytes),
                        caption="🏆 TOP 10 Oyinchilar\n📊 arenacs.uz/stats dan olingan\n\n💀 Kills  💙 Deaths  📈 K/D",
                    ),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_top"),
                        InlineKeyboardButton("🌐 Saytda ko'rish", url=SITE_URL),
                    ]]),
                )
    except Exception:
        logger.exception("callback error")

# =========================
# ERROR HANDLER
# =========================
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception: %s", context.error)

# =========================
# MAIN
# =========================
def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_error_handler(on_error)

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler(["status", "ststus"], cmd_status))
    app.add_handler(CommandHandler("top", cmd_top))

    # Online / Онлайн / Online botlar / онлайн ботлар
    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND
            & filters.Regex(r"(?iu)^\s*(online|онлайн|status|ststus)(\s+.*)?$"),
            on_online_message
        )
    )

    logger.info("Bot started: %s:%s", CS_HOST, CS_PORT)
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    run_bot()
