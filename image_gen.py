"""
image_gen.py — CS 1.6 Bot uchun rasm generatsiya moduli
Ishlatish: from image_gen import make_status_image, make_top_image, make_site_stats_image
Har funksiya BytesIO obyekti qaytaradi (telegram photo sifatida yuborish uchun)
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import math

# ─── SHRIFTLAR ───────────────────────────────────────────────
FONT_DIR = "/usr/share/fonts/truetype/google-fonts/"
DEJA_DIR = "/usr/share/fonts/truetype/dejavu/"

def _font(size, bold=False):
    try:
        path = FONT_DIR + ("Poppins-Bold.ttf" if bold else "Poppins-Regular.ttf")
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def _mono(size):
    try:
        return ImageFont.truetype(DEJA_DIR + "DejaVuSansMono.ttf", size)
    except:
        return ImageFont.load_default()

# ─── RANGLAR ────────────────────────────────────────────────
BG       = "#0a0a0f"
CARD     = "#13131a"
BORDER   = "#222233"
ORANGE   = "#f7931e"
ORANGE2  = "#ff6b35"
GREEN    = "#2ecc71"
RED      = "#e74c3c"
BLUE     = "#3498db"
GRAY     = "#555566"
WHITE    = "#f0f0f0"
GOLD     = "#FFD700"
SILVER   = "#C0C0C0"
BRONZE   = "#CD7F32"

W = 820  # Rasm kengligi

# ─── YORDAMCHI FUNKSIYALAR ───────────────────────────────────

def _new_image(height):
    img = Image.new("RGB", (W, height), color=BG)
    draw = ImageDraw.Draw(img)
    return img, draw

def _gradient_rect(draw, x1, y1, x2, y2, color1, color2, vertical=True):
    """Gradient to'rtburchak chizish"""
    r1,g1,b1 = int(color1[1:3],16), int(color1[3:5],16), int(color1[5:7],16)
    r2,g2,b2 = int(color2[1:3],16), int(color2[3:5],16), int(color2[5:7],16)
    steps = (y2 - y1) if vertical else (x2 - x1)
    for i in range(steps):
        t = i / max(steps - 1, 1)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        if vertical:
            draw.line([(x1, y1 + i), (x2, y1 + i)], fill=(r, g, b))
        else:
            draw.line([(x1 + i, y1), (x1 + i, y2)], fill=(r, g, b))

def _rounded_rect(draw, x1, y1, x2, y2, r=12, fill=CARD, outline=BORDER, width=1):
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill, outline=outline, width=width)

def _bar(draw, x, y, w, h, value, max_val, color1=ORANGE2, color2=ORANGE, bg="#1a1a2e", r=6):
    """Progress bar"""
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=bg)
    if max_val > 0:
        filled = int(w * min(value / max_val, 1.0))
        if filled > r*2:
            _gradient_rect(draw, x, y, x+filled, y+h, color1, color2, vertical=False)
            # Rounded ends
            draw.ellipse([x+filled-h, y, x+filled, y+h], fill=color2)
            draw.ellipse([x, y, x+h, y+h], fill=color1)

def _medal(i):
    return {0: ("🥇", GOLD), 1: ("🥈", SILVER), 2: ("🥉", BRONZE)}.get(i, (f"{i+1}.", GRAY))

def _format_time(seconds):
    s = int(seconds or 0)
    h, m = s // 3600, (s % 3600) // 60
    if h > 0: return f"{h}h {m}m"
    if m > 0: return f"{m}m {s%60}s"
    return f"{s}s"

def _header(draw, img, title, subtitle=""):
    """Yuqori sarlavha qismi"""
    # Gradient chiziq
    _gradient_rect(draw, 0, 0, W, 4, ORANGE2, ORANGE, vertical=False)
    
    f_title = _font(36, bold=True)
    f_sub   = _font(15)
    
    draw.text((W//2, 38), title, font=f_title, fill=WHITE, anchor="mm")
    if subtitle:
        draw.text((W//2, 68), subtitle, font=f_sub, fill=GRAY, anchor="mm")

def _footer(draw, y, host, port):
    """Quyi IP qismi"""
    f = _mono(13)
    txt = f"🌐  {host}:{port}  •  arenacs.uz"
    draw.text((W//2, y), txt, font=f, fill=GRAY, anchor="mm")
    # Chiziq
    draw.line([(40, y-14), (W-40, y-14)], fill=BORDER, width=1)

def _to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf

# ─────────────────────────────────────────────────────────────
# 1. STATUS RASMI
# ─────────────────────────────────────────────────────────────

def make_status_image(result, host="198.163.207.220", port=27015):
    """Server holati rasmi"""
    players_data = []
    online = result.get("online", False)

    if online:
        info = result["info"]
        players_data = [p for p in result.get("players", []) if p.name and p.name.strip()]
    
    rows = max(len(players_data), 1)
    H = 180 + 110 + rows * 44 + 80
    img, draw = _new_image(H)

    # HEADER
    _header(draw, img, "⚡  ARENACS  STATUS", f"CS 1.6 Server — {host}:{port}")

    y = 90

    # STATUS KARTA
    _rounded_rect(draw, 30, y, W-30, y+90, r=14, fill=CARD, outline=GREEN if online else RED, width=2)
    
    dot_color = GREEN if online else RED
    draw.ellipse([50, y+22, 68, y+40], fill=dot_color)
    # Pulse ring
    draw.ellipse([44, y+16, 74, y+46], outline=dot_color, width=1)

    f_big  = _font(22, bold=True)
    f_med  = _font(15)
    f_sm   = _font(13)

    status_txt = "🟢  ONLINE" if online else "🔴  OFFLINE"
    draw.text((85, y+22), status_txt, font=f_big, fill=GREEN if online else RED)

    if online:
        sv_name = (info.server_name or "CS 1.6")[:40]
        draw.text((85, y+52), sv_name, font=f_sm, fill=GRAY)

        # Map va ping
        map_name = info.map_name or "—"
        ping = round(info.ping * 1000) if info.ping else 0
        pc = info.player_count or 0
        mx = info.max_players or 32

        draw.text((W-200, y+15), f"🗺  {map_name}", font=f_med, fill=WHITE)
        ping_col = GREEN if ping < 80 else (ORANGE if ping < 150 else RED)
        draw.text((W-200, y+40), f"📶  {ping} ms", font=f_med, fill=ping_col)
        draw.text((W-200, y+65), f"👥  {pc} / {mx}", font=f_med, fill=WHITE)
    else:
        draw.text((85, y+52), "Server hozir javob bermayapti", font=f_sm, fill=GRAY)

    y += 100

    # PLAYER BAR
    if online:
        pc = info.player_count or 0
        mx = info.max_players or 32
        _rounded_rect(draw, 30, y, W-30, y+54, r=10, fill=CARD)
        draw.text((50, y+8), "OYINCHILAR", font=_font(10), fill=GRAY)
        pct_col = GREEN if pc < mx*0.7 else (ORANGE if pc < mx else RED)
        draw.text((W-50, y+8), f"{pc}/{mx}", font=_font(13, bold=True), fill=pct_col, anchor="ra")
        _bar(draw, 50, y+28, W-100, 14, pc, mx)
        y += 64
    else:
        y += 10

    # OYINCHILAR RO'YXATI
    f_name  = _font(14, bold=True)
    f_stats = _font(13)
    f_num   = _font(12)

    if players_data:
        _rounded_rect(draw, 30, y, W-30, y + len(players_data)*44 + 20, r=12, fill=CARD)
        draw.text((50, y+8), "HOZIRGI OYINCHILAR", font=_font(10), fill=GRAY)
        y += 28
        for i, p in enumerate(players_data):
            row_y = y + i * 44
            if i % 2 == 0:
                draw.rounded_rectangle([40, row_y, W-40, row_y+40], radius=6, fill="#0d0d14")
            
            # Raqam
            draw.text((58, row_y+12), str(i+1), font=f_num, fill=GRAY)
            # Ism
            name = (p.name.strip() or "—")[:22]
            draw.text((80, row_y+11), name, font=f_name, fill=WHITE)
            # Kill
            draw.text((W-280, row_y+12), f"💀 {p.score or 0}", font=f_stats, fill=RED)
            # Vaqt
            draw.text((W-160, row_y+12), f"⏱ {_format_time(p.duration)}", font=f_stats, fill=BLUE)
            # Bar (kill uchun)
            mx_score = max((pl.score or 0) for pl in players_data) or 1
            _bar(draw, 80, row_y+32, 200, 5, p.score or 0, mx_score, GREEN, GREEN, "#1a1a2e", r=2)

        y += len(players_data) * 44 + 20
    else:
        _rounded_rect(draw, 30, y, W-30, y+50, r=12, fill=CARD)
        draw.text((W//2, y+25), "😴  Hozir hech kim yo'q", font=f_med, fill=GRAY, anchor="mm")
        y += 60

    # FOOTER
    _footer(draw, y+24, host, port)

    return _to_bytes(img)

# ─────────────────────────────────────────────────────────────
# 2. TOP RASMI
# ─────────────────────────────────────────────────────────────

def make_top_image(result, mode="kills", host="198.163.207.220", port=27015):
    """TOP oyinchilar rasmi"""
    online = result.get("online", False)
    players_data = []
    if online:
        all_p = result.get("players", [])
        players_data = [p for p in all_p if p.name and p.name.strip()]
        if mode == "kills":
            players_data = sorted(players_data, key=lambda p: p.score or 0, reverse=True)
        else:
            players_data = sorted(players_data, key=lambda p: p.duration or 0, reverse=True)

    rows = max(len(players_data), 1)
    H = 150 + rows * 70 + 80
    img, draw = _new_image(H)

    title = "💀  TOP — KILL" if mode == "kills" else "⏱  TOP — VAQT"
    _header(draw, img, title, "Hozirgi sessiya natijalari")

    y = 88
    f_name  = _font(16, bold=True)
    f_stats = _font(14)
    f_sm    = _font(12)

    if not online:
        _rounded_rect(draw, 30, y, W-30, y+60, r=12, fill=CARD, outline=RED, width=2)
        draw.text((W//2, y+30), "🔴  Server offline — TOP ko'rish mumkin emas", font=f_stats, fill=RED, anchor="mm")
    elif not players_data:
        _rounded_rect(draw, 30, y, W-30, y+60, r=12, fill=CARD)
        draw.text((W//2, y+30), "😴  Hozir serverda hech kim yo'q", font=f_stats, fill=GRAY, anchor="mm")
    else:
        mx_val = (players_data[0].score or 1) if mode == "kills" else (players_data[0].duration or 1)
        medal_colors = [GOLD, SILVER, BRONZE]

        for i, p in enumerate(players_data):
            row_y = y + i * 70
            val = (p.score or 0) if mode == "kills" else (p.duration or 0)
            pct = val / mx_val if mx_val else 0

            # Karta
            bg_col = "#16161f" if i % 2 == 0 else CARD
            outline_col = medal_colors[i] if i < 3 else BORDER
            _rounded_rect(draw, 30, row_y, W-30, row_y+62, r=10, fill=bg_col, outline=outline_col, width=2 if i < 3 else 1)

            # Medal
            m_txt, m_col = _medal(i)
            draw.text((56, row_y+20), m_txt, font=_font(20, bold=True), fill=m_col, anchor="mm")

            # Ism
            name = (p.name.strip() or "—")[:24]
            draw.text((75, row_y+10), name, font=f_name, fill=WHITE)

            # Asosiy stat
            if mode == "kills":
                main_txt = f"💀  {p.score or 0} kill"
                sec_txt  = f"⏱ {_format_time(p.duration)}"
            else:
                main_txt = f"⏱  {_format_time(p.duration)}"
                sec_txt  = f"💀 {p.score or 0} kill"

            draw.text((75, row_y+34), main_txt, font=f_stats, fill=ORANGE if i == 0 else WHITE)
            draw.text((W-180, row_y+10), sec_txt, font=f_sm, fill=GRAY)

            # Bar
            bar_col1 = medal_colors[i] if i < 3 else GRAY
            bar_col2 = ORANGE if i == 0 else bar_col1
            _bar(draw, 75, row_y+52, W-120, 6, val, mx_val, bar_col1, bar_col2, "#1a1a2e", r=3)

            # % ko'rsatgich
            draw.text((W-60, row_y+28), f"{int(pct*100)}%", font=f_sm, fill=GRAY, anchor="rm")

        y += rows * 70

    _footer(draw, y+24, host, port)
    return _to_bytes(img)

# ─────────────────────────────────────────────────────────────
# 3. SAYT STATISTIKA RASMI
# ─────────────────────────────────────────────────────────────

STAT_MAP = [
    ("Пользователей",       "👤", "Foydalanuvchilar", BLUE),
    ("Всего банов",         "🔒", "Jami banlar",       RED),
    ("Серверов",            "🖥", "Serverlar",         ORANGE),
    ("Привилегированных",   "⭐", "VIP / Adminlar",    GOLD),
    ("Заявок на разбан",    "🔓", "Unban arizalar",    GREEN),
    ("Игроков на серверах", "🎮", "Jami o'yinchilar",  "#9b59b6"),
]

def make_site_stats_image(server_result, site_result, host="198.163.207.220", port=27015):
    """Sayt statistikasi rasmi"""
    H = 160 + 90 + 3 * 90 + 60
    img, draw = _new_image(H)

    _header(draw, img, "📊  ARENACS.UZ STATISTIKA", "arenacs.uz sayt ko'rsatkichlari")

    y = 88

    # Server mini-karta
    online = server_result.get("online", False)
    sv_col = GREEN if online else RED
    _rounded_rect(draw, 30, y, W-30, y+70, r=12, fill=CARD, outline=sv_col, width=2)
    
    f_med = _font(15)
    f_sm  = _font(13)

    if online:
        info = server_result["info"]
        pc   = info.player_count or 0
        mx   = info.max_players  or 32
        ping = round(info.ping * 1000) if info.ping else 0

        draw.text((55, y+12), "🟢  SERVER ONLINE", font=_font(16, bold=True), fill=GREEN)
        draw.text((55, y+38), f"🗺 {info.map_name}", font=f_sm, fill=GRAY)
        draw.text((300, y+38), f"📶 {ping} ms", font=f_sm, fill=GREEN if ping<80 else ORANGE)
        draw.text((W-60, y+12), f"{pc}/{mx}", font=_font(18, bold=True), fill=ORANGE, anchor="ra")
        draw.text((W-60, y+38), "oyinchi", font=f_sm, fill=GRAY, anchor="ra")
        _bar(draw, 55, y+58, W-90, 7, pc, mx)
    else:
        draw.text((W//2, y+32), "🔴  SERVER OFFLINE", font=_font(18, bold=True), fill=RED, anchor="mm")

    y += 82

    # Statistika kartalar (2 ustun x 3 qator)
    stats = site_result.get("stats", {}) if site_result.get("ok") else {}

    col_w = (W - 70) // 2
    for idx, (ru_key, emoji, uz_name, color) in enumerate(STAT_MAP):
        col  = idx % 2
        row  = idx // 2
        cx   = 30 + col * (col_w + 10)
        cy   = y + row * 88

        _rounded_rect(draw, cx, cy, cx+col_w, cy+78, r=12, fill=CARD, outline=BORDER)
        # Yon rang chizig'i
        _gradient_rect(draw, cx, cy+10, cx+4, cy+68, color, color+"88", vertical=True)

        draw.text((cx+20, cy+12), emoji, font=_font(22), fill=color)
        draw.text((cx+20, cy+46), uz_name, font=_font(11), fill=GRAY)

        val_txt = stats.get(ru_key, {}).get("value", "—")
        ch_txt  = stats.get(ru_key, {}).get("change", "")
        draw.text((cx+col_w-10, cy+18), val_txt, font=_font(20, bold=True), fill=WHITE, anchor="ra")
        if ch_txt:
            draw.text((cx+col_w-10, cy+46), ch_txt, font=_font(11), fill=GREEN, anchor="ra")

    y += 3 * 88 + 5

    _footer(draw, y+20, host, port)
    return _to_bytes(img)
