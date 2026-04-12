#!/usr/bin/env python3
# =============================================
# CS 1.6 Server Status Bot — Python
# pip install python-telegram-bot python-a2s
# =============================================

import asyncio
import a2s
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ──────────────────────────────────────────────
# SOZLAMALAR
# ──────────────────────────────────────────────
TOKEN   = "8754991264:AAGgXExoHIpsvbpiABrJhMy5Tj-p0ebrVpw"
CS_HOST = "198.163.207.220"
CS_PORT = 27015

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
    if h > 0:
        return f"{h}h {m % 60}m"
    if m > 0:
        return f"{m}m {s % 60}s"
    return f"{s}s"

def medal(index: int) -> str:
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    return medals.get(index, f"{index + 1}.")

def star_bar(value: float, max_value: float, length: int = 5) -> str:
    if max_value == 0:
        return "☆" * length
    filled = round((value / max_value) * length)
    filled = max(0, min(filled, length))
    return "★" * filled + "☆" * (length - filled)

# ──────────────────────────────────────────────
# SERVER HOLATI XABARI
# ──────────────────────────────────────────────
def build_status_message(result: dict) -> str:
    if not result["online"]:
        return (
            "🔴 <b>SERVER OFFLINE</b>\n\n"
            f"🌐 <b>IP:</b> <code>{CS_HOST}:{CS_PORT}</code>\n"
            "❌ Server hozir javob bermayapti."
        )

    info    = result["info"]
    players = result["players"]

    server_name  = info.server_name  or "CS 1.6 Server"
    map_name     = info.map_name     or "Noma'lum"
    player_count = info.player_count or 0
    max_players  = info.max_players  or 32
    ping         = round(info.ping * 1000) if info.ping else 0

    filled = round(player_count / max_players * 10) if max_players else 0
    bar    = "█" * filled + "░" * (10 - filled)

    real_players = [p for p in players if p.name and p.name.strip()]
    if not real_players:
        player_list = "  <i>Hozir hech kim yo'q</i>"
    else:
        lines = []
        for i, p in enumerate(real_players, 1):
            name  = p.name.strip()
            score = p.score if p.score is not None else 0
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
        f"📋 <b>Oyinchilar:</b>\n"
        f"{player_list}"
    )

# ──────────────────────────────────────────────
# TOP LIST XABARI
# ──────────────────────────────────────────────
def build_top_message(result: dict, mode: str = "kills") -> str:
    if not result["online"]:
        return "🔴 <b>Server offline</b> — TOP ko'rish mumkin emas."

    players      = result["players"]
    real_players = [p for p in players if p.name and p.name.strip()]

    if not real_players:
        return (
            "📊 <b>TOP LIST</b>\n\n"
            "😴 <i>Hozir serverda hech kim yo'q</i>\n\n"
            f"🌐 <code>{CS_HOST}:{CS_PORT}</code>"
        )

    total = len(real_players)

    if mode == "kills":
        sorted_p  = sorted(real_players, key=lambda p: p.score or 0, reverse=True)
        max_val   = sorted_p[0].score or 1
        title     = "💀 <b>TOP — ENG KO'P KILL</b>"
        lines = []
        for i, p in enumerate(sorted_p):
            name  = p.name.strip()
            score = p.score if p.score is not None else 0
            time  = format_time(p.duration) if p.duration else "—"
            stars = star_bar(score, max_val)
            lines.append(
                f"{medal(i)} <b>{name}</b>\n"
                f"    {stars}  💀 <b>{score}</b> kill  ⏱ {time}"
            )
    else:
        sorted_p  = sorted(real_players, key=lambda p: p.duration or 0, reverse=True)
        max_val   = sorted_p[0].duration or 1
        title     = "⏱ <b>TOP — ENG KO'P O'YNAGAN</b>"
        lines = []
        for i, p in enumerate(sorted_p):
            name  = p.name.strip()
            score = p.score if p.score is not None else 0
            dur   = p.duration or 0
            time  = format_time(dur) if dur else "—"
            stars = star_bar(dur, max_val)
            lines.append(
                f"{medal(i)} <b>{name}</b>\n"
                f"    {stars}  ⏱ <b>{time}</b>  💀 {score} kill"
            )

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
        InlineKeyboardButton("📊 TOP list",  callback_data="show_top_kills"),
    ]])

def top_keyboard(mode: str):
    if mode == "kills":
        switch_btn = InlineKeyboardButton("⏱ Vaqt bo'yicha", callback_data="show_top_time")
    else:
        switch_btn = InlineKeyboardButton("💀 Kill bo'yicha", callback_data="show_top_kills")

    refresh_cb = "refresh_top_kills" if mode == "kills" else "refresh_top_time"

    return InlineKeyboardMarkup([
        [switch_btn],
        [
            InlineKeyboardButton("🔄 Yangilash", callback_data=refresh_cb),
            InlineKeyboardButton("🔙 Server",    callback_data="back_to_status"),
        ]
    ])

# ──────────────────────────────────────────────
# HANDLERLAR
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
    msg = await update.message.reply_html("⏳ <b>TOP list yuklanmoqda...</b>")
    result = await asyncio.get_event_loop().run_in_executor(None, query_server)
    await msg.edit_text(
        build_top_message(result, mode="kills"),
        parse_mode="HTML",
        reply_markup=top_keyboard("kills")
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
    query = update.callback_query
    data  = query.data

    if data in ("refresh_status", "back_to_status"):
        await query.answer("🔄 Yangilanmoqda..." if data == "refresh_status" else "")
        result = await asyncio.get_event_loop().run_in_executor(None, query_server)
        try:
            await query.edit_message_text(
                build_status_message(result),
                parse_mode="HTML",
                reply_markup=status_keyboard()
            )
        except Exception:
            pass

    elif data in ("show_top_kills", "refresh_top_kills"):
        await query.answer("🔄 Yangilanmoqda..." if "refresh" in data else "")
        result = await asyncio.get_event_loop().run_in_executor(None, query_server)
        try:
            await query.edit_message_text(
                build_top_message(result, mode="kills"),
                parse_mode="HTML",
                reply_markup=top_keyboard("kills")
            )
        except Exception:
            pass

    elif data in ("show_top_time", "refresh_top_time"):
        await query.answer("🔄 Yangilanmoqda..." if "refresh" in data else "")
        result = await asyncio.get_event_loop().run_in_executor(None, query_server)
        try:
            await query.edit_message_text(
                build_top_message(result, mode="time"),
                parse_mode="HTML",
                reply_markup=top_keyboard("time")
            )
        except Exception:
            pass

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
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
