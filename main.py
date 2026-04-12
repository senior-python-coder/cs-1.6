#!/usr/bin/env python3
"""
CS 1.6 Server Status Bot + Web Sayt
pip install python-telegram-bot python-a2s beautifulsoup4 requests flask
"""

import asyncio
import threading
import logging

import a2s
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ═══════════════════════════════════════════════
#  SOZLAMALAR
# ═══════════════════════════════════════════════

TOKEN   = "8754991264:AAGgXExoHIpsvbpiABrJhMy5Tj-p0ebrVpw"
CS_HOST = "198.163.207.220"
CS_PORT = 27015

SITE_STATS_URL = "https://arenacs.uz/modules_extra/site_stats/ajax/actions.php"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
#  SERVER / SAYT SO'ROVLARI
# ═══════════════════════════════════════════════

def query_server() -> dict:
    addr = (CS_HOST, CS_PORT)
    try:
        info    = a2s.info(addr, timeout=5)
        players = a2s.players(addr, timeout=5)
        return {"online": True, "info": info, "players": players}
    except Exception as exc:
        return {"online": False, "error": str(exc)}


def query_site_stats() -> dict:
    headers = {
        "User-Agent":        "Mozilla/5.0",
        "X-Requested-With":  "XMLHttpRequest",
        "Referer":           "https://arenacs.uz/stats",
    }
    try:
        resp = requests.post(SITE_STATS_URL, headers=headers, timeout=8)
        soup = BeautifulSoup(resp.text, "html.parser")
        stats = {}
        for block in soup.select(".stats_mini_block"):
            name_el   = block.select_one(".name_stats")
            number_el = block.select_one(".span_number")
            if not name_el or not number_el:
                continue
            name      = name_el.get_text(strip=True)
            change_el = number_el.find("small")
            change    = change_el.get_text(strip=True) if change_el else ""
            if change_el:
                change_el.decompose()
            stats[name] = {"value": number_el.get_text(strip=True), "change": change}
        return {"ok": True, "stats": stats}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ═══════════════════════════════════════════════
#  YORDAMCHI FUNKSIYALAR
# ═══════════════════════════════════════════════

def fmt_time(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s   = divmod(rem, 60)
    if h:  return f"{h}h {m}m"
    if m:  return f"{m}m {s}s"
    return f"{s}s"


def medal(i: int) -> str:
    return {0: "🥇", 1: "🥈", 2: "🥉"}.get(i, f"{i + 1}.")


def star_bar(val: float, mx: float, n: int = 5) -> str:
    if mx == 0:
        return "☆" * n
    filled = max(0, min(round(val / mx * n), n))
    return "★" * filled + "☆" * (n - filled)


def fill_bar(count: int, total: int, width: int = 10) -> str:
    filled = round(count / total * width) if total else 0
    return "█" * filled + "░" * (width - filled)


STAT_MAP = {
    "Пользователей":       ("👤", "Foydalanuvchilar"),
    "Всего банов":         ("🔒", "Jami banlar"),
    "Серверов":            ("🖥", "Serverlar"),
    "Привилегированных":   ("⭐", "VIP / Adminlar"),
    "Заявок на разбан":    ("🔓", "Unban arizalar"),
    "Игроков на серверах": ("🎮", "Jami o'yinchilar"),
}


# ═══════════════════════════════════════════════
#  TELEGRAM XABAR QURUVCHLARI
# ═══════════════════════════════════════════════

def build_status_message(result: dict) -> str:
    if not result["online"]:
        return (
            "🔴 <b>SERVER OFFLINE</b>\n\n"
            f"🌐 <b>IP:</b> <code>{CS_HOST}:{CS_PORT}</code>\n"
            "❌ Server hozir javob bermayapti."
        )

    info         = result["info"]
    players      = result["players"]
    server_name  = info.server_name  or "CS 1.6 Server"
    map_name     = info.map_name     or "Noma'lum"
    player_count = info.player_count or 0
    max_players  = info.max_players  or 32
    ping         = round(info.ping * 1000) if info.ping else 0

    bar  = fill_bar(player_count, max_players)
    real = [p for p in players if p.name and p.name.strip()]

    if not real:
        player_lines = "  <i>Hozir hech kim yo'q</i>"
    else:
        player_lines = "\n".join(
            f"  {i}. 🎮 <b>{p.name.strip()}</b>"
            f"  ·  💀 {p.score or 0} kill"
            f"  ·  ⏱ {fmt_time(p.duration) if p.duration else '—'}"
            for i, p in enumerate(real, 1)
        )

    return (
        "🟢 <b>SERVER ONLINE</b>\n\n"
        f"🖥  <b>{server_name}</b>\n"
        f"🌐  <b>IP:</b> <code>{CS_HOST}:{CS_PORT}</code>\n"
        f"🗺  <b>Xarita:</b> <code>{map_name}</code>\n"
        f"📶  <b>Ping:</b> {ping} ms\n\n"
        f"👥  <b>Oyinchilar:</b> {player_count} / {max_players}\n"
        f"<code>[{bar}]</code>\n\n"
        f"📋 <b>Oyinchilar ro'yxati:</b>\n{player_lines}"
    )


def build_top_message(result: dict, mode: str = "kills") -> str:
    if not result["online"]:
        return "🔴 <b>Server offline</b> — TOP ko'rish mumkin emas."

    real = [p for p in result["players"] if p.name and p.name.strip()]
    if not real:
        return "📊 <b>TOP LIST</b>\n\n😴 <i>Hozir serverda hech kim yo'q</i>"

    if mode == "kills":
        srt   = sorted(real, key=lambda p: p.score or 0, reverse=True)
        mx    = srt[0].score or 1
        title = "💀 <b>TOP — ENG KO'P KILL</b>"
        lines = [
            f"{medal(i)}  <b>{p.name.strip()}</b>\n"
            f"    <code>{star_bar(p.score or 0, mx)}</code>"
            f"  💀 <b>{p.score or 0}</b>"
            f"  ⏱ {fmt_time(p.duration) if p.duration else '—'}"
            for i, p in enumerate(srt)
        ]
    else:
        srt   = sorted(real, key=lambda p: p.duration or 0, reverse=True)
        mx    = srt[0].duration or 1
        title = "⏱ <b>TOP — ENG KO'P O'YNAGAN</b>"
        lines = [
            f"{medal(i)}  <b>{p.name.strip()}</b>\n"
            f"    <code>{star_bar(p.duration or 0, mx)}</code>"
            f"  ⏱ <b>{fmt_time(p.duration) if p.duration else '—'}</b>"
            f"  💀 {p.score or 0}"
            for i, p in enumerate(srt)
        ]

    header = (
        f"{title}\n"
        f"🌐 <code>{CS_HOST}:{CS_PORT}</code>  ·  👥 {len(real)} oyinchi\n"
        f"{'─' * 26}\n\n"
    )
    return header + "\n\n".join(lines)


def build_site_stats_message(server_result: dict, site_result: dict) -> str:
    if server_result["online"]:
        info = server_result["info"]
        pc   = info.player_count or 0
        mp   = info.max_players  or 32
        bar  = fill_bar(pc, mp)
        ping = round(info.ping * 1000) if info.ping else 0
        srv_block = (
            "🟢 <b>SERVER ONLINE</b>\n"
            f"🗺  <code>{info.map_name}</code>  ·  📶 {ping} ms\n"
            f"👥  {pc} / {mp}  <code>[{bar}]</code>\n"
        )
    else:
        srv_block = "🔴 <b>SERVER OFFLINE</b>\n"

    if not site_result["ok"]:
        stats_block = "⚠️ <i>Sayt statistikasi olinmadi</i>"
    else:
        lines = []
        for ru_key, (emoji, uz_name) in STAT_MAP.items():
            entry = site_result["stats"].get(ru_key)
            if not entry:
                continue
            change = f"  <i>({entry['change']})</i>" if entry["change"] else ""
            lines.append(f"{emoji}  <b>{uz_name}:</b>  {entry['value']}{change}")
        stats_block = "\n".join(lines) or "⚠️ Ma'lumot topilmadi"

    return (
        f"{srv_block}\n"
        f"📊 <b>ARENACS.UZ STATISTIKASI</b>\n"
        f"{'─' * 26}\n"
        f"{stats_block}\n\n"
        f"🌐 <a href='https://arenacs.uz/stats'>arenacs.uz/stats</a>"
    )


# ═══════════════════════════════════════════════
#  TELEGRAM KLAVIATURALAR
# ═══════════════════════════════════════════════

def status_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Yangilash",   callback_data="refresh_status"),
        InlineKeyboardButton("📊 TOP",         callback_data="show_top_kills"),
        InlineKeyboardButton("🌐 Sayt stats",  callback_data="show_site_stats"),
    ]])


def top_keyboard(mode: str) -> InlineKeyboardMarkup:
    switch_btn = (
        InlineKeyboardButton("⏱ Vaqt bo'yicha", callback_data="show_top_time")
        if mode == "kills"
        else InlineKeyboardButton("💀 Kill bo'yicha", callback_data="show_top_kills")
    )
    refresh_cb = "refresh_top_kills" if mode == "kills" else "refresh_top_time"
    return InlineKeyboardMarkup([
        [switch_btn],
        [
            InlineKeyboardButton("🔄 Yangilash", callback_data=refresh_cb),
            InlineKeyboardButton("🔙 Server",    callback_data="back_to_status"),
        ],
    ])


def site_stats_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Yangilash", callback_data="refresh_site_stats"),
        InlineKeyboardButton("🔙 Server",    callback_data="back_to_status"),
    ]])


# ═══════════════════════════════════════════════
#  TELEGRAM BUYRUQ HANDLERLARI
# ═══════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "🎮 <b>CS 1.6 Server Status Bot</b>\n\n"
        f"🌐 Server: <code>{CS_HOST}:{CS_PORT}</code>\n\n"
        "📌 <b>Buyruqlar:</b>\n"
        "  🔹 <code>online</code> — Server holati\n"
        "  🔹 /status — Server holati\n"
        "  🔹 /top    — TOP o'yinchilar\n"
        "  🔹 /sayt   — Sayt statistikasi\n"
        "  🔹 /help   — Yordam"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg    = await update.message.reply_html("⏳ <b>So'ralmoqda...</b>")
    result = await asyncio.get_event_loop().run_in_executor(None, query_server)
    await msg.edit_text(
        build_status_message(result),
        parse_mode="HTML",
        reply_markup=status_keyboard(),
    )


async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg    = await update.message.reply_html("⏳ <b>TOP yuklanmoqda...</b>")
    result = await asyncio.get_event_loop().run_in_executor(None, query_server)
    await msg.edit_text(
        build_top_message(result, "kills"),
        parse_mode="HTML",
        reply_markup=top_keyboard("kills"),
    )


async def cmd_sayt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = await update.message.reply_html("⏳ <b>Yuklanmoqda...</b>")
    loop = asyncio.get_event_loop()
    sr   = await loop.run_in_executor(None, query_server)
    st   = await loop.run_in_executor(None, query_site_stats)
    await msg.edit_text(
        build_site_stats_message(sr, st),
        parse_mode="HTML",
        reply_markup=site_stats_keyboard(),
        disable_web_page_preview=True,
    )


async def on_online(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg    = await update.message.reply_html(
        "⏳ <b>So'ralmoqda...</b>",
        reply_to_message_id=update.message.message_id,
    )
    result = await asyncio.get_event_loop().run_in_executor(None, query_server)
    await msg.edit_text(
        build_status_message(result),
        parse_mode="HTML",
        reply_markup=status_keyboard(),
    )


# ═══════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ═══════════════════════════════════════════════

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data  = query.data
    loop  = asyncio.get_event_loop()

    # ── Status ──────────────────────────────────
    if data in ("refresh_status", "back_to_status"):
        await query.answer("🔄 Yangilanmoqda..." if data == "refresh_status" else "")
        r = await loop.run_in_executor(None, query_server)
        try:
            await query.edit_message_text(
                build_status_message(r),
                parse_mode="HTML",
                reply_markup=status_keyboard(),
            )
        except Exception:
            pass

    # ── TOP kills ───────────────────────────────
    elif data in ("show_top_kills", "refresh_top_kills"):
        await query.answer("🔄 Yangilanmoqda..." if "refresh" in data else "")
        r = await loop.run_in_executor(None, query_server)
        try:
            await query.edit_message_text(
                build_top_message(r, "kills"),
                parse_mode="HTML",
                reply_markup=top_keyboard("kills"),
            )
        except Exception:
            pass

    # ── TOP time ────────────────────────────────
    elif data in ("show_top_time", "refresh_top_time"):
        await query.answer("🔄 Yangilanmoqda..." if "refresh" in data else "")
        r = await loop.run_in_executor(None, query_server)
        try:
            await query.edit_message_text(
                build_top_message(r, "time"),
                parse_mode="HTML",
                reply_markup=top_keyboard("time"),
            )
        except Exception:
            pass

    # ── Sayt statistikasi ───────────────────────
    elif data in ("show_site_stats", "refresh_site_stats"):
        await query.answer("🔄 Yangilanmoqda..." if "refresh" in data else "")
        sr = await loop.run_in_executor(None, query_server)
        st = await loop.run_in_executor(None, query_site_stats)
        try:
            await query.edit_message_text(
                build_site_stats_message(sr, st),
                parse_mode="HTML",
                reply_markup=site_stats_keyboard(),
                disable_web_page_preview=True,
            )
        except Exception:
            pass


# ═══════════════════════════════════════════════
#  FLASK WEB SAYT
# ═══════════════════════════════════════════════

flask_app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ArenaCS — Server Status</title>
  <style>
    *, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      background: #0a0a0f;
      color: #e0e0e0;
      font-family: 'Segoe UI', system-ui, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    .container { max-width: 700px; width: 100%; }

    .header { text-align: center; margin-bottom: 28px; }

    .header h1 {
      font-size: 2.4em;
      background: linear-gradient(135deg, #ff6b35, #f7931e);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      letter-spacing: 3px;
      font-weight: 800;
    }

    .header p { color: #555; margin-top: 6px; font-size: 0.88em; letter-spacing: 1px; }

    .card {
      background: #13131a;
      border: 1px solid #1e1e2a;
      border-radius: 18px;
      padding: 22px 24px;
      margin-bottom: 14px;
    }

    .card-title {
      font-size: 0.72em;
      text-transform: uppercase;
      letter-spacing: 2.5px;
      color: #444;
      margin-bottom: 16px;
    }

    .status-row { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }

    .dot {
      width: 11px; height: 11px;
      border-radius: 50%;
      background: #2ecc71;
      box-shadow: 0 0 8px #2ecc71;
      animation: blink 2s infinite;
      flex-shrink: 0;
    }
    .dot.offline { background: #e74c3c; box-shadow: 0 0 8px #e74c3c; animation: none; }

    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.35} }

    .status-text { font-size: 1.05em; font-weight: 600; }

    .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

    .info-item { background: #0d0d14; border-radius: 12px; padding: 14px; }

    .info-label {
      font-size: 0.68em; color: #444;
      text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 5px;
    }

    .info-value { font-size: 1.2em; font-weight: 700; color: #fff; }
    .info-value.orange { color: #f7931e; }
    .info-value.green  { color: #2ecc71; }

    .bar-wrap { background: #0d0d14; border-radius: 12px; padding: 14px; margin-top: 10px; }
    .bar-label { font-size: 0.78em; color: #555; margin-bottom: 10px; }
    .bar-track { background: #1a1a2e; border-radius: 20px; height: 7px; overflow: hidden; }
    .bar-fill {
      height: 100%;
      background: linear-gradient(90deg, #ff6b35, #f7931e);
      border-radius: 20px;
      transition: width .5s ease;
    }

    .player-row {
      display: flex; align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid #161620;
      font-size: 0.88em; gap: 8px;
    }
    .player-row:last-child { border-bottom: none; }
    .player-num   { color: #333; min-width: 22px; }
    .player-name  { flex: 1; font-weight: 500; }
    .player-kills { color: #e74c3c; }
    .player-time  { color: #3498db; font-size: 0.83em; }

    .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }

    .stat-item {
      background: #0d0d14; border-radius: 12px;
      padding: 14px; display: flex; align-items: center; gap: 10px;
    }

    .stat-emoji { font-size: 1.5em; line-height: 1; }
    .stat-val   { font-size: 1.05em; font-weight: 700; }
    .stat-name  { font-size: 0.68em; color: #444; margin-top: 2px; }
    .stat-change { font-size: 0.68em; color: #2ecc71; margin-left: 4px; }

    .tg-btn {
      display: block; text-align: center;
      background: linear-gradient(135deg, #2196F3, #1565C0);
      color: #fff; text-decoration: none;
      padding: 14px; border-radius: 14px;
      font-weight: 600; letter-spacing: 1px;
      margin-top: 14px;
      transition: opacity .2s, transform .15s;
    }
    .tg-btn:hover { opacity: .88; transform: translateY(-1px); }

    .refresh-info { text-align: center; color: #2a2a3a; font-size: 0.72em; margin-top: 14px; }
    .empty        { color: #333; text-align: center; padding: 22px; font-size: 0.88em; }

    @media (max-width: 480px) {
      .info-grid, .stats-grid { grid-template-columns: 1fr; }
      .header h1 { font-size: 1.8em; }
    }
  </style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>⚡ ARENACS</h1>
    <p>CS 1.6 Server &mdash; Real-time holat</p>
  </div>

  <div class="card">
    <div class="card-title">🖥 Server holati</div>
    <div class="status-row">
      <div class="dot" id="status-dot"></div>
      <span class="status-text" id="status-text">Yuklanmoqda...</span>
    </div>
    <div class="info-grid" id="server-info" style="display:none">
      <div class="info-item">
        <div class="info-label">Xarita</div>
        <div class="info-value orange" id="map-name">—</div>
      </div>
      <div class="info-item">
        <div class="info-label">Ping</div>
        <div class="info-value green" id="ping-val">—</div>
      </div>
    </div>
    <div class="bar-wrap" id="bar-wrap" style="display:none">
      <div class="bar-label">
        👥 Oyinchilar: <b id="player-count">0</b> / <b id="max-players">0</b>
      </div>
      <div class="bar-track">
        <div class="bar-fill" id="bar-fill" style="width:0%"></div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-title">🎮 Hozirgi oyinchilar</div>
    <div id="players-list"><div class="empty">Yuklanmoqda...</div></div>
  </div>

  <div class="card">
    <div class="card-title">📊 Sayt statistikasi</div>
    <div class="stats-grid" id="site-stats">
      <div class="empty" style="grid-column:span 2">Yuklanmoqda...</div>
    </div>
  </div>

  <a href="https://t.me/cs_status_online_bot" class="tg-btn">
    📱 Telegram Botga o'tish
  </a>

  <div class="refresh-info" id="refresh-info">Yangilanmoqda...</div>
</div>

<script>
  const STAT_ICONS = {
    "Пользователей":       ["👤", "Foydalanuvchilar"],
    "Всего банов":         ["🔒", "Jami banlar"],
    "Серверов":            ["🖥", "Serverlar"],
    "Привилегированных":   ["⭐", "VIP/Adminlar"],
    "Игроков на серверах": ["🎮", "Jami o'yinchilar"],
    "Заявок на разбан":    ["🔓", "Unban arizalar"],
  };

  function fmtTime(sec) {
    sec = Math.floor(sec);
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = sec % 60;
    if (h) return h + "h " + m + "m";
    if (m) return m + "m " + s + "s";
    return s + "s";
  }

  async function loadData() {
    try {
      const data = await fetch("/api/status").then(r => r.json());
      const dot  = document.getElementById("status-dot");
      const stxt = document.getElementById("status-text");

      if (data.online) {
        dot.className    = "dot";
        stxt.textContent = "Online — " + (data.server_name || "CS 1.6");

        document.getElementById("server-info").style.display = "grid";
        document.getElementById("bar-wrap").style.display    = "block";
        document.getElementById("map-name").textContent      = data.map  || "—";
        document.getElementById("ping-val").textContent      = data.ping + " ms";
        document.getElementById("player-count").textContent  = data.player_count;
        document.getElementById("max-players").textContent   = data.max_players;

        const pct = data.max_players > 0
          ? (data.player_count / data.max_players * 100).toFixed(1) : 0;
        document.getElementById("bar-fill").style.width = pct + "%";

        const pl = document.getElementById("players-list");
        if (data.players && data.players.length > 0) {
          pl.innerHTML = data.players.map((p, i) =>
            `<div class="player-row">
              <span class="player-num">${i + 1}</span>
              <span class="player-name">${p.name}</span>
              <span class="player-kills">💀 ${p.score}</span>
              <span class="player-time">⏱ ${fmtTime(p.duration)}</span>
            </div>`
          ).join("");
        } else {
          pl.innerHTML = '<div class="empty">😴 Hozir hech kim yo\'q</div>';
        }
      } else {
        dot.className    = "dot offline";
        stxt.textContent = "Offline";
        document.getElementById("players-list").innerHTML =
          '<div class="empty">Server offline</div>';
      }

      const sg = document.getElementById("site-stats");
      if (data.site_stats && Object.keys(data.site_stats).length) {
        const html = Object.entries(data.site_stats)
          .filter(([k]) => STAT_ICONS[k])
          .map(([k, v]) => {
            const [icon, name] = STAT_ICONS[k];
            const ch = v.change ? `<span class="stat-change">${v.change}</span>` : "";
            return `<div class="stat-item">
              <span class="stat-emoji">${icon}</span>
              <div>
                <div class="stat-val">${v.value}${ch}</div>
                <div class="stat-name">${name}</div>
              </div>
            </div>`;
          }).join("");
        sg.innerHTML = html ||
          '<div class="empty" style="grid-column:span 2">Ma\'lumot yo\'q</div>';
      }

      document.getElementById("refresh-info").textContent =
        "Oxirgi yangilanish: " + new Date().toLocaleTimeString("uz-UZ") +
        "  ·  Har 30 soniyada yangilanadi";

    } catch (e) {
      console.error("loadData error:", e);
    }
  }

  loadData();
  setInterval(loadData, 30_000);
</script>
</body>
</html>
"""


@flask_app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@flask_app.route("/api/status")
def api_status():
    server = query_server()
    site   = query_site_stats()
    result = {"online": server["online"], "site_stats": {}}

    if server["online"]:
        info    = server["info"]
        players = server["players"]
        result.update({
            "server_name":  info.server_name,
            "map":          info.map_name,
            "ping":         round(info.ping * 1000) if info.ping else 0,
            "player_count": info.player_count or 0,
            "max_players":  info.max_players  or 32,
            "players": [
                {"name": p.name, "score": p.score or 0, "duration": p.duration or 0}
                for p in players
                if p.name and p.name.strip()
            ],
        })

    if site["ok"]:
        result["site_stats"] = site["stats"]

    return jsonify(result)


@flask_app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ═══════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════

def run_flask() -> None:
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)


def main() -> None:
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Web sayt: http://0.0.0.0:8080")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("top",    cmd_top))
    app.add_handler(CommandHandler("sayt",   cmd_sayt))
    app.add_handler(MessageHandler(filters.Regex(r"(?i)^online$"), on_online))
    app.add_handler(CallbackQueryHandler(on_callback))

    print("CS 1.6 Status Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
