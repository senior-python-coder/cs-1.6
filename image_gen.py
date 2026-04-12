"""
image_gen.py — CS 1.6 Bot uchun rasm generatsiya moduli (SHARP / 2x scale)
Har funksiya BytesIO qaytaradi — telegram.reply_photo(photo=...) uchun
"""

from PIL import Image, ImageDraw, ImageFont
import io

# ─── 2x SCALE (retina-sharp) ─────────────────
S = 2          # Hamma o'lchamni S barobarga kattalashtir
W = 860        # Kenglik (mantiqiy px)

# ─── SHRIFTLAR ───────────────────────────────
_POP = "/usr/share/fonts/truetype/google-fonts/Poppins-{}.ttf"
_DEJ = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

def F(size, bold=False):
    try:
        name = "Bold" if bold else "Regular"
        return ImageFont.truetype(_POP.format(name), size * S)
    except:
        return ImageFont.load_default()

def FM(size):
    try:
        return ImageFont.truetype(_DEJ, size * S)
    except:
        return ImageFont.load_default()

# ─── RANGLAR ────────────────────────────────
BG      = "#0a0a0f"
CARD    = "#13131a"
CARD2   = "#0d0d14"
BORDER  = "#1e1e2e"
ORANGE  = "#f7931e"
ORANGE2 = "#ff6b35"
GREEN   = "#2ecc71"
RED     = "#e74c3c"
BLUE    = "#3b9fe8"
GRAY    = "#4a4a5e"
GRAY2   = "#666680"
WHITE   = "#f0f0f8"
GOLD    = "#FFD700"
SILVER  = "#C0C0C0"
BRONZE  = "#CD7F32"

# ─── YORDAMCHI ───────────────────────────────

def _canvas(h_logical):
    img = Image.new("RGB", (W * S, h_logical * S), BG)
    d   = ImageDraw.Draw(img)
    return img, d

def _shrink(img):
    return img.resize((W, img.height // S), Image.LANCZOS)

def _to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf

def sc(x):
    return x * S

def _rr(d, x1, y1, x2, y2, r=12, fill=CARD, outline=BORDER, width=1):
    d.rounded_rectangle(
        [sc(x1), sc(y1), sc(x2), sc(y2)],
        radius=sc(r), fill=fill, outline=outline, width=sc(width)
    )

def _grad_h(d, x1, y1, x2, y2, c1, c2):
    r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
    steps = sc(x2 - x1)
    for i in range(steps):
        t = i / max(steps - 1, 1)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        d.line([(sc(x1) + i, sc(y1)), (sc(x1) + i, sc(y2))], fill=(r, g, b))

def _bar(d, x, y, w, h, val, mx, c1=ORANGE2, c2=ORANGE, bg=CARD2, r=4):
    _rr(d, x, y, x+w, y+h, r=r, fill=bg, outline=bg)
    if mx > 0 and val > 0:
        fw = int(w * min(val / mx, 1.0))
        if fw >= r * 2:
            _grad_h(d, x, y, x+fw, y+h, c1, c2)
            d.ellipse([sc(x), sc(y), sc(x+h), sc(y+h)], fill=c1)
            d.ellipse([sc(x+fw-h), sc(y), sc(x+fw), sc(y+h)], fill=c2)

def _txt(d, x, y, text, font, fill=WHITE, anchor="la"):
    d.text((sc(x), sc(y)), text, font=font, fill=fill, anchor=anchor)

def _fmt_time(sec):
    s = int(sec or 0)
    h, m = s // 3600, (s % 3600) // 60
    if h: return f"{h}h {m}m"
    if m: return f"{m}m {s%60}s"
    return f"{s}s"

def _medal_col(i):
    return [GOLD, SILVER, BRONZE][i] if i < 3 else GRAY2

def _header(d, title, subtitle):
    _grad_h(d, 0, 0, W, 3, ORANGE2, ORANGE)
    _txt(d, W//2, 36, title,    F(26, bold=True), fill=WHITE,  anchor="mm")
    _txt(d, W//2, 62, subtitle, F(13),            fill=GRAY2,  anchor="mm")

def _footer(d, y, host, port):
    d.line([sc(40), sc(y-10), sc(W-40), sc(y-10)], fill=BORDER, width=sc(1))
    _txt(d, W//2, y+4, f"🌐  {host}:{port}  •  arenacs.uz",
         FM(12), fill=GRAY, anchor="mm")


# ═══════════════════════════════════════════════
# 1. STATUS RASMI
# ═══════════════════════════════════════════════
def make_status_image(result, host="198.163.207.220", port=27015):
    online  = result.get("online", False)
    players = []
    if online:
        info    = result["info"]
        players = [p for p in result.get("players", []) if p.name and p.name.strip()]

    rows   = max(len(players), 1)
    H      = 88 + 88 + 64 + rows * 48 + 56
    img, d = _canvas(H)

    _header(d, "⚡  ARENACS  STATUS", f"CS 1.6 Server — {host}:{port}")
    y = 80

    # Status kartasi
    sv_col = GREEN if online else RED
    _rr(d, 20, y, W-20, y+82, r=14, fill=CARD, outline=sv_col, width=2)
    d.ellipse([sc(36), sc(y+18), sc(52), sc(y+34)], fill=sv_col)
    d.ellipse([sc(30), sc(y+12), sc(58), sc(y+40)], outline=sv_col+"55", width=sc(1))

    if online:
        _txt(d, 66, y+12, "🟢  ONLINE",                   F(18, bold=True), fill=GREEN)
        _txt(d, 66, y+40, (info.server_name or "CS 1.6")[:42], F(13),       fill=GRAY2)
        ping  = round(info.ping * 1000) if info.ping else 0
        pc    = info.player_count or 0
        mx    = info.max_players  or 32
        p_col = GREEN if ping < 80 else (ORANGE if ping < 150 else RED)
        _txt(d, W-24, y+12, f"🗺  {info.map_name}", F(14), fill=WHITE,  anchor="ra")
        _txt(d, W-24, y+36, f"📶  {ping} ms",       F(13), fill=p_col,  anchor="ra")
        _txt(d, W-24, y+58, f"👥  {pc} / {mx}",     F(13), fill=WHITE,  anchor="ra")
    else:
        _txt(d, 66, y+18, "🔴  OFFLINE",                  F(18, bold=True), fill=RED)
        _txt(d, 66, y+46, "Server hozir javob bermayapti", F(13),            fill=GRAY)

    y += 90

    # Player bar
    if online:
        pc = info.player_count or 0
        mx = info.max_players  or 32
        _rr(d, 20, y, W-20, y+52, r=10, fill=CARD, outline=BORDER)
        _txt(d, 34, y+7,  "OYINCHILAR",    FM(10), fill=GRAY)
        pct_col = GREEN if pc < mx*0.7 else (ORANGE if pc < mx else RED)
        _txt(d, W-34, y+7, f"{pc} / {mx}", F(13, bold=True), fill=pct_col, anchor="ra")
        _bar(d, 34, y+30, W-68, 12, pc, mx)
        y += 62
    else:
        y += 10

    # Oyinchilar ro'yxati
    list_h = rows * 48 + 24
    _rr(d, 20, y, W-20, y+list_h, r=12, fill=CARD, outline=BORDER)
    _txt(d, 36, y+8, "HOZIRGI OYINCHILAR", FM(10), fill=GRAY)
    y += 26

    if players:
        mx_score = max((p.score or 0) for p in players) or 1
        for i, p in enumerate(players):
            ry = y + i * 48
            if i % 2 == 0:
                d.rounded_rectangle([sc(28), sc(ry), sc(W-28), sc(ry+44)],
                                     radius=sc(6), fill=CARD2)
            _txt(d, 46,    ry+14, str(i+1),                     FM(11),           fill=GRAY)
            _txt(d, 64,    ry+10, (p.name.strip() or "—")[:24], F(14, bold=True), fill=WHITE)
            _txt(d, W-270, ry+12, f"💀 {p.score or 0}",         F(13),            fill=RED)
            _txt(d, W-150, ry+12, f"⏱ {_fmt_time(p.duration)}", F(13),            fill=BLUE)
            _bar(d, 64, ry+36, 180, 5, p.score or 0, mx_score, GREEN+"88", GREEN, CARD2, r=2)
        y += rows * 48 + 8
    else:
        _txt(d, W//2, y+18, "😴  Hozir hech kim yo'q", F(14), fill=GRAY, anchor="mm")
        y += 40

    _footer(d, y+16, host, port)
    return _to_bytes(_shrink(img))


# ═══════════════════════════════════════════════
# 2. TOP RASMI
# ═══════════════════════════════════════════════
def make_top_image(result, mode="kills", host="198.163.207.220", port=27015):
    online  = result.get("online", False)
    players = []
    if online:
        all_p   = result.get("players", [])
        players = [p for p in all_p if p.name and p.name.strip()]
        key     = (lambda p: p.score or 0) if mode == "kills" else (lambda p: p.duration or 0)
        players = sorted(players, key=key, reverse=True)

    rows   = max(len(players), 1)
    H      = 88 + rows * 72 + 56
    img, d = _canvas(H)

    title = "💀  TOP — KILL" if mode == "kills" else "⏱  TOP — VAQT"
    _header(d, title, "Hozirgi sessiya natijalari")
    y = 80

    if not online:
        _rr(d, 20, y, W-20, y+56, r=12, fill=CARD, outline=RED, width=2)
        _txt(d, W//2, y+28, "🔴  Server offline", F(15, bold=True), fill=RED, anchor="mm")
    elif not players:
        _rr(d, 20, y, W-20, y+56, r=12, fill=CARD)
        _txt(d, W//2, y+28, "😴  Hozir serverda hech kim yo'q", F(14), fill=GRAY, anchor="mm")
    else:
        mx_val = (players[0].score or 1) if mode == "kills" else (players[0].duration or 1)
        for i, p in enumerate(players):
            ry  = y + i * 72
            val = (p.score or 0) if mode == "kills" else (p.duration or 0)
            pct = val / mx_val if mx_val else 0
            mc  = _medal_col(i)
            bg  = "#16161f" if i % 2 == 0 else CARD

            _rr(d, 20, ry, W-20, ry+66, r=10, fill=bg,
                outline=mc if i < 3 else BORDER, width=2 if i < 3 else 1)

            # Rang chizig'i
            d.rounded_rectangle([sc(20), sc(ry), sc(24), sc(ry+66)],
                                  radius=sc(4), fill=mc)

            m_txt = {0:"🥇",1:"🥈",2:"🥉"}.get(i, str(i+1)+".")
            _txt(d, 36, ry+22, m_txt,                        F(17, bold=True), fill=mc)
            _txt(d, 62, ry+10, (p.name.strip() or "—")[:26], F(16, bold=True), fill=WHITE)

            if mode == "kills":
                main = f"💀  {p.score or 0} kill"
                sec  = f"⏱ {_fmt_time(p.duration)}"
            else:
                main = f"⏱  {_fmt_time(p.duration)}"
                sec  = f"💀 {p.score or 0} kill"

            _txt(d, 62,   ry+36, main,            F(13),  fill=ORANGE if i == 0 else WHITE)
            _txt(d, W-28, ry+10, sec,              F(12),  fill=GRAY2, anchor="ra")
            _txt(d, W-28, ry+36, f"{int(pct*100)}%", FM(12), fill=mc, anchor="ra")
            _bar(d, 62, ry+56, W-100, 7, val, mx_val, mc+"88", mc, CARD2, r=3)

        y += rows * 72

    _footer(d, y+18, host, port)
    return _to_bytes(_shrink(img))


# ═══════════════════════════════════════════════
# 3. SAYT STATISTIKA RASMI
# ═══════════════════════════════════════════════
STAT_MAP = [
    ("Пользователей",       "👤", "Foydalanuvchilar", BLUE),
    ("Всего банов",         "🔒", "Jami banlar",      RED),
    ("Серверов",            "🖥", "Serverlar",        ORANGE),
    ("Привилегированных",   "⭐", "VIP / Adminlar",   GOLD),
    ("Заявок на разбан",    "🔓", "Unban arizalar",   GREEN),
    ("Игроков на серверах", "🎮", "O'yinchilar",      "#9b59b6"),
]

def make_site_stats_image(server_result, site_result, host="198.163.207.220", port=27015):
    H      = 88 + 78 + 3 * 96 + 56
    img, d = _canvas(H)

    _header(d, "📊  ARENACS.UZ STATISTIKA", "Sayt ko'rsatkichlari")
    y = 80

    # Mini server karta
    online = server_result.get("online", False)
    sv_col = GREEN if online else RED
    _rr(d, 20, y, W-20, y+68, r=12, fill=CARD, outline=sv_col, width=2)

    if online:
        info  = server_result["info"]
        pc    = info.player_count or 0
        mx    = info.max_players  or 32
        ping  = round(info.ping * 1000) if info.ping else 0
        p_col = GREEN if ping < 80 else ORANGE
        _txt(d, 36,   y+10, "🟢  SERVER ONLINE",   F(15, bold=True), fill=GREEN)
        _txt(d, 36,   y+36, f"🗺  {info.map_name}", F(12),            fill=GRAY2)
        _txt(d, 260,  y+36, f"📶  {ping} ms",       F(12),            fill=p_col)
        _txt(d, W-28, y+10, f"{pc}/{mx} oyinchi",   F(14, bold=True), fill=ORANGE, anchor="ra")
        _bar(d, 36, y+56, W-72, 8, pc, mx)
    else:
        _txt(d, W//2, y+32, "🔴  SERVER OFFLINE", F(16, bold=True), fill=RED, anchor="mm")

    y += 80

    # Statistika kartalar (2 ustun × 3 qator)
    stats  = site_result.get("stats", {}) if site_result.get("ok") else {}
    col_w  = (W - 52) // 2
    card_h = 88

    for idx, (ru_key, emoji, uz_name, color) in enumerate(STAT_MAP):
        col = idx % 2
        row = idx // 2
        cx  = 20 + col * (col_w + 12)
        cy  = y + row * (card_h + 8)

        _rr(d, cx, cy, cx+col_w, cy+card_h, r=12, fill=CARD, outline=BORDER)
        d.rounded_rectangle([sc(cx), sc(cy+8), sc(cx+4), sc(cy+card_h-8)],
                             radius=sc(3), fill=color)

        _txt(d, cx+14,        cy+14, emoji,    F(22),            fill=color)
        _txt(d, cx+14,        cy+58, uz_name,  F(11),            fill=GRAY2)
        val_txt = stats.get(ru_key, {}).get("value", "—")
        ch_txt  = stats.get(ru_key, {}).get("change", "")
        _txt(d, cx+col_w-10, cy+18, val_txt,  F(22, bold=True), fill=WHITE,  anchor="ra")
        if ch_txt:
            _txt(d, cx+col_w-10, cy+52, ch_txt, F(11),           fill=GREEN, anchor="ra")

    y += 3 * (card_h + 8)
    _footer(d, y+14, host, port)
    return _to_bytes(_shrink(img))
