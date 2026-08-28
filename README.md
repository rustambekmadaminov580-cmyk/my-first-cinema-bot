# 🎬 Kino Bot (Telegram)

aiogram 3.x va SQLite asosida qurilgan Telegram Kino Bot. Foydalanuvchilar kino ID
raqamini yuborib kino olishadi, admin esa maxsus panel orqali kinolarni
yuklaydi, ko'radi, qidiradi va o'chiradi.

## 📁 Loyiha strukturasi

```
kino_bot/
│
├── bot.py              # Botni ishga tushiruvchi asosiy fayl
├── config.py            # .env dan sozlamalarni o'qiydi
├── database.py           # SQLite bilan ishlash funksiyalari
├── states.py             # FSM holatlari
├── keyboards.py           # Reply va inline klaviaturalar
├── handlers/
│   ├── __init__.py
│   ├── user.py           # Oddiy foydalanuvchi handlerlari
│   └── admin.py           # Admin panel handlerlari
├── .env                 # Maxfiy sozlamalar (git'ga qo'shilmasin!)
├── .env.example           # .env namunasi
├── requirements.txt        # Kerakli kutubxonalar
└── README.md
```

## 🖥 Windows'da noldan ishga tushirish

### 1. Python o'rnatish

1. [python.org/downloads](https://www.python.org/downloads/) saytiga kiring.
2. Python 3.11 yoki undan yuqori versiyani yuklab oling.
3. O'rnatish jarayonida **"Add Python to PATH"** katakchasini albatta belgilang.
4. O'rnatilganini tekshirish uchun Command Prompt (CMD) oching va yozing:
   ```
   python --version
   ```
   Python versiyasi chiqishi kerak.

### 2. Loyiha papkasiga o'tish

Loyiha fayllarini bir papkaga joylashtiring (masalan, `C:\kino_bot`), so'ng
CMD orqali o'sha papkaga o'ting:

```
cd C:\kino_bot
```

### 3. Virtual environment (virtual muhit) yaratish

```
python -m venv venv
```

Virtual muhitni faollashtirish:

```
venv\Scripts\activate
```

Faollashgandan so'ng qator boshida `(venv)` yozuvi paydo bo'ladi.

### 4. Kerakli kutubxonalarni o'rnatish

```
pip install -r requirements.txt
```

### 5. `.env` faylini yaratish

`.env.example` faylidan nusxa oling va nomini `.env` deb o'zgartiring
(loyihada tayyor `.env` fayli allaqachon mavjud — faqat qiymatlarni
o'zingiznikiga almashtiring).

### 6. BotFather'dan token olish

1. Telegram'da [@BotFather](https://t.me/BotFather) botini toping.
2. `/newbot` buyrug'ini yuboring.
3. Bot uchun nom va username bering (username `bot` bilan tugashi kerak,
   masalan `mening_kino_bot`).
4. BotFather sizga token beradi, masalan:
   ```
   123456789:AAExampleTokenHereReplaceWithReal
   ```

### 7. `BOT_TOKEN` yozish

`.env` faylini biror matn muharriri (Notepad, VS Code) bilan oching va
`BOT_TOKEN` qatoriga BotFather'dan olgan tokeningizni yozing:

```
BOT_TOKEN=123456789:AAExampleTokenHereReplaceWithReal
```

### 8. `ADMIN_ID` yozish

O'zingizning Telegram ID raqamingizni bilish uchun Telegram'da
[@userinfobot](https://t.me/userinfobot) botiga `/start` yuboring — u sizga
ID raqamingizni ko'rsatadi. Shu raqamni `.env` fayliga yozing:

```
ADMIN_ID=123456789
```

### 9. `ADMIN_PASSWORD` yozish

Admin panelga kirish uchun o'zingiz xohlagan parolni tanlang va yozing:

```
ADMIN_PASSWORD=mening_maxfiy_parolim
```

### 10. Botni ishga tushirish

```
python bot.py
```

Agar hammasi to'g'ri sozlangan bo'lsa, terminalda quyidagiga o'xshash
xabar chiqadi:

```
Baza tayyor.
Bot ishga tushmoqda...
```

Bot shu paytdan boshlab ishlay boshlaydi. To'xtatish uchun `Ctrl+C` bosing.

---

## ✅ Botni test qilish

1. Telegram'da o'z botingizni oching va `/start` yuboring — salomlashuv
   xabari chiqishi kerak.
2. O'zingizning (admin) akkountingizdan `/admin` yuboring.
3. `.env` faylida ko'rsatgan parolni kiriting.
4. Admin panel klaviaturasi chiqadi. **🎬 Kino yuklash** tugmasini bosing.
5. Istalgan video faylni yuboring.
6. Kino nomini kiriting, masalan: `Interstellar`.
7. Kino ID sifatida raqam kiriting, masalan: `125`.
8. Bot "✅ Kino muvaffaqiyatli saqlandi!" deb javob beradi.
9. Endi **boshqa** Telegram akkountdan (yoki oddiy foydalanuvchi sifatida)
   botga `125` deb yozing — bot sizga saqlangan videoni qaytarib yuboradi.

## ⚙️ Texnik eslatmalar

- Videolar Telegram serverida saqlanadi — bot faqat `file_id` ni bazada
  saqlaydi, shu sababli katta hajmdagi videolar bilan ham muammosiz ishlaydi.
- Admin sessiyasi xotirada saqlanadi — bot qayta ishga tushirilsa, admin
  yana parol kiritishi kerak bo'ladi (xavfsizlik uchun).
- `.env` faylini hech qachon ochiq joyga (GitHub'ga public repo sifatida)
  yuklamang — u maxfiy ma'lumotlarni saqlaydi.
