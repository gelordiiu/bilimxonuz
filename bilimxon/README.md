# 🎓 Bilimxon v2.0 — IT Ta'lim Platformasi

O'zbekistonning #1 AI-powered IT ta'lim platformasi.

---

## 🚀 Serverni Ishga Tushirish

```bash
# 1. Python kutubxonalarini o'rnating
pip install -r requirements.txt

# 2. Serverni ishga tushiring
python server.py

# 3. Brauzerda oching
http://localhost:5000
```

## 🔑 Tizimga Kirish

| Rol     | Login   | Parol             |
|---------|---------|-------------------|
| Admin   | bobur   | bobur_2012admin   |
| Talaba  | student | demo123           |

---

## 📁 Loyiha Tuzilmasi

```
bilimxon/
├── server.py               # Flask backend (asosiy server)
├── bilimxon.db             # SQLite ma'lumotlar bazasi (auto-yaratiladi)
├── requirements.txt        # Python kutubxonalari
│
├── templates/              # HTML sahifalar
│   ├── index.html          # Bosh sahifa
│   ├── login.html          # Kirish/Ro'yxatdan o'tish
│   ├── dashboard.html      # Talaba paneli
│   ├── course.html         # Kurs sahifasi (Bob & Mavzular)
│   ├── lesson.html         # Dars sahifasi (video, matn, kod, test)
│   └── admin.html          # Admin panel
│
├── static/
│   ├── css/style.css       # Asosiy stil (Navy+Gold brend)
│   ├── js/
│   │   ├── i18n.js         # UZ/RU tarjimalar
│   │   └── app.js          # Umumiy funksiyalar
│   └── images/
│       └── logo.png        # Bilimxon logosi
│
├── courses/                # Kurs fayllari (eski tizimdan import)
│   ├── html/lesson1/
│   ├── css/lesson1/
│   └── ...
│
└── assets/
    ├── images/             # Rasm fayllar
    ├── icons/              # Ikonkalar
    ├── videos/             # Yuklangan dars videolari
    └── graphics/           # UI grafikalar
```

---

## 🗂️ Ma'lumotlar Bazasi Tuzilmasi

```
courses (kurslar)
└── bobs (boblar/bo'limlar)
    └── mavzular (darslar/mavzular)
        ├── content_uz/ru   (dars matni - Markdown)
        ├── code_example    (kod misoli)
        ├── video_url       (video manzili)
        └── quiz_questions  (test savollari)
```

---

## ⚙️ Admin Panel — Qo'llanma

### 1. Kurs Qo'shish
`Admin Panel → Kurslar → "+ Kurs Qo'shish"`

### 2. Bob (Bo'lim) Qo'shish
`Admin Panel → Bob & Mavzular → [Kurs] → "+ Bob"`

### 3. Mavzu (Dars) Qo'shish
`Admin Panel → Bob & Mavzular → [Bob] → "+ Mavzu"`
- Uzbekcha/Ruscha matn
- Markdown formatida yozish mumkin
- Kod misoli qo'shish

### 4. Video Yuklash
`Admin Panel → Bob & Mavzular → [Mavzu] → 🎬`
- Format: MP4, WebM, OGG, MOV
- Hajm: maksimum 500MB

### 5. Test/Quiz Qo'shish
`Admin Panel → Bob & Mavzular → [Mavzu] → 📝`
- Har bir savol uchun 4 ta variant
- To'g'ri javobni belgilash
- Uzbekcha va Ruscha versiya

---

## 🌐 Til Sozlamalari

- **UZ** (Uzbek) — standart til
- **RU** (Rus tili) — alohida til

Har qanday sahifada yuqori o'ng burchakdagi `UZ | RU` tugmalari orqali til almashtiriladi.

---

## 📊 Statistika (Admin)

- Jami foydalanuvchilar soni
- Jami kurslar va mavzular
- Sahifa ko'rishlar soni
- Bajarilgan darslar soni
- Kurs omilligi grafigi
- Kunlik faollik grafigi

---

## 🔌 API Endpointlar

### Ommaviy API
| Endpoint | Metod | Tavsif |
|----------|-------|--------|
| `/api/courses` | GET | Barcha kurslar |
| `/api/course/<slug>` | GET | Kurs tafsilotlari |
| `/api/lesson/<id>` | GET | Mavzu tafsilotlari |
| `/api/lesson/<id>/quiz` | GET | Test savollari |
| `/api/progress/complete` | POST | Darsni tugatish |

### Admin API (admin login kerak)
| Endpoint | Metod | Tavsif |
|----------|-------|--------|
| `/api/admin/stats` | GET | Statistika |
| `/api/admin/courses` | GET/POST | Kurslar |
| `/api/admin/courses/<slug>` | PUT/DELETE | Kurs tahrirlash |
| `/api/admin/bobs/<slug>` | GET | Bob ro'yxati |
| `/api/admin/bobs` | POST | Bob qo'shish |
| `/api/admin/bobs/<id>` | PUT/DELETE | Bob tahrirlash |
| `/api/admin/mavzular/<bob_id>` | GET | Mavzu ro'yxati |
| `/api/admin/mavzular` | POST | Mavzu qo'shish |
| `/api/admin/mavzular/<id>` | PUT/DELETE | Mavzu tahrirlash |
| `/api/admin/quiz/<mavzu_id>` | GET | Test savollari |
| `/api/admin/quiz` | POST | Savol qo'shish |
| `/api/admin/quiz/<id>` | PUT/DELETE | Savol tahrirlash |
| `/api/admin/upload-video/<id>` | POST | Video yuklash |

---

## 💡 Muhim Eslatmalar

- Barcha o'zgarishlar SQLite bazasida saqlanadi (`bilimxon.db`)
- Video fayllar `assets/videos/` papkasiga saqlanadi
- Parollar SHA-256 bilan shifrlangan
- Sessiya xavfsiz saqlanadi

---

© 2025 Bilimxon — Barcha huquqlar himoyalangan.
