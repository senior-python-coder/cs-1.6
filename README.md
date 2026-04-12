# 🎮 CS 1.6 Server Status Bot

> Telegram bot — Counter-Strike 1.6 server holatini real-time kuzatish uchun

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.3-green?style=flat-square)
![python-a2s](https://img.shields.io/badge/python--a2s-1.3.0-orange?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square)

---

## 📸 Ko'rinishi

```
🟢 SERVER ONLINE

🖥 My CS 1.6 Server
🌐 IP: 198.163.207.220:27015
🗺 Xarita: de_dust2
📶 Ping: 42 ms

👥 Oyinchilar: 8 / 20
[████████░░]

📋 Oyinchilar:
  1. 🎮 ProPlayer  💀 24  ⏱ 15m 30s
  2. 🎮 xXnoobXx   💀 12  ⏱ 8m 5s
  3. 🎮 cs_legend  💀 8   ⏱ 3m 22s
```

```
💀 TOP — ENG KO'P KILL
198.163.207.220:27015  👥 8 oyinchi
────────────────────────

🥇 ProPlayer
    ★★★★★  💀 48 kill  ⏱ 42m 10s

🥈 xXnoobXx
    ★★★☆☆  💀 24 kill  ⏱ 1h 5m

🥉 cs_legend
    ★★☆☆☆  💀 12 kill  ⏱ 15m 3s
```

---

## ✨ Imkoniyatlar

- 🟢 Server **online / offline** holati
- 👥 Real-time **oyinchilar ro'yxati** (ism, kill, vaqt)
- 💀 **TOP — eng ko'p kill** qilganlar
- ⏱ **TOP — eng ko'p vaqt** o'ynaganlar
- ★ **Yulduzli reyting** (1-o'ringa nisbatan)
- 🔄 **Yangilash tugmasi** — xabarni o'chirib yozmasdan yangilaydi
- 💬 Guruhda **`Online`** deb yozilsa avtomatik javob beradi
- 🥇🥈🥉 Medal tizimi (birinchi uchlikka)

---

## 🛠 O'rnatish

### 1. Repozitoriyani klonlash

```bash
git clone https://github.com/username/cs16-status-bot.git
cd cs16-status-bot
```

### 2. Virtual muhit (tavsiya etiladi)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Paketlarni o'rnatish

```bash
pip install -r requirements.txt
```

---

## ⚙️ Sozlash

`cs16bot.py` faylini oching va quyidagi qatorlarni o'zgartiring:

```python
TOKEN   = "SIZNING_BOT_TOKENINGIZ"   # @BotFather dan olinadi
CS_HOST = "198.163.207.220"           # CS 1.6 server IP
CS_PORT = 27015                       # CS 1.6 server port
```

### Bot tokeni olish

1. Telegramda [@BotFather](https://t.me/BotFather) ga o'ting
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting
4. Olingan tokenni `TOKEN` ga qo'ying

---

## ▶️ Ishga tushirish

```bash
python cs16bot.py
```

Muvaffaqiyatli ishga tushganda:

```
🎮 CS 1.6 Status Bot ishga tushdi!
📡 Server: 198.163.207.220:27015
```

---

## 📌 Buyruqlar

| Buyruq / Xabar | Tavsif |
|---|---|
| `/start` | Botni boshlash, buyruqlar ro'yxati |
| `/status` | Server holati va oyinchilar |
| `/top` | TOP o'yinchilar (kill bo'yicha) |
| `/help` | Yordam |
| `Online` | Server holatini ko'rish (guruhda ham ishlaydi) |

---

## 🕹 Inline tugmalar

**Server holati xabarida:**

| Tugma | Vazifa |
|---|---|
| 🔄 Yangilash | Server ma'lumotlarini yangilash |
| 📊 TOP list | Kill bo'yicha TOP ro'yxatini ochish |

**TOP list xabarida:**

| Tugma | Vazifa |
|---|---|
| ⏱ Vaqt bo'yicha | Eng ko'p vaqt o'ynaganlar |
| 💀 Kill bo'yicha | Eng ko'p kill qilganlar |
| 🔄 Yangilash | TOPni yangilash |
| 🔙 Server | Server holatiga qaytish |

---

## 📁 Fayl tuzilmasi

```
cs16-status-bot/
├── cs16bot.py          # Asosiy bot kodi
├── requirements.txt    # Python paketlari
└── README.md           # Hujjat
```

---

## 📦 Talablar

```
python-telegram-bot==21.3
python-a2s==1.3.0
```

| Dastur | Minimal versiya |
|---|---|
| Python | 3.10+ |
| python-telegram-bot | 21.3 |
| python-a2s | 1.3.0 |

---

## 🔁 Fonda ishlatish (Linux)

Agar server Linux'da bo'lsa, bot doim ishlashi uchun:

```bash
# screen orqali
screen -S cs16bot
python cs16bot.py
# Ctrl+A, D — chiqish (bot ishlayveradi)

# yoki systemd service sifatida
```

**systemd service fayli** (`/etc/systemd/system/cs16bot.service`):

```ini
[Unit]
Description=CS 1.6 Telegram Status Bot
After=network.target

[Service]
WorkingDirectory=/home/user/cs16-status-bot
ExecStart=/home/user/cs16-status-bot/venv/bin/python cs16bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cs16bot
sudo systemctl start cs16bot
sudo systemctl status cs16bot
```

---

## ⚠️ Muhim eslatmalar

- Bot bir vaqtda **faqat bitta nusxada** ishlashi kerak. Aks holda `409 Conflict` xatosi chiqadi.
- Agar xato chiqsa, barcha python processlarini to'xtatib qayta ishga tushiring:
  ```bash
  # Windows
  taskkill /F /IM python.exe

  # Linux
  pkill -f cs16bot.py
  ```
- CS 1.6 server **Valve A2S protokoli**ni qo'llab-quvvatlashi kerak (standart holda qo'llab-quvvatlanadi).

---

## 📜 Litsenziya

MIT License — xohlagan maqsadda erkin foydalaning.

---

<div align="center">
  Made with ❤️ for CS 1.6 community
</div>
