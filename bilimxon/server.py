"""
Bilimxon v3.0 — Social Learning Platform
Full-featured: Profiles, Friends, Chat, Store, Groups, Titles, Ticks
"""
from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory
import sqlite3, hashlib, json, os, shutil, random, string, urllib.request
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'bilimxon_v3_ultra_secret_2025'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 days

@app.after_request
def add_security_headers(resp):
    # Prevent caching of HTML pages (makes source harder to access)
    if 'text/html' in resp.content_type:
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return resp
from datetime import timedelta

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(BASE_DIR, 'bilimxon.db')
COURSES_DIR = os.path.join(BASE_DIR, 'courses')
ASSETS_DIR  = os.path.join(BASE_DIR, 'assets')
UPLOAD_VIDEO_DIR  = os.path.join(ASSETS_DIR, 'videos')
UPLOAD_AVATAR_DIR = os.path.join(ASSETS_DIR, 'avatars')
UPLOAD_BANNER_DIR = os.path.join(ASSETS_DIR, 'banners')
UPLOAD_STORE_DIR  = os.path.join(ASSETS_DIR, 'store')
UPLOAD_GROUP_DIR  = os.path.join(ASSETS_DIR, 'group_media')
GAMES_DIR         = os.path.join(BASE_DIR, 'games')
GAMES_THUMB_DIR   = os.path.join(GAMES_DIR, 'thumbnails')

for d in [UPLOAD_VIDEO_DIR, UPLOAD_AVATAR_DIR, UPLOAD_BANNER_DIR, UPLOAD_STORE_DIR, UPLOAD_GROUP_DIR, GAMES_DIR, GAMES_THUMB_DIR]:
    os.makedirs(d, exist_ok=True)

ALLOWED_GAME = {'zip', 'html'}
GAME_MAX_SIZE         = 50  * 1024 * 1024   # 50 MB  (free)
GAME_MAX_SIZE_PREMIUM = 100 * 1024 * 1024   # 100 MB (premium)

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

ALLOWED_IMG   = {'png','jpg','jpeg','gif','webp'}
ALLOWED_VIDEO = {'mp4','webm','ogg','mov'}

# ─────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────
def get_db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    conn = get_db(); cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        full_name TEXT, email TEXT, role TEXT DEFAULT 'student',
        bio TEXT DEFAULT '', avatar TEXT DEFAULT '', banner TEXT DEFAULT '',
        points INTEGER DEFAULT 0, lang TEXT DEFAULT 'uz',
        yt_link TEXT DEFAULT '', ig_link TEXT DEFAULT '',
        tg_link TEXT DEFAULT '', gh_link TEXT DEFAULT '',
        yt_followers INTEGER DEFAULT 0, ig_followers INTEGER DEFAULT 0,
        has_tick INTEGER DEFAULT 0,
        active_title TEXT DEFAULT '',
        active_frame TEXT DEFAULT '',
        profile_color TEXT DEFAULT '#1B2A4A',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL, title_uz TEXT NOT NULL, title_ru TEXT NOT NULL,
        desc_uz TEXT, desc_ru TEXT, icon TEXT DEFAULT '📚', color TEXT DEFAULT '#1B2A4A',
        level_uz TEXT DEFAULT 'Boshlangich', level_ru TEXT DEFAULT 'Начальный',
        duration TEXT DEFAULT '10 soat', category_uz TEXT DEFAULT 'Dasturlash',
        category_ru TEXT DEFAULT 'Программирование', sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS bobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, course_slug TEXT NOT NULL,
        title_uz TEXT NOT NULL, title_ru TEXT, sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS mavzular (
        id INTEGER PRIMARY KEY AUTOINCREMENT, bob_id INTEGER NOT NULL,
        course_slug TEXT NOT NULL, title_uz TEXT NOT NULL, title_ru TEXT,
        content_uz TEXT, content_ru TEXT, code_example TEXT, video_url TEXT,
        sort_order INTEGER DEFAULT 0, points_reward INTEGER DEFAULT 10,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, mavzu_id INTEGER NOT NULL,
        question_uz TEXT NOT NULL, question_ru TEXT,
        options_uz TEXT NOT NULL, options_ru TEXT,
        correct_idx INTEGER NOT NULL, explanation_uz TEXT, explanation_ru TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        mavzu_id INTEGER NOT NULL, course_slug TEXT NOT NULL,
        completed INTEGER DEFAULT 0, quiz_score INTEGER DEFAULT -1,
        code_submitted INTEGER DEFAULT 0,
        completed_at TEXT, UNIQUE(user_id, mavzu_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        event_type TEXT, ref_id INTEGER, ref_slug TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # ── SOCIAL ──
    cur.execute('''CREATE TABLE IF NOT EXISTS friend_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id INTEGER NOT NULL, to_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(from_id, to_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id INTEGER NOT NULL, user2_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user1_id, user2_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_id INTEGER NOT NULL, to_id INTEGER NOT NULL,
        content TEXT NOT NULL, msg_type TEXT DEFAULT 'text',
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # ── TITLES ──
    cur.execute('''CREATE TABLE IF NOT EXISTS titles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL, label_uz TEXT, label_ru TEXT,
        icon TEXT DEFAULT '🏆', color TEXT DEFAULT '#gold',
        is_special INTEGER DEFAULT 0, description TEXT DEFAULT ''
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS user_titles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, title_key TEXT NOT NULL,
        granted_by INTEGER, granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, title_key)
    )''')

    # ── STORE ──
    cur.execute('''CREATE TABLE IF NOT EXISTS store_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_uz TEXT NOT NULL, name_ru TEXT,
        desc_uz TEXT, desc_ru TEXT,
        item_type TEXT DEFAULT 'cosmetic',
        price_points INTEGER DEFAULT 100,
        image TEXT DEFAULT '', rarity TEXT DEFAULT 'common',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS user_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, item_id INTEGER NOT NULL,
        purchased_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, item_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS mystery_boxes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_uz TEXT NOT NULL, name_ru TEXT,
        price_points INTEGER DEFAULT 200,
        possible_rewards TEXT DEFAULT '[]',
        image TEXT DEFAULT '', rarity TEXT DEFAULT 'common',
        is_active INTEGER DEFAULT 1
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS box_openings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, box_id INTEGER NOT NULL,
        reward_item_id INTEGER, reward_points INTEGER DEFAULT 0,
        opened_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # ── GROUPS / CHANNELS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, slug TEXT UNIQUE NOT NULL,
        description TEXT DEFAULT '', group_type TEXT DEFAULT 'group',
        owner_id INTEGER NOT NULL,
        avatar TEXT DEFAULT '', banner TEXT DEFAULT '',
        bio TEXT DEFAULT '', is_public INTEGER DEFAULT 1,
        member_count INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        role TEXT DEFAULT 'member',
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(group_id, user_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS group_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        content TEXT NOT NULL, msg_type TEXT DEFAULT 'text',
        media_url TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # ── POINT TRANSACTIONS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS point_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, delta INTEGER NOT NULL,
        reason TEXT, ref_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # ── Seed admin ──
    admin_pass = hashlib.sha256('bobur_2012admin'.encode()).hexdigest()
    cur.execute('''INSERT OR IGNORE INTO users
        (username,password,full_name,email,role,has_tick,active_title,bio,points)
        VALUES (?,?,?,?,?,?,?,?,?)''',
        ('bobur', admin_pass, 'Bobur Alijonov', 'admin@bilimxon.uz',
         'admin', 1, 'bilimxon_creator',
         "Bilimxon platformasining yaratuvchisi 🚀", 99999))

    demo_pass = hashlib.sha256('demo123'.encode()).hexdigest()
    cur.execute('''INSERT OR IGNORE INTO users
        (username,password,full_name,email,role,bio,points)
        VALUES (?,?,?,?,?,?,?)''',
        ('student','demo123_hashed','Demo Talaba','student@bilimxon.uz',
         'student',"Men Bilimxon'da o'qiyapman!", 150))

    # ── Seed titles ──
    titles_seed = [
        ('bilimxon_creator','Bilimxon Yaratuvchisi','Создатель Bilimxon','👑','#FFD700',1,"Platforma yaratuvchisiga berilgan maxsus unvon"),
        ('admin_title','ADMIN','ADMIN','🛡️','#EF4444',1,"Platforma administratori"),
        ('premium_user','Premium Foydalanuvchi','Premium Пользователь','💎','#a855f7',1,"Premium obuna sotib olgan foydalanuvchi"),
        ('top_student','Eng Zor O\'quvchi','Лучший Ученик','🏆','#C9A84C',0,"Eng yuqori ball to'plagan o'quvchi"),
        ('senior','Senior','Senior','💎','#3B82F6',0,"Senior darajadagi dasturchi"),
        ('junior','Junior','Junior','🌱','#22C55E',0,"Junior darajadagi dasturchi"),
        ('popular','Mashhur','Популярный','⭐','#F59E0B',0,"Ko'p odamlar tomonidan kuzatilgan"),
        ('rich','Boy','Богатый','💰','#10B981',0,"Juda ko'p ochko to'plagan"),
        ('verified','Tasdiqlangan','Верифицированный','✅','#6366F1',0,"Tasdiqlangan foydalanuvchi"),
        ('speedrunner','Tezkor','Спидраннер','⚡','#EF4444',0,"Kurslarni tez tugatgan"),
        ('scholar','Olim','Учёный','📚','#8B5CF6',0,"Barcha kurslarni tugatgan"),
    ]
    for t in titles_seed:
        cur.execute('''INSERT OR IGNORE INTO titles
            (key,label_uz,label_ru,icon,color,is_special,description)
            VALUES (?,?,?,?,?,?,?)''', t)

    # Grant creator title to bobur
    cur.execute('''INSERT OR IGNORE INTO user_titles (user_id, title_key, granted_by)
        SELECT u.id, 'bilimxon_creator', u.id FROM users u WHERE u.username='bobur' ''')

    # ── Extra admin accounts ──
    extra_admins = [
        ('fuzayl', '022e7b1c92b74550dc8082b4334749253165534f2ba6b30cfc34456b1ec563e7', 'Fuzayl', 'fuzayl@bilimxon.uz'),
        ('shams',  'fad57d9a43d16462ae878483fb3e5f4a5c4e95b16c649bb8cb4d4fe795bd8c00', 'Shams',  'shams@bilimxon.uz'),
        ('adobe',  'ee2ac31885b759ad2a96bbd56a1ab6b5367bccae445aa920bfc0fac41fedd042', 'Adobe',  'adobe@bilimxon.uz'),
    ]
    for uname, pwd, fname, email in extra_admins:
        cur.execute('''INSERT OR IGNORE INTO users
            (username,password,full_name,email,role,has_tick,active_title,bio,points)
            VALUES (?,?,?,?,?,?,?,?,?)''',
            (uname, pwd, fname, email, 'admin', 1, 'admin_title', 'Bilimxon Administratori 🛡️', 5000))
        cur.execute('''INSERT OR IGNORE INTO user_titles (user_id, title_key, granted_by)
            SELECT u.id, 'admin_title', u.id FROM users u WHERE u.username=?''', (uname,))
        cur.execute('''INSERT OR IGNORE INTO user_titles (user_id, title_key, granted_by)
            SELECT u.id, 'verified', u.id FROM users u WHERE u.username=?''', (uname,))

    # ── Add missing columns (must be before seed) ──
    def add_col(table, col, coldef):
        try: cur.execute(f'ALTER TABLE {table} ADD COLUMN {col} {coldef}')
        except: pass
    add_col('users', 'yt_followers', 'INTEGER DEFAULT 0')
    add_col('users', 'ig_followers', 'INTEGER DEFAULT 0')
    add_col('users', 'active_frame', "TEXT DEFAULT ''")
    add_col('users', 'profile_color', "TEXT DEFAULT '#1B2A4A'")
    add_col('users', 'profile_style', "TEXT DEFAULT ''")
    add_col('users', 'premium_until', "TEXT DEFAULT ''")
    add_col('users', 'is_premium', "INTEGER DEFAULT 0")
    add_col('users', 'ai_unlocked_until', "TEXT DEFAULT ''")
    add_col('groups', 'bio', "TEXT DEFAULT ''")
    add_col('groups', 'is_public', 'INTEGER DEFAULT 1')
    add_col('groups', 'member_count', 'INTEGER DEFAULT 1')
    add_col('store_items', 'rarity', "TEXT DEFAULT 'common'")
    add_col('store_items', 'item_type', "TEXT DEFAULT 'cosmetic'")
    add_col('store_items', 'price_usd', "REAL DEFAULT 0")
    add_col('store_items', 'is_paid', "INTEGER DEFAULT 0")
    add_col('mystery_boxes', 'rarity', "TEXT DEFAULT 'common'")
    add_col('games', 'reject_reason', "TEXT DEFAULT ''")
    add_col('tournament_teams', 'is_private', 'INTEGER DEFAULT 0')
    add_col('tournament_teams', 'join_code', "TEXT DEFAULT ''")
    add_col('tournament_teams', 'owner_id', 'INTEGER DEFAULT 0')
    # Tournament questions new schema migration
    try:
        cur.execute("SELECT question_text FROM tournament_questions LIMIT 1")
    except Exception:
        # Old schema - drop and recreate
        try:
            cur.execute("DROP TABLE IF EXISTS tournament_questions")
            cur.execute("DROP TABLE IF EXISTS tournament_answers")
            cur.execute('''CREATE TABLE IF NOT EXISTS tournament_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT DEFAULT \'\'\', option_b TEXT DEFAULT \'\',
                option_c TEXT DEFAULT \'\'\', option_d TEXT DEFAULT \'\',
                correct_option TEXT DEFAULT \'A\',
                points INTEGER DEFAULT 10, time_limit INTEGER DEFAULT 30, order_num INTEGER DEFAULT 0
            )''')
            cur.execute('''CREATE TABLE IF NOT EXISTS tournament_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL, tournament_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL, team_id INTEGER NOT NULL,
                selected_option TEXT DEFAULT \'\', is_correct INTEGER DEFAULT 0,
                points_earned INTEGER DEFAULT 0,
                answered_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(question_id, user_id)
            )''')
        except Exception as em:
            print("Migration tournament_questions:", em)
    add_col('tournaments', 'entry_fee', 'INTEGER DEFAULT 0')
    add_col('notifications', 'sender_id', "INTEGER DEFAULT 0")
    add_col('groups', 'avatar', "TEXT DEFAULT ''")
    add_col('users', 'streak_days', 'INTEGER DEFAULT 0')
    add_col('users', 'last_activity_date', "TEXT DEFAULT ''")
    add_col('users', 'longest_streak', 'INTEGER DEFAULT 0')
    add_col('tournament_teams', 'owner_id', 'INTEGER DEFAULT 0')
    add_col('tournaments', 'entry_fee', 'INTEGER DEFAULT 0')
    add_col('tournaments', 'is_public', 'INTEGER DEFAULT 1')
    try:
        conn.execute('DELETE FROM store_items WHERE id NOT IN (SELECT MIN(id) FROM store_items GROUP BY name_uz)')
        conn.commit()
    except: pass
    # New tables for tournaments, streaks, certificates, payments
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS tournaments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, description TEXT DEFAULT '',
        start_date TEXT DEFAULT '', end_date TEXT DEFAULT '',
        status TEXT DEFAULT 'upcoming', prize_points INTEGER DEFAULT 500,
        entry_fee INTEGER DEFAULT 0, is_public INTEGER DEFAULT 1,
        created_by INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS tournament_teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL, name TEXT NOT NULL,
        color TEXT DEFAULT '#1B2A4A', total_points INTEGER DEFAULT 0,
        is_private INTEGER DEFAULT 0, join_code TEXT DEFAULT '',
        owner_id INTEGER DEFAULT 0, member_limit INTEGER DEFAULT 0
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS tournament_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL, team_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL, points_earned INTEGER DEFAULT 0,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(tournament_id, user_id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS tournament_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tournament_id INTEGER NOT NULL,
        question_text TEXT NOT NULL,
        option_a TEXT DEFAULT '', option_b TEXT DEFAULT '',
        option_c TEXT DEFAULT '', option_d TEXT DEFAULT '',
        correct_option TEXT DEFAULT 'A',
        points INTEGER DEFAULT 10,
        time_limit INTEGER DEFAULT 30,
        order_num INTEGER DEFAULT 0
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS tournament_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        tournament_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        selected_option TEXT DEFAULT '',
        is_correct INTEGER DEFAULT 0,
        points_earned INTEGER DEFAULT 0,
        answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(question_id, user_id)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS streak_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, activity_date TEXT NOT NULL,
        UNIQUE(user_id, activity_date)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, course_slug TEXT NOT NULL,
        issued_at TEXT DEFAULT CURRENT_TIMESTAMP, cert_code TEXT UNIQUE NOT NULL,
        UNIQUE(user_id, course_slug)
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, amount INTEGER NOT NULL,
        currency TEXT DEFAULT 'UZS', purpose TEXT NOT NULL,
        status TEXT DEFAULT 'pending', provider TEXT DEFAULT 'payme',
        transaction_id TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        paid_at TEXT DEFAULT ''
    )''')
    conn.commit()

    # ── Seed store items ──
    store_seed = [
        # Premium SOM narxlari (admin o'zgartira oladi)
        ('Premium 1 kun', 'Premium 1 день', '1 kunlik Premium — barcha imtiyozlar', '1 день Premium — все привилегии', 'premium', 0, '👑', 'legendary', 5000, 1),
        ('Premium 7 kun', 'Premium 7 дней', '7 kunlik Premium — haftalik rejim', '7 дней Premium — недельный режим', 'premium', 0, '💎', 'legendary', 20000, 1),
        ('Premium 30 kun', 'Premium 30 дней', '30 kunlik Premium — oylik rejim', '30 дней Premium — месячный режим', 'premium', 0, '🏆', 'legendary', 50000, 1),
        # Unvonlar
        ("Tasdiqlangan Belgi", "Галочка верификации", "Profilingizga ✓ galochka qo'shish", "Добавить ✓ галочку к профилю", 'cosmetic', 1000, '✓', 'legendary', 0, 0),
        ('Junior Unvon', 'Звание Junior', 'Junior unvonini oling', 'Получить звание Junior', 'title', 200, '🌱', 'uncommon', 0, 0),
        ('Senior Unvon', 'Звание Senior', 'Senior unvonini oling', 'Получить звание Senior', 'title', 500, '⚡', 'epic', 0, 0),
        ('Master Unvon', 'Звание Master', 'Master darajasiga yeting', 'Достичь уровня Master', 'title', 1000, '🔮', 'legendary', 0, 0),
        ('Pro Dasturchi', 'Pro Программист', 'Pro Dasturchi unvoni', 'Звание Pro Programmer', 'title', 750, '💻', 'epic', 0, 0),
        # Boostlar
        ('XP x2 (24h)', 'XP x2 (24ч)', '24 soat davomida 2x XP', '2x XP в течение 24 часов', 'boost', 150, '⚡', 'rare', 0, 0),
        ('XP x3 (6h)', 'XP x3 (6ч)', '6 soat davomida 3x XP', '3x XP в течение 6 часов', 'boost', 100, '🚀', 'epic', 0, 0),
        ('XP x2 (72h)', 'XP x2 (72ч)', '3 kun davomida 2x XP', '2x XP в течение 3 дней', 'boost', 350, '🌟', 'legendary', 0, 0),
        ('Ball +500', 'Очки +500', "Hisobingizga 500 ball qo'shish", 'Добавить 500 очков', 'boost', 0, '💰', 'rare', 2500, 1),
        ('Ball +1000', 'Очки +1000', "Hisobingizga 1000 ball qo'shish", 'Добавить 1000 очков', 'boost', 0, '💎', 'epic', 4500, 1),
        # Profil stillari
        ('Qizil Profil Stili', 'Красный Стиль', 'Profilingiz qizil rangga boyaladi', 'Красный цвет профиля', 'cosmetic', 120, '🎨', 'rare', 0, 0),
        ('Binafsha Profil Stili', 'Фиолетовый Стиль', 'Epik binafsha rang profil', 'Эпический фиолетовый', 'cosmetic', 180, '🎨', 'epic', 0, 0),
        ('Oltin Profil Stili', 'Золотой Стиль', 'Afsonaviy oltin rang profil', 'Легендарный золотой', 'cosmetic', 300, '🎨', 'legendary', 0, 0),
        ('Gradient Profil', 'Градиент', "Ko'k-binafsha gradient stil", 'Сине-фиолетовый градиент', 'cosmetic', 250, '🌈', 'epic', 0, 0),
        ('Neon Yashil', 'Неон Зелёный', 'Neon yashil profil stili', 'Неоновый зелёный профиль', 'cosmetic', 200, '💚', 'rare', 0, 0),
        ("Ko'k Neon", 'Синий Неон', "Ko'k neon profil effekti", 'Синий неоновый эффект', 'cosmetic', 220, '💙', 'rare', 0, 0),
        ('Qora Titanium', 'Чёрный Титан', 'Qora titanium premium stil', 'Чёрный титановый стиль', 'cosmetic', 400, '🖤', 'legendary', 0, 0),
        # Ramkalar
        ('Oltin Ramka', 'Золотая Рамка', 'Avatar atrofiga oltin ramka', 'Золотая рамка вокруг аватара', 'frame', 350, '🖼️', 'legendary', 0, 0),
        ('Neon Ramka', 'Неоновая Рамка', 'Neon effektli ramka', 'Рамка с неоновым эффектом', 'frame', 200, '✨', 'epic', 0, 0),
        ('Animatsiyali Ramka', 'Анимированная Рамка', 'Aylanuvchi animatsiyali ramka', 'Вращающаяся рамка', 'frame', 500, '🌟', 'legendary', 0, 0),
        # Effektlar
        ('Confetti Effekt', 'Конфетти', 'Profil ochinishida confetti', 'Конфетти при открытии профиля', 'effect', 180, '🎊', 'rare', 0, 0),
        ('Yulduz Effekt', 'Звёздный эффект', 'Yulduzlar uchib yuradi', 'Летящие звёзды в профиле', 'effect', 280, '⭐', 'epic', 0, 0),
        # Paketlar
        ('Maxsus Emoji Pack', 'Спец. Эмодзи', '50 ta maxsus emoji paketi', 'Пак из 50 специальных эмодзи', 'cosmetic', 100, '😎', 'uncommon', 0, 0),
        ('VIP Sticker Pack', 'VIP Стикеры', "VIP sticker to'plami", 'VIP стикеры для чатов', 'cosmetic', 300, '🎭', 'epic', 0, 0),
        # Maxsus
        ('AI Yordamchi (7 kun)', 'ИИ Помощник (7 дней)', '7 kunlik BilimxonAI kirish', '7 дней доступа к BilimxonAI', 'premium', 600, '🤖', 'epic', 0, 0),
        ('Maxfiy Nom', 'Секретный Ник', 'Profilida maxfiy nom', 'Отображать секретный ник', 'cosmetic', 150, '🎭', 'uncommon', 0, 0),
    ]
    # Deduplicate store items first
    cur.execute("""DELETE FROM store_items WHERE id NOT IN (
        SELECT MIN(id) FROM store_items GROUP BY name_uz
    )""")
    for seed_item in store_seed:
        existing = cur.execute('SELECT id FROM store_items WHERE name_uz=?', (seed_item[0],)).fetchone()
        if not existing:
            cur.execute("""INSERT INTO store_items
                (name_uz,name_ru,desc_uz,desc_ru,item_type,price_points,image,rarity,price_usd,is_paid)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", seed_item)


    # ── Seed mystery boxes ──
    box_seed = [
        ("Oddiy Quti","Обычный Ящик",50,"common"),
        ("Nadir Quti","Редкий Ящик",150,"rare"),
        ("Epik Quti","Эпический Ящик",300,"epic"),
        ("Afsonaviy Quti","Легендарный Ящик",500,"legendary"),
    ]
    for b in box_seed:
        cur.execute('''INSERT OR IGNORE INTO mystery_boxes
            (name_uz,name_ru,price_points,rarity) VALUES (?,?,?,?)''', b)

    # ── Seed courses ──
    default_courses = [
        ('html','HTML Asoslari','Основы HTML',
         "Web-sahifalar yaratish asoslarini o'rganing.",
         "Изучите основы создания веб-страниц.",
         '🌐','#e34c26',"Boshlangich",'Начальный','4 soat','Web Dasturlash','Веб-разработка',1),
        ('css','CSS va Dizayn','CSS и Дизайн',
         "Zamonaviy CSS bilan chiroyli dizaynlar yarating.",
         "Создавайте красивые дизайны с CSS.",
         '🎨','#2965f1',"Boshlangich",'Начальный','5 soat','Web Dasturlash','Веб-разработка',2),
        ('javascript','JavaScript','JavaScript',
         "JavaScript bilan web-saytlarga interaktivlik qo'shing.",
         "Добавьте интерактивность сайтам с JavaScript.",
         '⚡','#f7df1e',"O'rta",'Средний','8 soat','Web Dasturlash','Веб-разработка',3),
        ('python','Python Dasturlash','Программирование на Python',
         "Python'ni noldan o'rganing.",
         "Изучите Python с нуля.",
         '🐍','#3776ab',"Boshlangich",'Начальный','10 soat','Dasturlash','Программирование',4),
        ('csharp','C# va .NET','C# и .NET',
         "C# bilan enterprise ilovalar yarating.",
         "Создавайте enterprise-приложения с C#.",
         '💎','#512bd4',"O'rta",'Средний','12 soat','Dasturlash','Программирование',5),
        ('cpp','C++ Dasturlash','Программирование на C++',
         "C++ bilan tizim dasturlashni o'rganing.",
         "Освойте системное программирование с C++.",
         '⚙️','#00599c',"Ilg'or",'Продвинутый','15 soat','Dasturlash','Программирование',6),
        ('ai-development','AI Dasturlash','Разработка ИИ',
         "Haqiqiy AI ilovalar yarating.",
         "Создавайте реальные AI-приложения.",
         '🤖','#10a37f',"Ilg'or",'Продвинутый','20 soat','Sun\'iy Intellekt','Искусственный интеллект',7),
    ]
    for row in default_courses:
        cur.execute('''INSERT OR IGNORE INTO courses
            (slug,title_uz,title_ru,desc_uz,desc_ru,icon,color,
             level_uz,level_ru,duration,category_uz,category_ru,sort_order)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', row)


    # ── GAMES ──
    cur.execute('''CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        category TEXT DEFAULT 'Boshqa',
        author_id INTEGER NOT NULL,
        thumbnail TEXT DEFAULT '',
        file_path TEXT DEFAULT '',
        game_entry TEXT DEFAULT 'index.html',
        views INTEGER DEFAULT 0,
        rating_avg REAL DEFAULT 0.0,
        rating_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        reject_reason TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS game_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(game_id, user_id)
    )''')

    # ── GAME MONETIZATION ──
    cur.execute('''CREATE TABLE IF NOT EXISTS game_monetization (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        status TEXT DEFAULT 'none',
        ad_title TEXT DEFAULT '',
        ad_description TEXT DEFAULT '',
        ad_link TEXT DEFAULT '',
        ad_cta TEXT DEFAULT 'Oynash',
        total_ad_clicks INTEGER DEFAULT 0,
        approved_at TEXT,
        UNIQUE(game_id)
    )''')

    # ── NOTIFICATIONS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        notif_type TEXT DEFAULT 'system',
        title TEXT NOT NULL,
        body TEXT DEFAULT '',
        ref_url TEXT DEFAULT '',
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Create gifts table
    cur.execute('''CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user_id INTEGER NOT NULL,
        to_user_id INTEGER NOT NULL,
        gift_type TEXT NOT NULL,
        gift_value TEXT NOT NULL,
        item_id INTEGER DEFAULT NULL,
        message TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        claimed INTEGER DEFAULT 0
    )''')

    # ── BLOG / SHORTS / VIDEOS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_type TEXT DEFAULT 'text',
        content TEXT DEFAULT '',
        media_url TEXT DEFAULT '',
        thumbnail_url TEXT DEFAULT '',
        title TEXT DEFAULT '',
        promo_link TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        likes_count INTEGER DEFAULT 0,
        comments_count INTEGER DEFAULT 0,
        shares_count INTEGER DEFAULT 0,
        tags TEXT DEFAULT '[]',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS post_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(post_id, user_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS post_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS follows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        follower_id INTEGER NOT NULL,
        following_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(follower_id, following_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS user_interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        weight INTEGER DEFAULT 1,
        UNIQUE(user_id, tag)
    )''')

    # ── BLOG / SHORTS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_type TEXT DEFAULT 'text',
        content TEXT DEFAULT '',
        media_url TEXT DEFAULT '',
        thumbnail_url TEXT DEFAULT '',
        title TEXT DEFAULT '',
        promo_link TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        likes_count INTEGER DEFAULT 0,
        comments_count INTEGER DEFAULT 0,
        shares_count INTEGER DEFAULT 0,
        tags TEXT DEFAULT '[]',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS post_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(post_id, user_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS post_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS follows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        follower_id INTEGER NOT NULL,
        following_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(follower_id, following_id)
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS user_interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        weight INTEGER DEFAULT 1,
        UNIQUE(user_id, tag)
    )''')

    # ── MONETIZATSIYA ──
    cur.execute('''CREATE TABLE IF NOT EXISTS monetization (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        status TEXT DEFAULT 'none',
        ad_title TEXT DEFAULT '',
        ad_description TEXT DEFAULT '',
        ad_link TEXT DEFAULT '',
        ad_cta TEXT DEFAULT 'Batafsil',
        ad_bg_color TEXT DEFAULT '#1a1a2e',
        total_ad_clicks INTEGER DEFAULT 0,
        total_view_coins INTEGER DEFAULT 0,
        applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
        approved_at TEXT
    )''')

    # ── YOUTUBE SHORTS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS yt_shorts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        youtube_id TEXT NOT NULL UNIQUE,
        title TEXT DEFAULT '',
        tags TEXT DEFAULT '[]',
        views INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        added_by INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # ── VIDEO WATCH STATS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS video_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        viewer_id INTEGER DEFAULT 0,
        watch_seconds INTEGER DEFAULT 0,
        viewed_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # ── AD CLICKS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS ad_clicks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        monetization_id INTEGER NOT NULL,
        viewer_id INTEGER DEFAULT 0,
        clicked_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Add new user columns
    add_col('users', 'followers_count', 'INTEGER DEFAULT 0')
    add_col('users', 'following_count', 'INTEGER DEFAULT 0')
    add_col('users', 'is_premium', 'INTEGER DEFAULT 0')
    add_col('users', 'is_content_creator', 'INTEGER DEFAULT 0')
    add_col('users', 'total_video_views', 'INTEGER DEFAULT 0')
    add_col('posts', 'watch_seconds_total', 'INTEGER DEFAULT 0')

    # Seed demo YouTube Shorts (popular educational/coding shorts)
    demo_yt_shorts = [
        ('dQw4w9WgXcQ', 'Python tutorial', '["python","coding"]'),
        ('BgLTDT03QtU', 'Web development tip', '["web","html","css"]'),
        ('9bZkp7q19f0', 'JavaScript trick', '["javascript","js"]'),
        ('hT_nvWreIhg', 'Algorithm explained', '["algorithm","cs"]'),
        ('kJQP7kiw5Fk', 'Data structures', '["datastructures","coding"]'),
        ('pRpeEdMmmQ0', 'Machine learning', '["ai","ml"]'),
        ('60ItHLz5WEA', 'Git tutorial', '["git","devops"]'),
        ('nfmr7WqKwbs', 'Linux commands', '["linux","terminal"]'),
        ('FQM1pZgGbLQ', 'Database SQL', '["sql","database"]'),
        ('vNNq2YJ1v4k', 'React hooks', '["react","frontend"]'),
        ('Yw6u6YkTgQ4', 'Docker basics', '["docker","devops"]'),
        ('_sH8bFHnJE4', 'API design', '["api","backend"]'),
    ]
    for yt_id, title, tags in demo_yt_shorts:
        try:
            cur.execute('INSERT OR IGNORE INTO yt_shorts (youtube_id,title,tags,added_by) VALUES (?,?,?,0)',
                       (yt_id, title, tags))
        except: pass

    # ── SUPPORT TICKETS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 0,
        username TEXT DEFAULT '',
        ticket_type TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'open',
        reply TEXT DEFAULT '',
        replied_by INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        replied_at TEXT
    )''')

    # ── VACANCY POSITIONS ──
    cur.execute('''CREATE TABLE IF NOT EXISTS vacancy_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        requirements TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_by INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    _seed_lessons_from_files(cur)

    # ── MASALALAR (Problems) ──
    cur.execute('''CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        input_format TEXT DEFAULT '',
        output_format TEXT DEFAULT '',
        constraints TEXT DEFAULT '',
        example_input TEXT DEFAULT '',
        example_output TEXT DEFAULT '',
        difficulty TEXT DEFAULT 'easy',
        points INTEGER DEFAULT 100,
        time_limit INTEGER DEFAULT 2,
        memory_limit INTEGER DEFAULT 256,
        category TEXT DEFAULT 'Asosiy',
        is_active INTEGER DEFAULT 1,
        created_by INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        problem_id INTEGER NOT NULL,
        language TEXT DEFAULT 'python',
        code TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        runtime_ms INTEGER DEFAULT 0,
        memory_kb INTEGER DEFAULT 0,
        points_earned INTEGER DEFAULT 0,
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # ── GROUP INVITE LINKS ──
    add_col('groups', 'invite_code', "TEXT DEFAULT ''")
    add_col('groups', 'group_category', "TEXT DEFAULT 'normal'")

    # ── GROUP MODERATION ──
    add_col('group_members', 'is_muted', 'INTEGER DEFAULT 0')
    add_col('group_members', 'is_banned', 'INTEGER DEFAULT 0')
    add_col('group_members', 'restrict_media', 'INTEGER DEFAULT 0')
    add_col('group_members', 'restrict_tag', 'INTEGER DEFAULT 0')

    add_col('problems', 'category', "TEXT DEFAULT 'Asosiy'")

    # Game comments table
    cur.execute('''CREATE TABLE IF NOT EXISTS game_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(game_id) REFERENCES games(id),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # Multilang fields for games
    add_col('games', 'description_ru', "TEXT DEFAULT ''")
    add_col('games', 'description_en', "TEXT DEFAULT ''")
    add_col('games', 'title_ru', "TEXT DEFAULT ''")
    add_col('games', 'title_en', "TEXT DEFAULT ''")
    # Multilang fields for blog posts
    add_col('posts', 'title_ru', "TEXT DEFAULT ''")
    add_col('posts', 'title_en', "TEXT DEFAULT ''")
    add_col('posts', 'content_ru', "TEXT DEFAULT ''")
    add_col('posts', 'content_en', "TEXT DEFAULT ''")
    add_col('mavzular', 'video_url_ru', "TEXT DEFAULT ''")
    add_col('mavzular', 'video_url_en', "TEXT DEFAULT ''")

    # Moderator roli uchun maxsus foydalanuvchilar
    for uname in ('fuzayl', 'shams', 'adobe'):
        try:
            cur.execute("UPDATE users SET role='moderator' WHERE username=? AND role='student'", (uname,))
        except: pass

    # Seed default problems (categorized)
    sample_problems = [
        # ─── KIRISH/CHIQISH ───
        ("Salom Dunyo", "Ekranga aynan 'Hello World' so'zini chiqaring.",
         "Kirish yo'q.", "Bitta qator: Hello World",
         "Vaqt: 1s. Xotira: 256MB", "", "Hello World", "easy", 50, "Kirish/Chiqish"),

        ("Ismni chiqarish", "Foydalanuvchidan ism o'qing va 'Salom, <ism>!' formatida chiqaring.",
         "Bitta qatorda ism.", "Salom, <ism>!",
         "1 ≤ |ism| ≤ 50", "Ali", "Salom, Ali!", "easy", 60, "Kirish/Chiqish"),

        ("Ikkita son yig'indisi", "Ikkita butun son A va B ni qo'shing.",
         "Birinchi qatorda A va B (bo'shliq bilan).", "A+B ni chiqaring.",
         "1 ≤ A, B ≤ 10^9", "3 5", "8", "easy", 100, "Kirish/Chiqish"),

        ("Ko'paytma", "Ikkita sonning ko'paytmasini toping.",
         "A va B soni.", "A*B ni chiqaring.",
         "1 ≤ A, B ≤ 10^4", "6 7", "42", "easy", 80, "Kirish/Chiqish"),

        # ─── SHARTLI OPERATORLAR ───
        ("Musbat yoki manfiy", "Son musbatmi, manfiyimi yoki nolmi?",
         "Bitta butun son N.", "'musbat', 'manfiy' yoki 'nol' chiqaring.",
         "-10^9 ≤ N ≤ 10^9", "5", "musbat", "easy", 100, "Shartli operatorlar"),

        ("Juft yoki toq", "Son juftmi yoki toqmi?",
         "Bitta butun son N.", "'juft' yoki 'toq' chiqaring.",
         "1 ≤ N ≤ 10^9", "4", "juft", "easy", 100, "Shartli operatorlar"),

        ("Eng katta ikki son", "Ikkita sondan kattasini toping.",
         "A va B soni.", "Max(A, B) ni chiqaring.",
         "1 ≤ A, B ≤ 10^9", "3 7", "7", "easy", 120, "Shartli operatorlar"),

        ("Uch son maksimumi", "Uchta sondan eng kattasini toping.",
         "A, B, C sonlari.", "Max qiymatni chiqaring.",
         "1 ≤ A, B, C ≤ 10^9", "3 7 2", "7", "easy", 130, "Shartli operatorlar"),

        # ─── SIKLLAR ───
        ("1 dan N gacha", "1 dan N gacha bo'lgan sonlarni bir qatorda chiqaring.",
         "Bitta son N.", "1 dan N gacha sonlar (bo'shliq bilan).",
         "1 ≤ N ≤ 1000", "5", "1 2 3 4 5", "easy", 100, "Sikllar"),

        ("Juft sonlar yig'indisi", "1 dan N gacha juft sonlar yig'indisini toping.",
         "Bitta son N.", "Juft sonlar yig'indisi.",
         "1 ≤ N ≤ 10000", "6", "12", "easy", 150, "Sikllar"),

        ("Faktorial", "N! ni hisoblang.",
         "Bitta son N.", "N! ni chiqaring.",
         "1 ≤ N ≤ 12", "5", "120", "easy", 150, "Sikllar"),

        ("Raqamlar yig'indisi", "Sonning barcha raqamlari yig'indisini toping.",
         "Bitta musbat son N.", "Raqamlar yig'indisi.",
         "1 ≤ N ≤ 10^9", "1234", "10", "easy", 150, "Sikllar"),

        # ─── MASSIVLAR ───
        ("Eng katta son", "N ta sondan eng kattasini toping.",
         "Birinchi qatorda N, ikkinchi qatorda N ta son.", "Eng katta sonni chiqaring.",
         "1 ≤ N ≤ 1000, -10^9 ≤ a[i] ≤ 10^9", "5\n3 1 4 1 5", "5", "easy", 150, "Massivlar"),

        ("Sonlar o'rtachasi", "N ta sonning o'rtachasini hisoblang.",
         "N, so'ng N ta son.", "O'rtachani (float) chiqaring.",
         "1 ≤ N ≤ 1000", "4\n1 2 3 4", "2.5", "easy", 160, "Massivlar"),

        ("Saralanmish massiv", "N ta sonni o'sish tartibida saralang.",
         "N, so'ng N ta son.", "Saralangan sonlarni chiqaring.",
         "1 ≤ N ≤ 10000", "5\n5 2 8 1 9", "1 2 5 8 9", "medium", 250, "Massivlar"),

        ("Massivda qidirish", "X soni massivda bormi?",
         "N, so'ng N ta son, keyin X.", "'ha' yoki 'yoq' chiqaring.",
         "1 ≤ N ≤ 10000", "5\n3 1 4 1 5\n4", "ha", "easy", 180, "Massivlar"),

        # ─── SATRLAR ───
        ("Palindrom tekshirish", "So'z palindrommi?",
         "Bitta so'z.", "'YES' yoki 'NO'.",
         "1 ≤ |s| ≤ 100, faqat kichik harflar", "racecar", "YES", "medium", 200, "Satrlar"),

        ("Satr uzunligi", "Satrning uzunligini toping.",
         "Bitta satr.", "Uzunlikni chiqaring.",
         "1 ≤ |s| ≤ 1000", "salom", "5", "easy", 80, "Satrlar"),

        ("Harflarni almashtirish", "Kichik harflarni katta harflarga o'giring.",
         "Bitta satr.", "Katta harfli satr.",
         "1 ≤ |s| ≤ 1000", "salom", "SALOM", "easy", 100, "Satrlar"),

        ("So'zlar soni", "Satrdagi so'zlar sonini toping.",
         "Bitta satr.", "So'zlar sonini chiqaring.",
         "1 ≤ |s| ≤ 1000", "salom dunyo bilimxon", "3", "easy", 120, "Satrlar"),

        # ─── MATEMATIKA ───
        ("Fibonachchi soni", "N-chi Fibonachchi sonini toping (F1=1, F2=1).",
         "Bitta son N.", "N-chi Fibonachchi sonini chiqaring.",
         "1 ≤ N ≤ 40", "7", "13", "medium", 200, "Matematika"),

        ("EKUB", "Ikki sonning eng katta umumiy bo'luvchisini toping.",
         "A va B.", "EKUB(A, B).",
         "1 ≤ A, B ≤ 10^9", "12 8", "4", "medium", 200, "Matematika"),

        ("Tub son tekshirish", "Son tubmi?",
         "Bitta son N.", "'tub' yoki 'tub emas'.",
         "2 ≤ N ≤ 10^6", "7", "tub", "medium", 220, "Matematika"),

        ("Tub sonlar", "N gacha bo'lgan tub sonlarni chiqaring.",
         "Bitta son N.", "Tub sonlarni bo'shliq bilan.",
         "2 ≤ N ≤ 100", "10", "2 3 5 7", "medium", 250, "Matematika"),

        ("Daraja", "A ning B darajasini hisoblang.",
         "A va B.", "A^B ni chiqaring.",
         "1 ≤ A ≤ 10, 0 ≤ B ≤ 10", "2 10", "1024", "easy", 150, "Matematika"),

        # ─── REKURSIYA ───
        ("Rekursiv faktorial", "N! ni rekursiya bilan hisoblang.",
         "Bitta son N.", "N!",
         "0 ≤ N ≤ 12", "6", "720", "medium", 250, "Rekursiya"),

        ("Hanoy minorasi", "Hanoy minorasi uchun minimal qadam soni.",
         "Disk soni N.", "2^N - 1 ni chiqaring.",
         "1 ≤ N ≤ 20", "3", "7", "medium", 250, "Rekursiya"),

        # ─── MURAKKAB ───
        ("Graf qisqa yo'l (BFS)", "Ikki tepa orasida eng qisqa yo'lni toping.",
         "N va M, keyin M ta qirra (u v), so'ng S va T.", "S dan T gacha minimal qadam. Yo'q bo'lsa -1.",
         "1 ≤ N ≤ 1000, 1 ≤ M ≤ 10000", "4 4\n1 2\n2 3\n3 4\n1 4\n1 4", "1", "hard", 400, "Graf va BFS"),

        ("Eng uzun o'suvchi keta'lma (LIS)", "Massivda eng uzun o'suvchi ketma-ketlikni toping.",
         "N, so'ng N ta son.", "LIS uzunligini chiqaring.",
         "1 ≤ N ≤ 1000", "6\n3 10 2 1 20 4", "3", "hard", 450, "Dinamik dasturlash"),

        ("Tanga muammosi (DP)", "Minimal tangalar soni bilan S summani to'plang.",
         "Birinchi qatorda N va S, ikkinchi qatorda N ta tanga qiymati.",
         "Minimal tanga soni. Mumkin bo'lmasa -1.",
         "1 ≤ N ≤ 20, 1 ≤ S ≤ 10000", "3 11\n1 5 6", "2", "hard", 500, "Dinamik dasturlash"),
        # === QOSHIMCHA 70+ MASALALAR ===
        # --- KIRISH/CHIQISH ---
        ("Uch son yig'indisi", "Uchta butun sonning yig'indisini toping.",
         "Bitta qatorda A, B, C sonlari.", "A+B+C ni chiqaring.",
         "1<=A,B,C<=10^6", "2 3 5", "10", "easy", 60, "Kirish/Chiqish"),
        ("Bo'linma va qoldiq", "A ni B ga bo'lgandagi bo'linma va qoldiqni toping.",
         "A va B.", "Bo'linma va qoldiq (bo'shliq bilan).",
         "1<=B<=A<=10^9", "17 5", "3 2", "easy", 80, "Kirish/Chiqish"),
        ("Kvadrat hisoblash", "Sonning kvadratini hisoblang.",
         "Bitta son N.", "N*N ni chiqaring.",
         "1<=N<=10^4", "9", "81", "easy", 70, "Kirish/Chiqish"),
        ("Absolut qiymat", "Sonning absolut qiymatini toping.",
         "Bitta butun son N.", "|N| ni chiqaring.",
         "-10^9<=N<=10^9", "-42", "42", "easy", 70, "Kirish/Chiqish"),
        ("Sonlar almashish", "A va B ni almashtiring va chiqaring.",
         "A va B.", "Almashtirilgan A va B.",
         "1<=A,B<=10^9", "3 7", "7 3", "easy", 80, "Kirish/Chiqish"),
        # --- SHARTLI ---
        ("Yil fasli", "Oy raqamiga qarab fasli aniqlang.",
         "1-12 orasida oy.", "Qish/Bahor/Yoz/Kuz chiqaring.",
         "1<=M<=12", "7", "Yoz", "easy", 120, "Shartli operatorlar"),
        ("Katta-kichik yoki teng", "Ikki sonni taqqoslang.",
         "A va B.", "katta, kichik yoki teng chiqaring.",
         "0<=A,B<=10^9", "5 10", "kichik", "easy", 100, "Shartli operatorlar"),
        ("Uchburchak tekshirish", "Uch tomon bilan uchburchak hosil bo'ladimi?",
         "A, B, C tomonlari.", "HA yoki YOQ chiqaring.",
         "1<=A,B,C<=1000", "3 4 5", "HA", "easy", 130, "Shartli operatorlar"),
        ("Kabisa yili", "Yil kabisa yili ekanligini tekshiring.",
         "Bitta yil raqami.", "kabisa yoki oddiy chiqaring.",
         "1<=Y<=3000", "2024", "kabisa", "easy", 150, "Shartli operatorlar"),
        ("Baho aniqlash", "Ball asosida baho: 90-100=A'lo, 70-89=Yaxshi, 50-69=Qoniqarli, 0-49=Qoniqarsiz.",
         "Son (0-100).", "Bahoni chiqaring.",
         "0<=N<=100", "85", "Yaxshi", "easy", 130, "Shartli operatorlar"),
        # --- SIKLLAR ---
        ("Ko'paytma jadvali", "N ning ko'paytma jadvalini chiqaring (1-10).",
         "Bitta son N.", "N*1 dan N*10 gacha (yangi qatorda).",
         "1<=N<=10", "3", "3\n6\n9\n12\n15\n18\n21\n24\n27\n30", "easy", 140, "Sikllar"),
        ("Tub sonlar soni", "1 dan N gacha tub sonlar nechta?",
         "Bitta son N.", "Tub sonlar sonini chiqaring.",
         "2<=N<=10000", "10", "4", "medium", 200, "Sikllar"),
        ("Yulduzlar uchburchak", "N qator uchburchak yulduz chiqaring.",
         "Bitta son N.", "1,2,...,N tadan yulduz (yangi qatorda).",
         "1<=N<=10", "4", "*\n**\n***\n****", "easy", 120, "Sikllar"),
        ("Raqamlar ko'paytmasi", "Sonning barcha raqamlari ko'paytmasini toping.",
         "Bitta musbat son N.", "Raqamlar ko'paytmasi.",
         "1<=N<=10^9", "1234", "24", "easy", 150, "Sikllar"),
        ("Eng kichik bo'luvchi", "Sonning 1 dan katta eng kichik bo'luvchisini toping.",
         "Bitta son N.", "Eng kichik bo'luvchi.",
         "2<=N<=10^6", "12", "2", "easy", 150, "Sikllar"),
        ("N-chi Fibonacci", "Fibonacci ketma-ketligining N-chi hadini toping. F1=1, F2=1.",
         "Bitta son N.", "F(N) ni chiqaring.",
         "1<=N<=30", "10", "55", "easy", 180, "Sikllar"),
        # --- MASSIVLAR ---
        ("Massiv teskari", "Massivni teskari tartibda chiqaring.",
         "N, so'ng N ta son.", "Teskari tartibdagi sonlar.",
         "1<=N<=1000", "5\n1 2 3 4 5", "5 4 3 2 1", "easy", 150, "Massivlar"),
        ("Massiv yig'indisi", "N ta sonning yig'indisini toping.",
         "N, so'ng N ta son.", "Yig'indi.",
         "1<=N<=10000", "5\n1 2 3 4 5", "15", "easy", 100, "Massivlar"),
        ("Takroriy elementlar", "Massivda takroriy element bormi?",
         "N, so'ng N ta son.", "HA yoki YOQ.",
         "1<=N<=10000", "5\n1 2 3 2 5", "HA", "medium", 220, "Massivlar"),
        ("Massivda juft sonlar", "Massivdagi juft sonlarni chiqaring.",
         "N, so'ng N ta son.", "Juft sonlar, yo'q bo'lsa YOQ.",
         "1<=N<=1000", "6\n1 2 3 4 5 6", "2 4 6", "easy", 160, "Massivlar"),
        ("Maksimal ketma-ketlik", "Massivda maksimal ketma-ketlik yig'indisini toping (Kadane).",
         "N, so'ng N ta son.", "Maksimal yig'indi.",
         "1<=N<=10000", "8\n-2 1 -3 4 -1 2 1 -5 4", "6", "hard", 400, "Massivlar"),
        ("Ikki massiv kesishma", "Ikki massivning umumiy elementlarini toping.",
         "N va M, so'ng N ta son, so'ng M ta son.", "Umumiy elementlar yoki YOQ.",
         "1<=N,M<=1000", "3 3\n1 2 3\n2 3 4", "2 3", "medium", 250, "Massivlar"),
        # --- SATRLAR ---
        ("Satrni teskari", "Satrni teskari tartibda chiqaring.",
         "Bitta satr.", "Teskari satr.",
         "1<=|s|<=1000", "salom", "molas", "easy", 100, "Satrlar"),
        ("Satrda harf soni", "Satrdagi kichik harflar sonini toping.",
         "Bitta satr.", "Kichik harf soni.",
         "1<=|s|<=1000", "Hello World", "8", "easy", 110, "Satrlar"),
        ("Satr ikkinchi darajada", "Satrni 2 marta takrorlang.",
         "Bitta satr.", "Satr ikki marta.",
         "1<=|s|<=500", "abc", "abcabc", "easy", 90, "Satrlar"),
        ("CSV ajratish", "Vergul bilan ajratilgan qiymatlarni ajrating.",
         "Vergul bilan ajratilgan satr.", "Har birini yangi qatorda.",
         "1<=elementlar<=100", "a,b,c,d", "a\nb\nc\nd", "easy", 130, "Satrlar"),
        # --- MATEMATIKA ---
        ("EKUB va EKUK", "Ikki sonning EKUB va EKUKni hisoblang.",
         "A va B.", "EKUB va EKUK (bo'shliq bilan).",
         "1<=A,B<=10^6", "4 6", "2 12", "medium", 220, "Matematika"),
        ("Sonlar yig'indisi 1 dan N", "1+2+...+N yig'indisini hisoblang.",
         "Bitta son N.", "N*(N+1)/2 ni chiqaring.",
         "1<=N<=10^9", "100", "5050", "easy", 100, "Matematika"),
        ("Kvadrat ildiz", "Sonning butun qismidagi kvadrat ildizini toping.",
         "Bitta son N.", "floor(sqrt(N)) chiqaring.",
         "0<=N<=10^12", "16", "4", "easy", 120, "Matematika"),
        ("Raqamlar soni", "Sonning nechta raqamdan iboratligini toping.",
         "Bitta musbat son N.", "Raqamlar soni.",
         "1<=N<=10^18", "12345", "5", "easy", 100, "Matematika"),
        ("Palindrom son", "Son palindrommi?",
         "Bitta musbat son N.", "HA yoki YOQ.",
         "1<=N<=10^9", "12321", "HA", "easy", 130, "Matematika"),
        ("Kombinatsiya C(N,K)", "C(N,K) ni hisoblang.",
         "N va K.", "C(N,K) qiymatini chiqaring.",
         "0<=K<=N<=20", "5 2", "10", "medium", 250, "Matematika"),
        ("Modulli hisob", "(A^B) mod M ni hisoblang.",
         "A, B, M.", "(A^B) mod M.",
         "1<=A,B<=10^9, 2<=M<=10^9", "2 10 1000", "24", "medium", 280, "Matematika"),
        # --- REKURSIYA ---
        ("Ikkilik qidirish", "Saralangan massivda X ni ikkilik qidirish bilan toping.",
         "N, so'ng N ta saralangan son, keyin X.", "Indeks (0-dan) yoki -1.",
         "1<=N<=100000", "5\n1 3 5 7 9\n5", "2", "medium", 280, "Rekursiya"),
        ("Quvvat hisoblash (tez)", "A^B ni hisoblang (mod 10^9+7).",
         "A va B.", "A^B mod (10^9+7).",
         "1<=A,B<=10^18", "2 100", "976371285", "hard", 380, "Rekursiya"),
        # --- HASH VA SET ---
        ("Noyob elementlar", "Massivdagi noyob elementlarni chiqaring.",
         "N, so'ng N ta son.", "Noyob elementlar (tartib saqlansin).",
         "1<=N<=100000", "7\n1 2 3 2 4 1 5", "1 2 3 4 5", "medium", 220, "Hash va Set"),
        ("Anagramma tekshirish", "Ikki so'z anagrammami?",
         "Ikkita so'z (alohida qatorda).", "HA yoki YOQ.",
         "1<=|s|<=1000", "listen\nsilent", "HA", "medium", 200, "Hash va Set"),
        ("Chastota jadvali", "Eng ko'p takrorlangan elementni toping.",
         "N, so'ng N ta son.", "Eng ko'p takrorlangan son.",
         "1<=N<=100000", "7\n1 3 2 3 4 3 1", "3", "medium", 220, "Hash va Set"),
        ("Ikkita yig'indi (Two Sum)", "Yig'indisi S ga teng ikki elementning indekslarini toping.",
         "N va S, so'ng N ta son.", "Ikki indeks (0-dan, bo'shliq bilan).",
         "2<=N<=10000", "5 9\n2 7 11 15 1", "0 1", "medium", 280, "Hash va Set"),
        # --- STEK VA NAVBAT ---
        ("Qavslar tekshirish", "Qavslar to'g'ri joylashganmi? ()[]{}",
         "Bitta satr.", "HA yoki YOQ.",
         "1<=|s|<=1000", "({[]})", "HA", "medium", 250, "Stek va Navbat"),
        ("Navbatni simulyatsiya", "N kishi navbatda. Umumiy kutish vaqti.",
         "N, so'ng N ta vaqt.", "Har bir kishining kutish vaqti yig'indisi.",
         "1<=N<=1000", "3\n2 4 1", "6", "medium", 280, "Stek va Navbat"),
        # --- GREEDY ---
        ("Tangalar greedy", "Eng kam tanga: 1,5,10,25 tiyin.",
         "Bitta son N.", "Tanga soni.",
         "1<=N<=10000", "41", "4", "medium", 250, "Greedy"),
        ("Qo'shni farq minimumi", "Saralangan massivda qo'shni farq minimumi.",
         "N, so'ng N ta son.", "Minimal qo'shni farq.",
         "2<=N<=100000", "5\n1 3 6 10 15", "2", "medium", 260, "Greedy"),
        # --- DINAMIK DASTURLASH ---
        ("Yo'l hisoblash", "N*M to'rda chapdan quyi-o'ngga necha xil yo'l?",
         "N va M.", "Yo'llar soni.",
         "1<=N,M<=20", "3 3", "6", "medium", 300, "Dinamik dasturlash"),
        ("Knapsack masalasi", "N buyum (w,v), W sig'im. Maksimal qiymat.",
         "N va W, so'ng N qator (w v).", "Maksimal qiymat.",
         "1<=N<=20, 1<=W<=1000", "3 5\n2 3\n3 4\n4 5", "7", "hard", 500, "Dinamik dasturlash"),
        ("Levenshtein masofasi", "Ikki satrni bir xil qilish uchun minimal operatsiyalar.",
         "Ikkita satr.", "Minimal operatsiyalar.",
         "1<=|s|<=500", "kitten\nsitting", "3", "hard", 500, "Dinamik dasturlash"),
        # --- GEOMETRIYA ---
        ("Nuqtalar masofasi", "Ikki nuqta orasidagi masofa.",
         "x1 y1 va x2 y2.", "Masofa (float, 2 kasr).",
         "-1000<=x,y<=1000", "0 0 3 4", "5.00", "easy", 150, "Geometriya"),
        ("Uchburchak yuzi", "Uch nuqta bo'yicha uchburchak yuzini hisoblang.",
         "Uchta nuqta (x y).", "Yuz (float, 2 kasr).",
         "-1000<=x,y<=1000", "0 0\n4 0\n0 3", "6.00", "medium", 280, "Geometriya"),
        ("Doira yuzi", "R radiusli doiraning yuzini hisoblang.",
         "Bitta son R.", "Yuz (float, 2 kasr).",
         "1<=R<=1000", "5", "78.54", "easy", 130, "Geometriya"),
        # --- BIT OPERATSIYALAR ---
        ("Ikkilik ko'rinish", "Sonni ikkilik sanoq sistemasida chiqaring.",
         "Bitta son N.", "Ikkilik ko'rinish.",
         "1<=N<=10^9", "10", "1010", "easy", 150, "Bit operatsiyalar"),
        ("Bit soni", "Sonning ikkilik ko'rinishidagi 1 larning soni.",
         "Bitta son N.", "1 larning soni.",
         "0<=N<=10^9", "13", "3", "easy", 150, "Bit operatsiyalar"),
        ("XOR yig'indisi", "N ta son XOR yig'indisini hisoblang.",
         "N, so'ng N ta son.", "XOR yig'indisi.",
         "1<=N<=100000", "4\n1 2 3 4", "4", "medium", 220, "Bit operatsiyalar"),
        # --- IKKI POINTER ---
        ("Ikkita pointer yig'indisi", "Saralangan massivda S ga teng juftlik bormi?",
         "N va S, so'ng N ta saralangan son.", "HA yoki YOQ.",
         "2<=N<=100000", "5 9\n1 2 4 5 7", "HA", "medium", 280, "Ikki pointer"),
        # --- STRING ALGORITMLARI ---
        ("Eng uzun takrorlanmaydigan", "Eng uzun takrorlanmaydigan belgili pastki satr uzunligi.",
         "Bitta satr.", "Uzunlik.",
         "1<=|s|<=50000", "abcabcbb", "3", "hard", 420, "String algoritmlari"),
        # --- SIMULYATSIYA ---
        ("Soat qo'llari burchagi", "H soat M daqiqada soat va daqiqa qo'llari burchagi.",
         "H va M.", "Burchak daraja (float, 1 kasr).",
         "0<=H<=23, 0<=M<=59", "12 30", "165.0", "medium", 300, "Simulyatsiya"),
        ("Qo'shma foiz", "P summa, R foiz, N yil.",
         "P, R, N.", "floor(P*(1+R/100)^N) chiqaring.",
         "1<=P<=10^6, 1<=R<=100, 1<=N<=50", "1000 10 3", "1331", "medium", 250, "Simulyatsiya"),
        # --- GRAF ---
        ("Graf bog'liqligi", "Graf bog'liqmi?",
         "N va M, keyin M ta qirra (u v).", "HA yoki YOQ.",
         "1<=N<=1000, 0<=M<=10000", "4 3\n1 2\n2 3\n3 4", "HA", "hard", 380, "Graf va BFS"),

        # ─── QOSHIMCHA 100+ ───
        ("Ikki sonni almashtirish", "Ikki sonni almashtirib chiqaring.",
         "A va B.", "Avval B, keyin A.",
         "1<=A,B<=10^9", "3 7", "7\n3", "easy", 50, "Kirish/Chiqish"),

        ("Son kvadrati", "Sonning kvadratini toping.",
         "Bitta son N.", "N*N.",
         "1<=N<=10^4", "12", "144", "easy", 70, "Matematika"),

        ("Raqamlar soni", "Sonning nechta raqami borligini toping.",
         "Bitta musbat son N.", "Raqamlar soni.",
         "1<=N<=10^18", "12345", "5", "easy", 100, "Matematika"),

        ("Sonni uch baravar", "Sonni uch baravarga ko'paytiring.",
         "Bitta N.", "3*N.",
         "1<=N<=10^8", "7", "21", "easy", 50, "Kirish/Chiqish"),

        ("Hafta kuni", "Kun raqamiga ko'ra hafta kunini chiqaring (1=Dushanba...7=Yakshanba).",
         "1 dan 7 gacha son.", "Hafta kuni nomi.",
         "1<=N<=7", "1", "Dushanba", "easy", 100, "Shartli operatorlar"),

        ("Son juft bolimiga bo'linadi", "N 4 ga bo'linadimi?",
         "Bitta N.", "HA yoki YOQ.",
         "1<=N<=10^9", "16", "HA", "easy", 80, "Shartli operatorlar"),

        ("Eng katta son (massiv)", "Massivdagi maksimumni toping.",
         "N va N ta son.", "Maksimal qiymat.",
         "1<=N<=100000", "5\n-3 -1 -4 -1 -5", "-1", "easy", 130, "Massivlar"),

        ("Massiv juftlarini sanash", "Massivda nechta juft son bor?",
         "N va N ta son.", "Juft sonlar soni.",
         "1<=N<=10000", "6\n1 2 3 4 5 6", "3", "easy", 120, "Massivlar"),

        ("So'z palindromi", "So'z palindrommi (katta-kichik harf farqi yo'q)?",
         "Bitta so'z.", "YES yoki NO.",
         "1<=|s|<=100", "MadaM", "YES", "easy", 180, "Satrlar"),

        ("Satr ichida son", "Satrdagi barcha raqamlarni chiqaring.",
         "Bitta satr.", "Faqat raqamlar (tartibda).",
         "1<=|s|<=200", "a1b2c3d", "123", "easy", 150, "Satrlar"),

        ("Eng uzun so'z", "Satrdagi eng uzun so'zni toping.",
         "Bitta satr.", "Eng uzun so'z (teng bo'lsa birinchisi).",
         "1<=so'z<=100", "men bilimxon bilan", "bilimxon", "easy", 160, "Satrlar"),

        ("Matritsa izlari", "N×N matritsaning izini (bosh diagonal elementlari yig'indisi) toping.",
         "N va N×N matritsa.", "Iz qiymati.",
         "1<=N<=10", "3\n1 2 3\n4 5 6\n7 8 9", "15", "easy", 180, "Matritsa"),

        ("Chiziq tenglamasi", "ax + b = 0 tenglamasining yechimini toping.",
         "a va b (a != 0).", "x = -b/a (float, 2 xona).",
         "-1000<=a,b<=1000, a!=0", "2 -6", "3.00", "easy", 150, "Matematika"),

        ("Kombinatsiya C(n,k)", "C(n,k) = n! / (k! * (n-k)!) ni hisoblang.",
         "n va k.", "C(n,k) qiymati.",
         "0<=k<=n<=15", "5 2", "10", "medium", 220, "Matematika"),

        ("Matn shifri ROT13", "Matnni ROT13 bilan shifrlang (a->n, b->o, ...).",
         "Bitta kichik harfli satr.", "Shifrlangan satr.",
         "1<=|s|<=1000", "hello", "uryyb", "medium", 240, "Satrlar"),

        ("Uchburchak maydoni", "Uchburchak maydoni (Geron formulasi).",
         "Uch tomon a, b, c.", "Maydon (2 xona aniqlik).",
         "1<=a,b,c<=1000, ular uchburchak hosil qiladi", "3 4 5", "6.00", "medium", 200, "Geometriya"),

        ("Sifr sonlar", "Massivda nechta nol bor?",
         "N va N ta son.", "Nollar soni.",
         "1<=N<=1000", "5\n1 0 2 0 3", "2", "easy", 100, "Massivlar"),

    ]
    for p in sample_problems:
        existing = cur.execute('SELECT id FROM problems WHERE title=?', (p[0],)).fetchone()
        if not existing:
            cur.execute('''INSERT INTO problems
                (title,description,input_format,output_format,constraints,example_input,example_output,difficulty,points,category)
                VALUES (?,?,?,?,?,?,?,?,?,?)''', p)

    conn.commit(); conn.close()

def _seed_lessons_from_files(cur):
    for slug in ['html','css','javascript','python','csharp','cpp','ai-development']:
        slug_dir = os.path.join(COURSES_DIR, slug)
        if not os.path.isdir(slug_dir): continue
        existing = cur.execute('SELECT id FROM bobs WHERE course_slug=?',(slug,)).fetchone()
        if existing: continue
        bob_names = {
            'html':('1-Bob: HTML Asoslari','1-Глава: Основы HTML'),
            'css':('1-Bob: CSS Asoslari','1-Глава: Основы CSS'),
            'javascript':('1-Bob: JS Asoslari','1-Глава: Основы JS'),
            'python':('1-Bob: Python Asoslari','1-Глава: Основы Python'),
            'csharp':('1-Bob: C# Kirish','1-Глава: Введение в C#'),
            'cpp':('1-Bob: C++ Kirish','1-Глава: Введение в C++'),
            'ai-development':('1-Bob: AI Asoslari','1-Глава: Основы AI'),
        }
        bname_uz, bname_ru = bob_names.get(slug,('1-Bob','1-Глава'))
        cur.execute('INSERT INTO bobs (course_slug,title_uz,title_ru,sort_order) VALUES (?,?,?,?)',
                    (slug,bname_uz,bname_ru,1))
        bob_id = cur.lastrowid
        lesson_dirs = sorted([d for d in os.listdir(slug_dir) if d.startswith('lesson')],
                             key=lambda x: int(''.join(filter(str.isdigit,x)) or '0'))
        for idx, ldir in enumerate(lesson_dirs, start=1):
            lpath = os.path.join(slug_dir, ldir)
            txt   = os.path.join(lpath,'lesson.txt')
            quiz  = os.path.join(lpath,'quiz.json')
            content = ''
            if os.path.exists(txt):
                with open(txt,'r',encoding='utf-8') as f: content = f.read()
            first_line = content.split('\n')[0] if content else f'Mavzu {idx}'
            title_uz = first_line.replace('LESSON','').replace(f'{idx}:','').strip(' :') or f'Mavzu {idx}'
            cur.execute('''INSERT INTO mavzular
                (bob_id,course_slug,title_uz,title_ru,content_uz,sort_order,points_reward)
                VALUES (?,?,?,?,?,?,?)''', (bob_id,slug,title_uz,title_uz,content,idx,10))
            mavzu_id = cur.lastrowid
            if os.path.exists(quiz):
                with open(quiz,'r',encoding='utf-8') as f:
                    try: qdata = json.load(f)
                    except: qdata = {'questions':[]}
                for q in qdata.get('questions',[]):
                    opts = json.dumps(q.get('options',[]),ensure_ascii=False)
                    cur.execute('''INSERT INTO quiz_questions
                        (mavzu_id,question_uz,options_uz,correct_idx,explanation_uz)
                        VALUES (?,?,?,?,?)''',
                        (mavzu_id,q.get('question',''),opts,q.get('correct',0),q.get('explanation','')))

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def get_user_progress(user_id):
    conn = get_db()
    rows = conn.execute('SELECT * FROM progress WHERE user_id=?',(user_id,)).fetchall()
    conn.close()
    return {r['mavzu_id']: dict(r) for r in rows}

def track(event_type, ref_id=None, ref_slug=None):
    try:
        conn = get_db()
        conn.execute('INSERT INTO analytics (user_id,event_type,ref_id,ref_slug) VALUES (?,?,?,?)',
                     (session.get('user_id'),event_type,ref_id,ref_slug))
        conn.commit(); conn.close()
    except: pass

def update_streak(user_id):
    """Update daily streak for user"""
    from datetime import date, timedelta
    today = date.today().isoformat()
    conn = get_db()
    try:
        conn.execute('INSERT OR IGNORE INTO streak_log (user_id, activity_date) VALUES (?,?)', (user_id, today))
        conn.commit()
        u = conn.execute('SELECT streak_days, last_activity_date, longest_streak FROM users WHERE id=?', (user_id,)).fetchone()
        ud = dict(u) if u else {}
        last = ud.get('last_activity_date', '')
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        if last == today:
            conn.close(); return
        if last == yesterday:
            new_streak = (ud.get('streak_days') or 0) + 1
        else:
            new_streak = 1
        longest = max(ud.get('longest_streak') or 0, new_streak)
        conn.execute('UPDATE users SET streak_days=?, last_activity_date=?, longest_streak=? WHERE id=?',
                     (new_streak, today, longest, user_id))
        conn.commit()
        # Bonus points for streak milestones
        if new_streak in (3, 7, 14, 30, 60, 100):
            bonus = {3:20, 7:50, 14:100, 30:250, 60:500, 100:1000}.get(new_streak, 0)
            conn.execute('UPDATE users SET points=points+? WHERE id=?', (bonus, user_id))
            conn.execute('INSERT INTO point_log (user_id,delta,reason) VALUES (?,?,?)',
                         (user_id, bonus, f'{new_streak} kunlik streak bonusi'))
            conn.commit()
    except Exception as e:
        print('Streak error:', e)
    finally:
        try: conn.close()
        except: pass

def add_points(user_id, delta, reason='', ref_id=None):
    conn = get_db()
    conn.execute('UPDATE users SET points=points+? WHERE id=?',(delta,user_id))
    conn.execute('INSERT INTO point_log (user_id,delta,reason,ref_id) VALUES (?,?,?,?)',
                 (user_id,delta,reason,ref_id))
    conn.commit(); conn.close()
    check_auto_titles(user_id)

def add_notification(user_id, notif_type, title, body='', ref_url=''):
    """Create a notification for a user"""
    try:
        conn = get_db()
        conn.execute('''INSERT INTO notifications (user_id,notif_type,title,body,ref_url)
            VALUES (?,?,?,?,?)''', (user_id, notif_type, title, body, ref_url))
        conn.commit(); conn.close()
    except Exception as e:
        pass

def check_auto_titles(user_id):
    """Auto-grant titles based on conditions"""
    conn = get_db()
    u = conn.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
    if not u: conn.close(); return
    pts = u['points']
    completed = conn.execute('SELECT COUNT(*) as c FROM progress WHERE user_id=? AND completed=1',(user_id,)).fetchone()['c']
    friends_c = conn.execute('''SELECT COUNT(*) as c FROM friends
        WHERE user1_id=? OR user2_id=?''',(user_id,user_id)).fetchone()['c']
    
    grants = []
    if pts >= 1000: grants.append('rich')
    if completed >= 10: grants.append('top_student')
    if completed >= 20: grants.append('scholar')
    if friends_c >= 5: grants.append('popular')

    for key in grants:
        existing = conn.execute('SELECT id FROM user_titles WHERE user_id=? AND title_key=?',(user_id,key)).fetchone()
        if not existing:
            conn.execute('INSERT OR IGNORE INTO user_titles (user_id,title_key,granted_by) VALUES (?,?,?)',
                         (user_id,key,user_id))
            # Notify user of new title
            title_names = {'rich':'💰 Boy','top_student':'📚 Top Talaba','scholar':'🎓 Olim','popular':'👥 Mashhur'}
            if key in title_names:
                conn.execute('''INSERT INTO notifications (user_id,notif_type,title,body,ref_url)
                    VALUES (?,?,?,?,?)''', (user_id,'system',
                    f"🏆 Yangi unvon qo'lga kiritildi!",
                    f"Siz '{title_names[key]}' unvoniga erishdingiz!",
                    f'/profile/{user_id}'))
        else:
            conn.execute('INSERT OR IGNORE INTO user_titles (user_id,title_key,granted_by) VALUES (?,?,?)',
                         (user_id,key,user_id))
    # Milestone notifications for points
    milestones = {100:'🌟 100 ochko!', 500:'💫 500 ochko!', 1000:'🔥 1000 ochko!', 5000:'👑 5000 ochko!'}
    for milestone, msg in milestones.items():
        if pts >= milestone:
            already = conn.execute('''SELECT id FROM notifications WHERE user_id=? AND body=?''',
                (user_id, msg)).fetchone()
            if not already:
                conn.execute('''INSERT INTO notifications (user_id,notif_type,title,body,ref_url)
                    VALUES (?,?,?,?,?)''', (user_id,'system','🎉 Yutuq qo\'lga kiritildi!', msg, '/leaderboard'))
    conn.commit(); conn.close()

def get_user_full(user_id, viewer_id=None):
    conn = get_db()
    u = conn.execute('SELECT * FROM users WHERE id=?',(user_id,)).fetchone()
    if not u: conn.close(); return None

    _lang = session.get('lang','uz') if 'lang' in session else 'uz'
    lang = _lang if _lang in ('uz','ru') else 'uz'  # en falls back to uz for DB fields

    titles = conn.execute('''SELECT t.* FROM user_titles ut
        JOIN titles t ON ut.title_key=t.key WHERE ut.user_id=?''',(user_id,)).fetchall()

    completed = conn.execute('SELECT COUNT(*) as c FROM progress WHERE user_id=? AND completed=1',(user_id,)).fetchone()['c']
    followers = conn.execute('''SELECT COUNT(*) as c FROM friends WHERE user2_id=?''',(user_id,)).fetchone()['c']
    friends_c = conn.execute('''SELECT COUNT(*) as c FROM friends
        WHERE user1_id=? OR user2_id=?''',(user_id,user_id)).fetchone()['c']

    # Course stats for profile page
    courses = conn.execute('SELECT * FROM courses WHERE is_active=1 ORDER BY sort_order').fetchall()
    course_stats = []
    for c in courses:
        c_dict = dict(c)
        ctotal = conn.execute('SELECT COUNT(*) as cnt FROM mavzular WHERE course_slug=?',(c['slug'],)).fetchone()['cnt']
        cdone  = conn.execute('SELECT COUNT(*) as cnt FROM progress WHERE user_id=? AND course_slug=? AND completed=1',(user_id,c['slug'])).fetchone()['cnt']
        if cdone > 0:
            course_stats.append({'slug':c['slug'],'title':c_dict.get(f'title_{lang}') or c['title_uz'],
                                  'icon':c['icon'],'color':c['color'],
                                  'completed':cdone,'total':ctotal,
                                  'pct':int((cdone/ctotal)*100) if ctotal else 0})

    friend_status = None
    if viewer_id and viewer_id != user_id:
        f = conn.execute('''SELECT * FROM friends
            WHERE (user1_id=? AND user2_id=?) OR (user1_id=? AND user2_id=?)''',
            (viewer_id,user_id,user_id,viewer_id)).fetchone()
        if f: friend_status = 'friends'
        else:
            req = conn.execute('''SELECT * FROM friend_requests
                WHERE from_id=? AND to_id=? AND status='pending' ''',
                (viewer_id,user_id)).fetchone()
            if req: friend_status = 'pending_sent'
            else:
                req2 = conn.execute('''SELECT * FROM friend_requests
                    WHERE from_id=? AND to_id=? AND status='pending' ''',
                    (user_id,viewer_id)).fetchone()
                if req2: friend_status = 'pending_received'
    conn.close()
    u_dict = dict(u)
    return {
        'id': u['id'], 'username': u['username'], 'full_name': u['full_name'] or '',
        'bio': u_dict.get('bio') or '', 'avatar': u_dict.get('avatar') or '',
        'banner': u_dict.get('banner') or '',
        'points': u_dict.get('points') or 0, 'role': u_dict.get('role') or 'student',
        'has_tick': u_dict.get('has_tick') or 0,
        'active_title': u_dict.get('active_title') or '',
        'active_frame': u_dict.get('active_frame') or '',
        'profile_color': u_dict.get('profile_color') or '#1B2A4A',
        'profile_style': u_dict.get('profile_style') or '',
        'is_premium': bool(u_dict.get('is_premium')),
        'yt_link': u_dict.get('yt_link') or '', 'ig_link': u_dict.get('ig_link') or '',
        'tg_link': u_dict.get('tg_link') or '', 'gh_link': u_dict.get('gh_link') or '',
        'yt_followers': u_dict.get('yt_followers') or 0,
        'ig_followers': u_dict.get('ig_followers') or 0,
        'completed_lessons': completed, 'followers': followers, 'friends_count': friends_c,
        'course_stats': course_stats,
        'titles': [{'key':t['key'],'label_uz':t['label_uz'],'label_ru':t['label_ru'],
                    'icon':t['icon'],'color':t['color'],'is_special':t['is_special']} for t in titles],
        'friend_status': friend_status,
        'created_at': u_dict.get('created_at') or '',
        'streak_days': u_dict.get('streak_days') or 0,
        'longest_streak': u_dict.get('longest_streak') or 0,
        'last_activity_date': u_dict.get('last_activity_date') or '',
    }

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def dec(*a,**k):
        if session.get('role') not in ('admin','moderator'): return jsonify({'error':'Forbidden'}),403
        return f(*a,**k)
    return dec

def login_required(f):
    from functools import wraps
    @wraps(f)
    def dec(*a,**k):
        if 'user_id' not in session: return jsonify({'error':'Not logged in'}),401
        return f(*a,**k)
    return dec

def allowed_img(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_IMG

def save_upload(file, directory, prefix=''):
    if not file or not file.filename: return None
    ext = file.filename.rsplit('.',1)[-1].lower()
    if ext not in ALLOWED_IMG and ext not in ALLOWED_VIDEO: return None
    fname = secure_filename(f"{prefix}_{int(datetime.now().timestamp())}.{ext}")
    path  = os.path.join(directory, fname)
    file.save(path)
    return fname

# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.get_json()
    username = (d.get('username') or '').strip()
    password = (d.get('password') or '').strip()
    if not username or not password:
        return jsonify({'success':False,'error':'Maydonlarni to\'ldiring'})
    hashed = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username=? AND password=?',(username,hashed)).fetchone()
    conn.close()
    if user:
        session.permanent = True
        session.update({'user_id':user['id'],'username':user['username'],
                        'full_name':user['full_name'],'role':user['role'],'lang':user['lang'] or 'uz'})
        track('login')
        return jsonify({'success':True,'role':user['role'],'name':user['full_name']})
    return jsonify({'success':False,'error':'Login yoki parol noto\'g\'ri'})

@app.route('/api/register', methods=['POST'])
def api_register():
    d = request.get_json()
    username  = (d.get('username') or '').strip()
    password  = (d.get('password') or '').strip()
    full_name = (d.get('full_name') or '').strip()
    email     = (d.get('email') or '').strip()
    if not all([username,password,full_name]):
        return jsonify({'success':False,'error':'Barcha maydonlarni to\'ldiring'})
    if len(password) < 6:
        return jsonify({'success':False,'error':'Parol kamida 6 ta belgi'})
    hashed = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = get_db()
        # Check username availability first
        existing = conn.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()
        if existing:
            conn.close()
            return jsonify({'success':False,'error':f'@{username} username allaqachon band. Boshqa username tanlang!'})
        conn.execute('INSERT INTO users (username,password,full_name,email) VALUES (?,?,?,?)',
                     (username,hashed,full_name,email))
        conn.commit()
        user = conn.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
        conn.close()
        session.permanent = True
        session.update({'user_id':user['id'],'username':user['username'],
                        'full_name':user['full_name'],'role':user['role'],'lang':'uz'})
        try:
            add_points(user['id'],50,"Ro'yxatdan o'tish uchun bonus")
        except Exception as ep:
            print("add_points error on register:", ep)
        return jsonify({'success':True,'role':'student'})
    except sqlite3.IntegrityError:
        return jsonify({'success':False,'error':f'@{username} username allaqachon band. Boshqa username tanlang!'})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success':True})

@app.route('/api/me')
def api_me():
    if 'user_id' not in session: return jsonify({'logged_in':False})
    return jsonify({'logged_in':True,'user_id':session['user_id'],
                    'username':session['username'],'full_name':session['full_name'],
                    'role':session['role'],'lang':session.get('lang','uz')})

@app.route('/api/set-lang', methods=['POST'])
def api_set_lang():
    lang = (request.get_json() or {}).get('lang','uz')
    if lang not in ('uz','ru','en'): lang='uz'
    session.permanent = True
    session['lang'] = lang
    if 'user_id' in session:
        conn=get_db(); conn.execute('UPDATE users SET lang=? WHERE id=?',(lang,session['user_id']))
        conn.commit(); conn.close()
    return jsonify({'success':True,'lang':lang})

# ─────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────
@app.route('/')
def index(): track('page_home'); return render_template('index.html')

@app.route('/login')
def login():
    if 'user_id' in session: return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect('/login')
    track('page_dashboard'); return render_template('dashboard.html')

@app.route('/course/<slug>')
def course(slug):
    if 'user_id' not in session: return redirect('/login')
    conn=get_db(); c=conn.execute('SELECT slug FROM courses WHERE slug=?',(slug,)).fetchone(); conn.close()
    if not c: return redirect('/dashboard')
    track('page_course',ref_slug=slug); return render_template('course.html')

@app.route('/lesson/<int:mid>')
def lesson(mid):
    if 'user_id' not in session: return redirect('/login')
    track('page_lesson',ref_id=mid); return render_template('lesson.html')

@app.route('/admin')
def admin():
    if session.get('role') not in ('admin', 'moderator'): return redirect('/login')
    return render_template('admin.html')

@app.route('/profile/<username>')
def profile(username):
    if 'user_id' not in session: return redirect('/login')
    return render_template('profile.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session: return redirect('/login')
    return render_template('chat.html')


@app.route('/social')
def social():
    if 'user_id' not in session: return redirect('/login')
    return render_template('social.html')

@app.route('/store')
def store():
    if 'user_id' not in session: return redirect('/login')
    return render_template('store.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session: return redirect('/login')
    return render_template('settings.html')

@app.route('/privacy')
def privacy_page():
    lang = session.get('lang','uz')
    return render_template('privacy.html', lang=lang)

@app.route('/streak')
def streak_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('streak.html')

@app.route('/api/streak/log')
@login_required
def api_streak_log():
    uid = session['user_id']
    conn = get_db()
    try:
        rows = conn.execute(
            'SELECT activity_date FROM streak_log WHERE user_id=? ORDER BY activity_date DESC LIMIT 90',
            (uid,)).fetchall()
        dates = [r['activity_date'] for r in rows]
    except:
        dates = []
    conn.close()
    return jsonify({'dates': dates})

@app.route('/terms')
def terms_page():
    lang = session.get('lang','uz')
    return render_template('terms.html', lang=lang)

@app.route('/cookie')
def cookie_page():
    return render_template('cookie.html')

@app.route('/contact')
def contact_page():
    lang = session.get('lang','uz')
    return render_template('contact.html', lang=lang)

@app.route('/about')
def about_page():
    lang = session.get('lang','uz')
    return render_template('about.html', lang=lang)

@app.route('/groups')
def groups():
    if 'user_id' not in session: return redirect('/login')
    return render_template('groups.html')

@app.route('/group/<slug>')
def group_page(slug):
    if 'user_id' not in session: return redirect('/login')
    return render_template('group_detail.html')

# ─────────────────────────────────────────
# COURSES API (same as v2)
# ─────────────────────────────────────────
@app.route('/api/courses')
def api_courses():
    _lang = session.get('lang','uz'); lang = _lang if _lang in ('uz','ru') else 'uz'
    user_id = session.get('user_id')
    conn = get_db()
    courses = conn.execute('SELECT * FROM courses WHERE is_active=1 ORDER BY sort_order').fetchall()
    result = []
    for c in courses:
        total = conn.execute('SELECT COUNT(*) as cnt FROM mavzular WHERE course_slug=?',(c['slug'],)).fetchone()['cnt']
        completed = 0
        if user_id:
            completed = conn.execute('SELECT COUNT(*) as cnt FROM progress WHERE user_id=? AND course_slug=? AND completed=1',(user_id,c['slug'])).fetchone()['cnt']
        result.append({'id':c['id'],'slug':c['slug'],'title':c[f'title_{lang}'],'desc':c[f'desc_{lang}'],
                       'icon':c['icon'],'color':c['color'],'level':c[f'level_{lang}'],'duration':c['duration'],
                       'category':c[f'category_{lang}'],'total_mavzu':total,'completed_mavzu':completed,
                       'progress_pct':int((completed/total)*100) if total else 0})
    conn.close(); return jsonify(result)

@app.route('/api/course/<slug>')
def api_course(slug):
    _lang = session.get('lang','uz'); lang = _lang if _lang in ('uz','ru') else 'uz'
    conn = get_db()
    c = conn.execute('SELECT * FROM courses WHERE slug=?',(slug,)).fetchone()
    if not c: conn.close(); return jsonify({'error':'Not found'}),404
    bobs = conn.execute('SELECT * FROM bobs WHERE course_slug=? ORDER BY sort_order',(slug,)).fetchall()
    user_id = session.get('user_id')
    progress = get_user_progress(user_id) if user_id else {}
    bob_list = []
    for b in bobs:
        mavzular = conn.execute('SELECT * FROM mavzular WHERE bob_id=? ORDER BY sort_order',(b['id'],)).fetchall()
        mavzu_list = []
        for m in mavzular:
            has_quiz = conn.execute('SELECT COUNT(*) as cnt FROM quiz_questions WHERE mavzu_id=?',(m['id'],)).fetchone()['cnt']>0
            prog = progress.get(m['id'],{})
            mavzu_list.append({'id':m['id'],'title':m[f'title_{lang}'] or m['title_uz'],
                               'has_video':bool(m['video_url']),'has_quiz':has_quiz,
                               'has_code':bool(m['code_example']),'completed':prog.get('completed',0),
                               'quiz_score':prog.get('quiz_score',-1),'points_reward':m['points_reward']})
        bob_list.append({'id':b['id'],'title':b[f'title_{lang}'] or b['title_uz'],'mavzular':mavzu_list})
    conn.close()
    return jsonify({'slug':c['slug'],'title':c[f'title_{lang}'],'desc':c[f'desc_{lang}'],
                    'icon':c['icon'],'color':c['color'],'level':c[f'level_{lang}'],
                    'duration':c['duration'],'bobs':bob_list})

@app.route('/api/lesson/<int:mid>')
def api_lesson(mid):
    _lang = session.get('lang','uz')
    lang = _lang if _lang in ('uz','ru','en') else 'uz'
    db_lang = 'uz' if lang == 'en' else lang  # DB columns only have uz/ru
    conn = get_db()
    m = conn.execute('SELECT * FROM mavzular WHERE id=?',(mid,)).fetchone()
    if not m: conn.close(); return jsonify({'error':'Not found'}),404
    has_quiz = conn.execute('SELECT COUNT(*) as cnt FROM quiz_questions WHERE mavzu_id=?',(mid,)).fetchone()['cnt']>0
    bob = conn.execute('SELECT * FROM bobs WHERE id=?',(m['bob_id'],)).fetchone()
    all_mavzu = conn.execute('''SELECT m.id FROM mavzular m JOIN bobs b ON m.bob_id=b.id
        WHERE b.course_slug=? ORDER BY b.sort_order,m.sort_order''',(m['course_slug'],)).fetchall()
    ids = [r['id'] for r in all_mavzu]
    cur_idx = ids.index(mid) if mid in ids else -1
    user_id = session.get('user_id')
    prog = {}
    if user_id:
        row = conn.execute('SELECT * FROM progress WHERE user_id=? AND mavzu_id=?',(user_id,mid)).fetchone()
        if row: prog = dict(row)
    conn.close()
    # Pick video: try exact lang, then fallback to any available
    def pick_video(m, lang):
        m_dict = dict(m)
        # Try exact lang column first
        for key in [f'video_url_{lang}', 'video_url_uz', 'video_url', 'video_url_ru', 'video_url_en']:
            v = m_dict.get(key) or ''
            if str(v).strip():
                return str(v).strip()
        return ''

    chosen_video = pick_video(m, lang)
    m_dict = dict(m)

    return jsonify({'id':m['id'],
                    'title': m_dict.get(f'title_{db_lang}') or m_dict.get('title_uz',''),
                    'content': m_dict.get(f'content_{db_lang}') or m_dict.get('content_uz') or '',
                    'code_example': m_dict.get('code_example') or '',
                    'video_url': chosen_video,
                    'video_url_uz': m_dict.get('video_url_uz') or m_dict.get('video_url') or '',
                    'video_url_ru': m_dict.get('video_url_ru') or '',
                    'video_url_en': m_dict.get('video_url_en') or '',
                    'course_slug':m['course_slug'],
                    'bob_title': dict(bob).get(f'title_{db_lang}') or dict(bob).get('title_uz','') if bob else '',
                    'has_video': bool(chosen_video),
                    'has_code': bool(m_dict.get('code_example')),
                    'has_quiz':has_quiz,'completed':prog.get('completed',0),
                    'quiz_score':prog.get('quiz_score',-1),'points_reward': m_dict.get('points_reward',10),
                    'prev_id':ids[cur_idx-1] if cur_idx>0 else None,
                    'next_id':ids[cur_idx+1] if cur_idx<len(ids)-1 else None})

@app.route('/api/lesson/<int:mid>/quiz')
def api_lesson_quiz(mid):
    _lang = session.get('lang','uz'); lang = _lang if _lang in ('uz','ru') else 'uz'
    conn = get_db()
    qs = conn.execute('SELECT * FROM quiz_questions WHERE mavzu_id=?',(mid,)).fetchall()
    conn.close()
    result = []
    for q in qs:
        try: opts = json.loads(q[f'options_{lang}'] or q['options_uz'])
        except: opts = json.loads(q['options_uz'])
        result.append({'id':q['id'],'question':q[f'question_{lang}'] or q['question_uz'],
                       'options':opts,'correct':q['correct_idx'],
                       'explanation':q[f'explanation_{lang}'] or q['explanation_uz'] or ''})
    return jsonify({'questions':result})

@app.route('/api/progress/complete', methods=['POST'])
@login_required
def api_complete():
    d = request.get_json()
    mid = d.get('mavzu_id'); quiz_score = d.get('quiz_score',-1)
    code_submitted = d.get('code_submitted',0); course_slug = d.get('course_slug','')
    now = datetime.now().isoformat()
    conn = get_db()
    existing = conn.execute('SELECT * FROM progress WHERE user_id=? AND mavzu_id=?',(session['user_id'],mid)).fetchone()
    conn.execute('''INSERT INTO progress (user_id,mavzu_id,course_slug,completed,quiz_score,code_submitted,completed_at)
        VALUES (?,?,?,1,?,?,?)
        ON CONFLICT(user_id,mavzu_id) DO UPDATE SET completed=1,quiz_score=?,code_submitted=?,completed_at=?''',
        (session['user_id'],mid,course_slug,quiz_score,code_submitted,now,quiz_score,code_submitted,now))
    conn.commit()
    mavzu = conn.execute('SELECT points_reward FROM mavzular WHERE id=?',(mid,)).fetchone()
    conn.close()
    if not existing or not existing['completed']:
        pts = mavzu['points_reward'] if mavzu else 10
        if quiz_score >= 80: pts += 5
        if code_submitted: pts += 5
        uid = session['user_id']
        add_points(uid, pts, f'Dars #{mid} bajarildi')
        update_streak(uid)
        try:
            conn3 = get_db()
            tm3 = conn3.execute(
                "SELECT tm.id, tm.team_id FROM tournament_members tm JOIN tournaments t ON tm.tournament_id=t.id "
                "WHERE tm.user_id=? AND t.status='active' LIMIT 1",(uid,)).fetchone()
            if tm3:
                conn3.execute('UPDATE tournament_members SET points_earned=points_earned+? WHERE id=?',(pts,tm3['id']))
                conn3.execute('UPDATE tournament_teams SET total_points=total_points+? WHERE id=?',(pts,tm3['team_id']))
                conn3.commit()
            conn3.close()
        except: pass
        return jsonify({'success':True,'points_earned':pts})
    return jsonify({'success':True,'points_earned':0})

@app.route('/api/dashboard')
@login_required
def api_dashboard():
    _lang = session.get('lang','uz'); lang = _lang if _lang in ('uz','ru') else 'uz'
    uid = session['user_id']
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) as c FROM mavzular').fetchone()['c']
    completed = conn.execute('SELECT COUNT(*) as c FROM progress WHERE user_id=? AND completed=1',(uid,)).fetchone()['c']
    scores = conn.execute('SELECT quiz_score FROM progress WHERE user_id=? AND quiz_score>=0',(uid,)).fetchall()
    avg = int(sum(r['quiz_score'] for r in scores)/len(scores)) if scores else 0
    u = conn.execute('SELECT points FROM users WHERE id=?',(uid,)).fetchone()
    courses = conn.execute('SELECT * FROM courses WHERE is_active=1 ORDER BY sort_order').fetchall()
    course_stats = []
    for c in courses:
        ctotal = conn.execute('SELECT COUNT(*) as cnt FROM mavzular WHERE course_slug=?',(c['slug'],)).fetchone()['cnt']
        cdone  = conn.execute('SELECT COUNT(*) as cnt FROM progress WHERE user_id=? AND course_slug=? AND completed=1',(uid,c['slug'])).fetchone()['cnt']
        if cdone>0:
            course_stats.append({'slug':c['slug'],'title':c[f'title_{lang}'],'icon':c['icon'],
                                  'color':c['color'],'completed':cdone,'total':ctotal,
                                  'pct':int((cdone/ctotal)*100) if ctotal else 0})
    friends_c = conn.execute('SELECT COUNT(*) as c FROM friends WHERE user1_id=? OR user2_id=?',(uid,uid)).fetchone()['c']
    pending_req = conn.execute('SELECT COUNT(*) as c FROM friend_requests WHERE to_id=? AND status=?',(uid,'pending')).fetchone()['c']
    unread_msgs = conn.execute('SELECT COUNT(*) as c FROM chat_messages WHERE to_id=? AND is_read=0',(uid,)).fetchone()['c']
    conn.close()
    return jsonify({'total_mavzu':total,'completed':completed,'overall_pct':int((completed/total)*100) if total else 0,
                    'avg_score':avg,'courses_started':len(course_stats),'course_stats':course_stats,
                    'points':u['points'] if u else 0,'friends_count':friends_c,
                    'pending_requests':pending_req,'unread_messages':unread_msgs})

# ─────────────────────────────────────────
# PROFILE API
# ─────────────────────────────────────────
@app.route('/api/profile/<username>')
@login_required
def api_profile(username):
    conn = get_db()
    u = conn.execute('SELECT id FROM users WHERE username=?',(username,)).fetchone()
    conn.close()
    if not u: return jsonify({'error':'Topilmadi'}),404
    try:
        data = get_user_full(u['id'], session.get('user_id'))
        if not data: return jsonify({'error':'Topilmadi'}),404
        return jsonify(data)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': 'Serverda xato', 'detail': str(e)}), 500

@app.route('/api/profile/update', methods=['POST'])
@login_required
def api_profile_update():
    d = request.get_json()
    uid = session['user_id']
    allowed = ['full_name','bio','yt_link','ig_link','tg_link','gh_link','profile_color','active_title','active_frame','yt_followers','ig_followers']
    updates = {k:v for k,v in d.items() if k in allowed}
    if not updates: return jsonify({'success':True})
    # Verify title ownership
    if 'active_title' in updates and updates['active_title']:
        conn = get_db()
        owned = conn.execute('SELECT id FROM user_titles WHERE user_id=? AND title_key=?',
                             (uid,updates['active_title'])).fetchone()
        conn.close()
        if not owned: return jsonify({'success':False,'error':'Bu unvon sizda yo\'q'})
    sets = ','.join(f'{k}=?' for k in updates)
    vals = list(updates.values()) + [uid]
    conn = get_db()
    conn.execute(f'UPDATE users SET {sets} WHERE id=?',vals)
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/profile/upload-avatar', methods=['POST'])
@login_required
def api_upload_avatar():
    f = request.files.get('avatar')
    if not f: return jsonify({'success':False,'error':'Fayl yo\'q'})
    fname = save_upload(f, UPLOAD_AVATAR_DIR, f'avatar_{session["user_id"]}')
    if not fname: return jsonify({'success':False,'error':'Noto\'g\'ri format'})
    url = f'/assets/avatars/{fname}'
    conn=get_db(); conn.execute('UPDATE users SET avatar=? WHERE id=?',(url,session['user_id']))
    conn.commit(); conn.close()
    return jsonify({'success':True,'url':url})

@app.route('/api/profile/upload-banner', methods=['POST'])
@login_required
def api_upload_banner():
    f = request.files.get('banner')
    if not f: return jsonify({'success':False,'error':'Fayl yo\'q'})
    fname = save_upload(f, UPLOAD_BANNER_DIR, f'banner_{session["user_id"]}')
    if not fname: return jsonify({'success':False,'error':'Noto\'g\'ri format'})
    url = f'/assets/banners/{fname}'
    conn=get_db(); conn.execute('UPDATE users SET banner=? WHERE id=?',(url,session['user_id']))
    conn.commit(); conn.close()
    return jsonify({'success':True,'url':url})

@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    uid = session['user_id']
    d = request.get_json() or {}
    old_pw = d.get('old_password','').strip()
    new_pw = d.get('new_password','').strip()
    if not old_pw or not new_pw:
        return jsonify({'error': 'Barcha maydonlarni to\'ldiring'}), 400
    if len(new_pw) < 6:
        return jsonify({'error': 'Parol kamida 6 ta belgidan iborat bo\'lsin'}), 400
    conn = get_db()
    user = conn.execute('SELECT password FROM users WHERE id=?', (uid,)).fetchone()
    if not user or user['password'] != hashlib.md5(old_pw.encode()).hexdigest():
        conn.close()
        return jsonify({'error': 'Joriy parol noto\'g\'ri'}), 400
    new_hash = hashlib.md5(new_pw.encode()).hexdigest()
    conn.execute('UPDATE users SET password=? WHERE id=?', (new_hash, uid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/profile/delete-account', methods=['DELETE'])
@login_required
def api_delete_account():
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT role FROM users WHERE id=?', (uid,)).fetchone()
    if user and user['role'] == 'admin':
        conn.close()
        return jsonify({'error': 'Admin hisobini o\'chirib bo\'lmaydi'}), 403
    # Delete user data
    for tbl in ['progress','analytics','friend_requests','friends','chat_messages',
                'user_titles','user_inventory','post_likes','post_comments','follows',
                'submissions','posts']:
        try: conn.execute(f'DELETE FROM {tbl} WHERE user_id=?', (uid,))
        except: pass
    conn.execute('DELETE FROM users WHERE id=?', (uid,))
    conn.commit(); conn.close()
    session.clear()
    return jsonify({'success': True})

# ─────────────────────────────────────────
# SOCIAL – FRIENDS
# ─────────────────────────────────────────
@app.route('/api/social/search')
@login_required
def api_social_search():
    q = (request.args.get('q') or '').strip()
    if len(q) < 2: return jsonify([])
    conn = get_db()
    users = conn.execute('''SELECT id,username,full_name,avatar,has_tick,active_title,points
        FROM users WHERE (username LIKE ? OR full_name LIKE ?) AND id!=? LIMIT 20''',
        (f'%{q}%',f'%{q}%',session['user_id'])).fetchall()
    result = []
    for u in users:
        # Check friend status
        uid = session['user_id']
        f = conn.execute('SELECT id FROM friends WHERE (user1_id=? AND user2_id=?) OR (user1_id=? AND user2_id=?)',
                         (uid,u['id'],u['id'],uid)).fetchone()
        r = conn.execute('SELECT status FROM friend_requests WHERE from_id=? AND to_id=?',(uid,u['id'])).fetchone()
        title = conn.execute('SELECT t.label_uz,t.icon FROM user_titles ut JOIN titles t ON ut.title_key=t.key WHERE ut.user_id=? AND t.key=?',
                             (u['id'],u['active_title'])).fetchone() if u['active_title'] else None
        result.append({'id':u['id'],'username':u['username'],'full_name':u['full_name'],
                       'avatar':u['avatar'],'has_tick':u['has_tick'],'points':u['points'],
                       'active_title':{'label':title['label_uz'],'icon':title['icon']} if title else None,
                       'friend_status':'friends' if f else ('pending' if r and r['status']=='pending' else None)})
    conn.close(); return jsonify(result)

@app.route('/api/social/friend-request', methods=['POST'])
@login_required
def api_friend_request():
    to_id = request.get_json().get('to_id')
    if to_id == session['user_id']: return jsonify({'success':False,'error':'O\'zingizga request tashab bo\'lmaydi'})
    conn = get_db()
    try:
        conn.execute('INSERT INTO friend_requests (from_id,to_id) VALUES (?,?)',(session['user_id'],to_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close(); return jsonify({'success':False,'error':'Allaqachon yuborilgan'})
    conn.close()
    # Notify recipient
    sender = conn = get_db()
    s = conn.execute('SELECT full_name,username FROM users WHERE id=?',(session['user_id'],)).fetchone()
    conn.close()
    if s:
        add_notification(to_id,'friend_req',f"👥 Do'stlik so'rovi",
            f"{s['full_name']} (@{s['username']}) do'stlik so'rovi yubordi",
            '/social')
    return jsonify({'success':True})

@app.route('/api/social/accept-friend', methods=['POST'])
@login_required
def api_accept_friend():
    from_id = request.get_json().get('from_id')
    uid = session['user_id']
    conn = get_db()
    req = conn.execute('SELECT * FROM friend_requests WHERE from_id=? AND to_id=? AND status=?',
                       (from_id,uid,'pending')).fetchone()
    if not req: conn.close(); return jsonify({'success':False,'error':'Request topilmadi'})
    conn.execute("UPDATE friend_requests SET status='accepted' WHERE id=?",(req['id'],))
    u1,u2 = min(from_id,uid),max(from_id,uid)
    try: conn.execute('INSERT INTO friends (user1_id,user2_id) VALUES (?,?)',(u1,u2))
    except: pass
    me_row = conn.execute('SELECT full_name,username FROM users WHERE id=?',(uid,)).fetchone()
    conn.commit(); conn.close()
    add_points(uid,10,"Do'st qo'shish")
    add_points(from_id,10,"Do'stlikni qabul qilish")
    if me_row:
        add_notification(from_id,'friend_acc',f"✅ Do'stlik qabul qilindi",
            f"{me_row['full_name']} (@{me_row['username']}) do'stligingizni qabul qildi 🎉",
            f'/profile/{me_row["username"]}')
    return jsonify({'success':True})

@app.route('/api/social/reject-friend', methods=['POST'])
@login_required
def api_reject_friend():
    from_id = request.get_json().get('from_id')
    conn = get_db()
    conn.execute("UPDATE friend_requests SET status='rejected' WHERE from_id=? AND to_id=?",(from_id,session['user_id']))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/social/remove-friend', methods=['POST'])
@login_required
def api_remove_friend():
    other_id = request.get_json().get('user_id')
    uid = session['user_id']
    u1,u2 = min(uid,other_id),max(uid,other_id)
    conn=get_db()
    conn.execute('DELETE FROM friends WHERE user1_id=? AND user2_id=?',(u1,u2))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/social/friends')
@login_required
def api_my_friends():
    uid = session['user_id']
    conn = get_db()
    rows = conn.execute('''SELECT u.id,u.username,u.full_name,u.avatar,u.has_tick,u.active_title,u.points,u.bio
        FROM friends f JOIN users u ON (f.user1_id=u.id OR f.user2_id=u.id)
        WHERE (f.user1_id=? OR f.user2_id=?) AND u.id!=?
        ORDER BY f.created_at DESC''',(uid,uid,uid)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/social/pending-requests')
@login_required
def api_pending_requests():
    uid = session['user_id']
    conn = get_db()
    rows = conn.execute('''SELECT fr.*,u.username,u.full_name,u.avatar,u.has_tick
        FROM friend_requests fr JOIN users u ON fr.from_id=u.id
        WHERE fr.to_id=? AND fr.status='pending' ORDER BY fr.created_at DESC''',(uid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ─────────────────────────────────────────
# CHAT
# ─────────────────────────────────────────
@app.route('/api/chat/conversations')
@login_required
def api_conversations():
    uid = session['user_id']
    conn = get_db()
    # Get all users I have messages with
    convos = conn.execute('''
        SELECT DISTINCT CASE WHEN from_id=? THEN to_id ELSE from_id END as other_id
        FROM chat_messages WHERE from_id=? OR to_id=?''',(uid,uid,uid)).fetchall()
    result = []
    for c in convos:
        oid = c['other_id']
        u = conn.execute('SELECT id,username,full_name,avatar,has_tick,active_title FROM users WHERE id=?',(oid,)).fetchone()
        if not u: continue
        last = conn.execute('''SELECT * FROM chat_messages WHERE
            (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)
            ORDER BY created_at DESC LIMIT 1''',(uid,oid,oid,uid)).fetchone()
        unread = conn.execute('SELECT COUNT(*) as c FROM chat_messages WHERE from_id=? AND to_id=? AND is_read=0',(oid,uid)).fetchone()['c']
        result.append({'user':dict(u),'last_msg':dict(last) if last else None,'unread':unread})
    conn.close()
    result.sort(key=lambda x: x['last_msg']['created_at'] if x['last_msg'] else '', reverse=True)
    return jsonify(result)

@app.route('/api/chat/messages/<int:other_id>')
@login_required
def api_chat_messages(other_id):
    uid = session['user_id']
    since_id = request.args.get('since', 0, type=int)
    conn = get_db()
    q = '''SELECT m.*,u.username,u.full_name,u.avatar FROM chat_messages m
        JOIN users u ON m.from_id=u.id
        WHERE ((m.from_id=? AND m.to_id=?) OR (m.from_id=? AND m.to_id=?))'''
    params = [uid,other_id,other_id,uid]
    if since_id:
        q += ' AND m.id > ?'; params.append(since_id)
    q += ' ORDER BY m.created_at ASC LIMIT 100'
    msgs = conn.execute(q, params).fetchall()
    conn.execute('UPDATE chat_messages SET is_read=1 WHERE from_id=? AND to_id=?',(other_id,uid))
    conn.commit(); conn.close()
    return jsonify([dict(m) for m in msgs])

@app.route('/api/chat/stream/<int:other_id>')
@login_required
def api_chat_stream(other_id):
    """SSE stream for real-time chat"""
    uid = session['user_id']
    import time as _time
    def generate():
        last_id = 0
        # Get latest id first
        conn = get_db()
        row = conn.execute(
            'SELECT MAX(id) as mid FROM chat_messages WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)',
            (uid,other_id,other_id,uid)).fetchone()
        if row and row['mid']: last_id = row['mid']
        conn.close()
        yield f'data: {{"connected":true,"last_id":{last_id}}}\n\n'
        for _ in range(60):  # 60 seconds max connection
            _time.sleep(1)
            try:
                conn = get_db()
                msgs = conn.execute(
                    '''SELECT m.*,u.username,u.full_name,u.avatar FROM chat_messages m
                       JOIN users u ON m.from_id=u.id
                       WHERE ((m.from_id=? AND m.to_id=?) OR (m.from_id=? AND m.to_id=?))
                       AND m.id > ? ORDER BY m.id ASC LIMIT 20''',
                    (uid,other_id,other_id,uid,last_id)).fetchall()
                if msgs:
                    conn.execute('UPDATE chat_messages SET is_read=1 WHERE from_id=? AND to_id=?',(other_id,uid))
                    conn.commit()
                    for m in msgs:
                        last_id = max(last_id, m['id'])
                    import json
                    yield f'data: {json.dumps([dict(m) for m in msgs])}\n\n'
                conn.close()
            except: pass
        yield 'data: {"reconnect":true}\n\n'
    return Response(generate(), mimetype='text/event-stream',
                   headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.route('/api/chat/send', methods=['POST'])
@login_required
def api_chat_send():
    d = request.get_json()
    to_id = d.get('to_id'); content = (d.get('content') or '').strip()
    if not content: return jsonify({'success':False,'error':'Bo\'sh xabar'})
    # Check friendship
    uid = session['user_id']
    conn = get_db()
    f = conn.execute('SELECT id FROM friends WHERE (user1_id=? AND user2_id=?) OR (user1_id=? AND user2_id=?)',
                     (min(uid,to_id),max(uid,to_id),min(uid,to_id),max(uid,to_id))).fetchone()
    if not f: conn.close(); return jsonify({'success':False,'error':'Faqat do\'stlaringiz bilan chat qila olasiz'})
    conn.execute('INSERT INTO chat_messages (from_id,to_id,content) VALUES (?,?,?)',(uid,to_id,content))
    conn.commit()
    msg_id = conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    # Get sender name for notification
    sender = conn.execute('SELECT full_name,username FROM users WHERE id=?',(uid,)).fetchone()
    conn.close()
    # Notify recipient (but not if they're online - we send anyway, SSE handles it)
    if sender:
        sname = sender['full_name'] or sender['username']
        add_notification(to_id,'message',f"💬 {sname} xabar yubordi",
            content[:60] if len(content)>60 else content,
            f'/chat?with={uid}')
    return jsonify({'success':True,'msg_id':msg_id})

# ─────────────────────────────────────────
# STORE
# ─────────────────────────────────────────
@app.route('/api/store/items')
@login_required
def api_store_items():
    _lang = session.get('lang','uz'); lang = _lang if _lang in ('uz','ru') else 'uz'
    conn = get_db()
    # Ensure columns exist before querying
    try: conn.execute('ALTER TABLE store_items ADD COLUMN price_usd REAL DEFAULT 0')
    except: pass
    try: conn.execute('ALTER TABLE store_items ADD COLUMN is_paid INTEGER DEFAULT 0')
    except: pass
    conn.commit()
    items = conn.execute('SELECT * FROM store_items WHERE is_active=1 ORDER BY COALESCE(is_paid,0) DESC, price_points ASC').fetchall()
    uid = session['user_id']
    owned = {r['item_id'] for r in conn.execute('SELECT item_id FROM user_inventory WHERE user_id=?',(uid,)).fetchall()}
    u = conn.execute('SELECT points FROM users WHERE id=?',(uid,)).fetchone()
    result = []
    safe_lang = lang if lang in ('uz','ru') else 'uz'
    for i in items:
        d = dict(i)
        d['name'] = i[f'name_{safe_lang}'] or i['name_uz'] or ''
        d['desc'] = i[f'desc_{safe_lang}'] or i['desc_uz'] or ''
        d['owned'] = i['id'] in owned
        result.append(d)
    conn.close()
    return jsonify({'items':result,'my_points':u['points'] if u else 0})

@app.route('/api/store/buy', methods=['POST'])
@login_required
def api_store_buy():
    item_id = request.get_json().get('item_id')
    uid = session['user_id']
    conn = get_db()
    item = conn.execute('SELECT * FROM store_items WHERE id=? AND is_active=1',(item_id,)).fetchone()
    if not item: conn.close(); return jsonify({'success':False,'error':'Tovar topilmadi'})
    owned = conn.execute('SELECT id FROM user_inventory WHERE user_id=? AND item_id=?',(uid,item_id)).fetchone()
    if owned: conn.close(); return jsonify({'success':False,'error':'Allaqachon sotib olingan'})
    u = conn.execute('SELECT points FROM users WHERE id=?',(uid,)).fetchone()
    if u['points'] < item['price_points']:
        conn.close(); return jsonify({'success':False,'error':'Ochko yetarli emas'})
    conn.execute('UPDATE users SET points=points-? WHERE id=?',(item['price_points'],uid))
    conn.execute('INSERT INTO user_inventory (user_id,item_id) VALUES (?,?)',(uid,item_id))
    conn.execute('INSERT INTO point_log (user_id,delta,reason,ref_id) VALUES (?,?,?,?)',
                 (uid,-item['price_points'],f"Store: {item['name_uz']}",item_id))
    # Auto-apply item effects
    itype = item['item_type']
    iname = item['name_uz'].lower()
    if itype == 'title':
        title_key = 'junior' if 'junior' in iname else 'senior' if 'senior' in iname else iname.replace(' ','_').replace("'",'')
        conn.execute('INSERT OR IGNORE INTO user_titles (user_id,title_key,granted_by) VALUES (?,?,?)',(uid,title_key,0))
        conn.execute('UPDATE users SET active_title=? WHERE id=?',(title_key,uid))
    elif itype == 'cosmetic':
        if 'tasdiqlangan' in iname or 'galochka' in iname or 'tick' in iname:
            conn.execute('UPDATE users SET has_tick=1 WHERE id=?',(uid,))
        # Profile style mapping
        style_map = {'qizil':'style_red','binafsha':'style_purple','oltin':'style_gold','gradient':'style_gradient','neon':'style_neon'}
        for k,v in style_map.items():
            if k in iname:
                conn.execute('UPDATE users SET profile_style=? WHERE id=?',(v,uid)); break
        if 'frame' in iname or 'animatsiyali' in iname:
            conn.execute("UPDATE users SET active_frame=? WHERE id=?",('frame_'+str(item['id']),uid))
    conn.commit(); conn.close()
    return jsonify({'success':True,'itype':itype,'iname':item['name_uz']})

@app.route('/api/store/buy-paid', methods=['POST'])
@login_required
def api_store_buy_paid():
    data = request.get_json(); item_id = data.get('item_id'); uid = session['user_id']
    conn = get_db()
    item = conn.execute('SELECT * FROM store_items WHERE id=? AND is_active=1 AND is_paid=1',(item_id,)).fetchone()
    if not item: conn.close(); return jsonify({'success':False,'error':'Tovar topilmadi'})
    from datetime import datetime, timedelta
    iname = item['name_uz'].lower()
    days = 1 if '1 kun' in iname else 7 if '7 kun' in iname else 30
    u = conn.execute('SELECT premium_until FROM users WHERE id=?',(uid,)).fetchone()
    base = datetime.now()
    try:
        ex = datetime.fromisoformat(u['premium_until']) if u['premium_until'] else base
        if ex > base: base = ex
    except: pass
    new_until = (base + timedelta(days=days)).isoformat()
    conn.execute('UPDATE users SET is_premium=1,premium_until=?,active_title=? WHERE id=?',(new_until,'premium_user',uid))
    conn.execute('INSERT OR IGNORE INTO user_titles (user_id,title_key,granted_by) VALUES (?,?,?)',(uid,'premium_user',0))
    conn.execute('INSERT INTO user_inventory (user_id,item_id) VALUES (?,?)',(uid,item_id))
    conn.commit(); conn.close()
    return jsonify({'success':True,'premium_until':new_until,'days':days})

@app.route('/api/store/watch-ad', methods=['POST'])
@login_required
def api_store_watch_ad():
    data = request.get_json(); reward = data.get('reward','ai'); uid = session['user_id']
    from datetime import datetime, timedelta
    conn = get_db()
    if reward == 'ai':
        until = (datetime.now() + timedelta(hours=1)).isoformat()
        conn.execute('UPDATE users SET ai_unlocked_until=? WHERE id=?',(until,uid))
        conn.commit(); conn.close()
        return jsonify({'success':True,'ai_until':until,'message':'AI 1 soatga ochildi!'})
    else:
        conn.execute('UPDATE users SET points=points+50 WHERE id=?',(uid,))
        conn.execute('INSERT INTO point_log (user_id,delta,reason) VALUES (?,?,?)',(uid,50,'Reklama bonus'))
        conn.commit(); conn.close()
        return jsonify({'success':True,'points':50,'message':'+50 ochko qoshildi!'})

@app.route('/api/store/buy-points-demo', methods=['POST'])
@login_required
def api_store_buy_points_demo():
    """Demo endpoint - in production, integrate with payment processor"""
    uid = session['user_id']
    amount = int((request.get_json() or {}).get('amount', 0))
    if amount not in [100, 500, 1500, 3000]:
        return jsonify({'success': False, 'error': 'Notogri miqdor'})
    conn = get_db()
    conn.execute('UPDATE users SET points=points+? WHERE id=?', (amount, uid))
    conn.execute('INSERT INTO point_log (user_id,delta,reason) VALUES (?,?,?)',
                 (uid, amount, f'Ochko sotib olindi (demo)'))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'points': amount})

@app.route('/api/user/premium-status')
@login_required
def api_premium_status():
    from datetime import datetime; uid = session['user_id']
    conn = get_db()
    u = conn.execute('SELECT is_premium,premium_until,ai_unlocked_until,profile_style FROM users WHERE id=?',(uid,)).fetchone()
    conn.close()
    now = datetime.now()
    premium_active = False; ai_active = False
    try:
        if u['premium_until']: premium_active = datetime.fromisoformat(u['premium_until']) > now
    except: pass
    try:
        if u['ai_unlocked_until']: ai_active = datetime.fromisoformat(u['ai_unlocked_until']) > now
    except: pass
    return jsonify({'is_premium':premium_active,'ai_active':ai_active,
                   'premium_until':u['premium_until'],'ai_until':u['ai_unlocked_until'],'profile_style':u['profile_style']})


@app.route('/api/gifts/send', methods=['POST'])
@login_required
def api_send_gift():
    data = request.get_json(); uid = session['user_id']
    to_username = data.get('to_username'); gift_type = data.get('gift_type')
    gift_value = str(data.get('gift_value','')); message = data.get('message','')[:200]
    conn = get_db()
    target = conn.execute('SELECT id FROM users WHERE username=?',(to_username,)).fetchone()
    if not target: conn.close(); return jsonify({'success':False,'error':'Foydalanuvchi topilmadi'})
    if target['id'] == uid: conn.close(); return jsonify({'success':False,'error':'Ozingizga hadya jonatib bolmaydi'})
    f = conn.execute('SELECT id FROM friends WHERE (user1_id=? AND user2_id=?) OR (user1_id=? AND user2_id=?)',(uid,target['id'],target['id'],uid)).fetchone()
    if not f: conn.close(); return jsonify({'success':False,'error':'Faqat dostlarga hadya jonating'})
    if gift_type == 'points':
        amount = int(gift_value)
        if amount < 10: conn.close(); return jsonify({'success':False,'error':'Minimum 10 ochko'})
        sender = conn.execute('SELECT points FROM users WHERE id=?',(uid,)).fetchone()
        if sender['points'] < amount: conn.close(); return jsonify({'success':False,'error':'Ochko yetarli emas'})
        conn.execute('UPDATE users SET points=points-? WHERE id=?',(amount,uid))
        conn.execute('UPDATE users SET points=points+? WHERE id=?',(amount,target['id']))
        conn.execute('INSERT INTO point_log (user_id,delta,reason) VALUES (?,?,?)',(uid,-amount,f"Hadya @{to_username}"))
        conn.execute('INSERT INTO point_log (user_id,delta,reason) VALUES (?,?,?)',(target['id'],amount,f"Hadya @{session['username']}"))
    elif gift_type == 'premium':
        from datetime import datetime, timedelta
        days = int(gift_value)
        base = datetime.now()
        u_t = conn.execute('SELECT premium_until FROM users WHERE id=?',(target['id'],)).fetchone()
        try:
            ex = datetime.fromisoformat(u_t['premium_until']) if u_t['premium_until'] else base
            if ex > base: base = ex
        except: pass
        new_until = (base + timedelta(days=days)).isoformat()
        conn.execute('UPDATE users SET is_premium=1,premium_until=?,active_title=? WHERE id=?',(new_until,'premium_user',target['id']))
        conn.execute('INSERT OR IGNORE INTO user_titles (user_id,title_key,granted_by) VALUES (?,?,?)',(target['id'],'premium_user',0))
    conn.execute('INSERT INTO gifts (from_user_id,to_user_id,gift_type,gift_value,message) VALUES (?,?,?,?,?)',
                 (uid,target['id'],gift_type,gift_value,message))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/gifts/inbox')
@login_required
def api_gifts_inbox():
    uid = session['user_id']; conn = get_db()
    gifts = conn.execute('''SELECT g.*,u.username as from_username,u.full_name as from_name
        FROM gifts g JOIN users u ON g.from_user_id=u.id
        WHERE g.to_user_id=? ORDER BY g.created_at DESC LIMIT 20''',(uid,)).fetchall()
    conn.close()
    return jsonify([dict(g) for g in gifts])

@app.route('/api/store/boxes')
@login_required
def api_store_boxes():
    _lang = session.get('lang','uz'); lang = _lang if _lang in ('uz','ru') else 'uz'
    conn = get_db()
    boxes = conn.execute('SELECT * FROM mystery_boxes WHERE is_active=1').fetchall()
    uid = session['user_id']
    u = conn.execute('SELECT points FROM users WHERE id=?',(uid,)).fetchone()
    conn.close()
    safe_lang = session.get('lang','uz') if session.get('lang') in ('uz','ru') else 'uz'
    boxes_out = []
    for b in boxes:
        bd = dict(b)
        bd['name'] = bd.get(f'name_{safe_lang}') or bd.get('name_uz') or ''
        boxes_out.append(bd)
    return jsonify({'boxes':boxes_out,'my_points':u['points'] if u else 0})

@app.route('/api/store/open-box', methods=['POST'])
@login_required
def api_open_box():
    box_id = request.get_json().get('box_id')
    uid = session['user_id']
    conn = get_db()
    box = conn.execute('SELECT * FROM mystery_boxes WHERE id=? AND is_active=1',(box_id,)).fetchone()
    if not box: conn.close(); return jsonify({'success':False,'error':'Quti topilmadi'})
    u = conn.execute('SELECT points FROM users WHERE id=?',(uid,)).fetchone()
    if u['points'] < box['price_points']:
        conn.close(); return jsonify({'success':False,'error':'Ochko yetarli emas'})
    
    # Determine reward based on rarity
    rarity = box['rarity']
    reward_type = random.choices(['points','item','title'],weights=[50,35,15])[0]
    reward_points = 0; reward_item_id = None; reward_msg = ''
    
    if reward_type == 'points':
        pts_map = {'common':(20,80),'rare':(50,200),'epic':(100,500),'legendary':(200,1000)}
        lo,hi = pts_map.get(rarity,(20,80))
        reward_points = random.randint(lo,hi)
        reward_msg = f"🎉 {reward_points} ochko yutdingiz!"
        conn.execute('UPDATE users SET points=points+? WHERE id=?',(reward_points,uid))
    elif reward_type == 'item':
        rarity_order = {'common':1,'uncommon':2,'rare':3,'epic':4,'legendary':5}
        rarity_val = rarity_order.get(rarity, 3)
        eligible = [k for k,v in rarity_order.items() if v <= rarity_val]
        ph = ','.join('?'*len(eligible))
        items = conn.execute(f'SELECT * FROM store_items WHERE is_active=1 AND rarity IN ({ph}) ORDER BY RANDOM() LIMIT 1',
                             eligible).fetchall()
        if items:
            item = items[0]
            reward_item_id = item['id']
            reward_msg = f"🎁 '{item['name_uz']}' sovg'a qo'lga kiritdingiz!"
            try: conn.execute('INSERT INTO user_inventory (user_id,item_id) VALUES (?,?)',(uid,item['id']))
            except: pass
    else:
        reward_msg = f"⭐ Bonus {box['price_points']//2} ochko!"
        reward_points = box['price_points']//2
        conn.execute('UPDATE users SET points=points+? WHERE id=?',(reward_points,uid))
    
    conn.execute('UPDATE users SET points=points-? WHERE id=?',(box['price_points'],uid))
    conn.execute('INSERT INTO box_openings (user_id,box_id,reward_item_id,reward_points) VALUES (?,?,?,?)',
                 (uid,box_id,reward_item_id,reward_points))
    conn.commit(); conn.close()
    return jsonify({'success':True,'reward_msg':reward_msg,'reward_points':reward_points,'reward_item_id':reward_item_id})

@app.route('/api/inventory')
@login_required
def api_inventory():
    uid = session['user_id']
    _lang = session.get('lang','uz'); lang = _lang if _lang in ('uz','ru') else 'uz'
    conn = get_db()
    rows = conn.execute('''SELECT si.*,ui.purchased_at FROM user_inventory ui
        JOIN store_items si ON ui.item_id=si.id WHERE ui.user_id=?''',(uid,)).fetchall()
    conn.close()
    return jsonify([{**dict(r),'name':r[f'name_{lang}'],'desc':r[f'desc_{lang}']} for r in rows])

# ─────────────────────────────────────────
# GROUPS / CHANNELS
# ─────────────────────────────────────────
@app.route('/api/groups')
@login_required
def api_groups():
    conn = get_db()
    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'popular')
    gtype = request.args.get('type', 'all')
    order_map = {'popular':'g.member_count DESC','newest':'g.created_at DESC','oldest':'g.created_at ASC'}
    order = order_map.get(sort, 'g.member_count DESC')
    where = 'WHERE g.is_public=1'
    params = []
    if q:
        where += ' AND (g.name LIKE ? OR g.description LIKE ?)'
        params += ['%'+q+'%', '%'+q+'%']
    if gtype in ('group', 'channel'):
        where += ' AND g.group_type=?'
        params.append(gtype)
    sql = 'SELECT g.*,u.username as owner_name,u.avatar as owner_avatar FROM groups g JOIN users u ON g.owner_id=u.id ' + where + ' ORDER BY ' + order + ' LIMIT 100'
    groups = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(g) for g in groups])

@app.route('/api/groups/my')
@login_required
def api_my_groups():
    uid = session['user_id']
    conn = get_db()
    groups = conn.execute('''SELECT g.*,gm.role FROM group_members gm
        JOIN groups g ON gm.group_id=g.id WHERE gm.user_id=? ORDER BY gm.joined_at DESC''',(uid,)).fetchall()
    conn.close()
    return jsonify([dict(g) for g in groups])

@app.route('/api/groups/create', methods=['POST'])
@login_required
def api_create_group():
    d = request.get_json() or {}
    name = (d.get('name') or '').strip()
    group_type = d.get('group_type','group')
    if not name: return jsonify({'success':False,'error':'Nom kiriting'})
    import re as _re
    base = _re.sub(r'[^a-z0-9]', '', name.lower().replace(' ','-'))[:20] or 'group'
    slug = base + '-' + str(random.randint(1000,9999))
    uid = session['user_id']
    conn = get_db()
    try:
        # Try with group_category first
        try:
            conn.execute('''INSERT INTO groups (name,slug,description,group_type,owner_id,bio,is_public,group_category)
                VALUES (?,?,?,?,?,?,?,?)''',(name,slug,d.get('description',''),group_type,uid,d.get('bio',''),
                 int(d.get('is_public',1)), d.get('group_category','normal')))
        except Exception:
            # Fallback without group_category if column missing
            conn.execute('''INSERT INTO groups (name,slug,description,group_type,owner_id,bio,is_public)
                VALUES (?,?,?,?,?,?,?)''',(name,slug,d.get('description',''),group_type,uid,d.get('bio',''),
                 int(d.get('is_public',1))))
        gid = conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']
        conn.execute('INSERT INTO group_members (group_id,user_id,role) VALUES (?,?,?)',(gid,uid,'owner'))
        # Pre-generate invite code so it's instant when admin needs it
        invite_code = _gen_invite_code()
        try:
            conn.execute('UPDATE groups SET invite_code=? WHERE id=?', (invite_code, gid))
        except Exception:
            pass
        conn.commit(); conn.close()
        return jsonify({'success':True,'slug':slug})
    except Exception as e:
        conn.close(); return jsonify({'success':False,'error':str(e)})

@app.route('/api/groups/<slug>')
@login_required
def api_group_detail(slug):
    conn = get_db()
    g = conn.execute('SELECT g.*,u.username as owner_name FROM groups g JOIN users u ON g.owner_id=u.id WHERE g.slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'error':'Topilmadi'}),404
    members = conn.execute('''SELECT u.id,u.username,u.full_name,u.avatar,u.has_tick,gm.role
        FROM group_members gm JOIN users u ON gm.user_id=u.id WHERE gm.group_id=? LIMIT 20''',(g['id'],)).fetchall()
    uid = session['user_id']
    is_member = conn.execute('SELECT id FROM group_members WHERE group_id=? AND user_id=?',(g['id'],uid)).fetchone()
    role = None
    if is_member:
        role_row = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?',(g['id'],uid)).fetchone()
        role = role_row['role'] if role_row else None
    conn.close()
    return jsonify({**dict(g),'members':[dict(m) for m in members],'is_member':bool(is_member),'my_role':role})

@app.route('/api/groups/<slug>/join', methods=['POST'])
@login_required
def api_join_group(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'success':False,'error':'Topilmadi'})
    try:
        conn.execute('INSERT INTO group_members (group_id,user_id) VALUES (?,?)',(g['id'],uid))
        conn.execute('UPDATE groups SET member_count=member_count+1 WHERE id=?',(g['id'],))
        conn.commit()
    except: pass
    conn.close(); return jsonify({'success':True})

@app.route('/api/groups/<slug>/leave', methods=['POST'])
@login_required
def api_leave_group(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id,owner_id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'success':False})
    if g['owner_id'] == uid: conn.close(); return jsonify({'success':False,'error':'Owner chiqib keta olmaydi'})
    conn.execute('DELETE FROM group_members WHERE group_id=? AND user_id=?',(g['id'],uid))
    conn.execute('UPDATE groups SET member_count=MAX(member_count-1,0) WHERE id=?',(g['id'],))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/groups/<slug>/update', methods=['POST'])
@login_required
def api_update_group(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id,owner_id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'success':False,'error':'Topilmadi'})
    role = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?',(g['id'],uid)).fetchone()
    if not role or role['role'] not in ('owner','admin'):
        conn.close(); return jsonify({'success':False,'error':'Ruxsat yo\'q'})
    d = request.get_json() or {}
    updates = []
    params = []
    if 'name' in d: updates.append('name=?'); params.append(d['name'])
    if 'bio' in d: updates.append('bio=?'); params.append(d['bio'])
    if 'is_public' in d: updates.append('is_public=?'); params.append(int(d['is_public']))
    if updates:
        params.append(g['id'])
        conn.execute('UPDATE groups SET '+','.join(updates)+' WHERE id=?', params)
        conn.commit()
    conn.close()
    return jsonify({'success':True})

@app.route('/api/groups/<slug>/delete', methods=['POST'])
@login_required
def api_delete_group(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id,owner_id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'success':False,'error':'Topilmadi'})
    if g['owner_id'] != uid:
        conn.close(); return jsonify({'success':False,'error':'Faqat owner o\'chira oladi'})
    conn.execute('DELETE FROM group_messages WHERE group_id=?',(g['id'],))
    conn.execute('DELETE FROM group_members WHERE group_id=?',(g['id'],))
    conn.execute('DELETE FROM groups WHERE id=?',(g['id'],))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/groups/<slug>/avatar', methods=['POST'])
@login_required
def api_group_avatar(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id,owner_id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'success':False,'error':'Topilmadi'})
    role = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?',(g['id'],uid)).fetchone()
    if not role or role['role'] not in ('owner','admin'):
        conn.close(); return jsonify({'success':False,'error':'Ruxsat yo\'q'})
    if 'avatar' not in request.files:
        conn.close(); return jsonify({'success':False,'error':'Fayl topilmadi'})
    f = request.files['avatar']
    ext = os.path.splitext(f.filename)[1] if f.filename else '.jpg'
    fname = 'group_'+slug+'_avatar'+ext
    fpath = os.path.join('assets','avatars',fname)
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    f.save(fpath)
    url = '/'+fpath
    conn.execute('UPDATE groups SET avatar=? WHERE id=?',(url,g['id']))
    conn.commit(); conn.close()
    return jsonify({'success':True,'url':url})


@app.route('/api/groups/<slug>/messages')
@login_required
def api_group_messages(slug):
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify([])
    after = request.args.get('after', 0, type=int)
    if after:
        msgs = conn.execute('''SELECT m.*,u.username,u.full_name,u.avatar,u.has_tick,u.active_title
            FROM group_messages m JOIN users u ON m.user_id=u.id
            WHERE m.group_id=? AND m.id>? ORDER BY m.created_at ASC LIMIT 50''',(g['id'],after)).fetchall()
    else:
        msgs = conn.execute('''SELECT m.*,u.username,u.full_name,u.avatar,u.has_tick,u.active_title
            FROM group_messages m JOIN users u ON m.user_id=u.id
            WHERE m.group_id=? ORDER BY m.created_at DESC LIMIT 60''',(g['id'],)).fetchall()
        msgs = list(reversed(msgs))
    conn.close()
    return jsonify([dict(m) for m in msgs])

@app.route('/api/groups/<slug>/stream')
@login_required
def api_group_stream(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'error':'Not found'}), 404
    gid = g['id']
    conn.close()
    import json as _json
    def generate():
        last_id = 0
        try:
            c = get_db()
            row = c.execute('SELECT COALESCE(MAX(id),0) as m FROM group_messages WHERE group_id=?',(gid,)).fetchone()
            last_id = row['m'] or 0
            c.close()
        except: pass
        while True:
            try:
                c = get_db()
                rows = c.execute('''SELECT m.id,m.group_id,m.user_id,m.content,m.msg_type,m.media_url,m.created_at,
                    u.username,u.full_name,u.avatar,u.has_tick
                    FROM group_messages m JOIN users u ON m.user_id=u.id
                    WHERE m.group_id=? AND m.id>? ORDER BY m.id ASC LIMIT 10''',(gid,last_id)).fetchall()
                c.close()
                for r in rows:
                    last_id = r['id']
                    yield f'data: {_json.dumps(dict(r), ensure_ascii=False, default=str)}\n\n'
                yield ': ping\n\n'
            except GeneratorExit:
                return
            except Exception:
                pass
            _time.sleep(2)
    from flask import Response
    return Response(generate(), mimetype='text/event-stream',
        headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no','Connection':'keep-alive'})

@app.route('/api/groups/<slug>/send', methods=['POST'])
@login_required
def api_group_send(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'success':False})
    is_member = conn.execute('SELECT id,is_muted,is_banned FROM group_members WHERE group_id=? AND user_id=?',(g['id'],uid)).fetchone()
    if not is_member: conn.close(); return jsonify({'success':False,'error':'Avval guruhga qo\'shiling'})
    if is_member['is_banned']: conn.close(); return jsonify({'success':False,'error':'Siz ban qilingansiz'})
    if is_member['is_muted']: conn.close(); return jsonify({'success':False,'error':'Siz jim qilingansiz (mute)'})
    content = (request.get_json().get('content') or '').strip()
    if not content: conn.close(); return jsonify({'success':False})
    conn.execute('INSERT INTO group_messages (group_id,user_id,content) VALUES (?,?,?)',(g['id'],uid,content))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/groups/<slug>/upload', methods=['POST'])
@login_required
def api_group_upload(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id,owner_id FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'success':False})
    
    upload_type = request.form.get('type','avatar')
    f = request.files.get('file')
    if not f: conn.close(); return jsonify({'success':False,'error':'Fayl yo\'q'})
    
    fname = save_upload(f, UPLOAD_GROUP_DIR, f'group_{g["id"]}_{upload_type}')
    if not fname: conn.close(); return jsonify({'success':False,'error':'Noto\'g\'ri format'})
    url = f'/assets/group_media/{fname}'
    
    field = 'avatar' if upload_type=='avatar' else 'banner'
    conn.execute(f'UPDATE groups SET {field}=? WHERE id=?',(url,g['id']))
    conn.commit(); conn.close()
    return jsonify({'success':True,'url':url})

# ─────────────────────────────────────────
# ADMIN API (extended)
# ─────────────────────────────────────────
@app.route('/api/admin/stats')
@admin_required
def api_admin_stats():
    conn = get_db()
    def safe(fn, default=0):
        try: return fn()
        except: return default
    users        = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM users WHERE role='student'").fetchone()['c'])
    courses      = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM courses WHERE is_active=1").fetchone()['c'])
    lessons      = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM mavzular").fetchone()['c'])
    views        = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM analytics WHERE event_type='page_lesson'").fetchone()['c'])
    completions  = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM progress WHERE completed=1").fetchone()['c'])
    total_pts    = safe(lambda: conn.execute("SELECT SUM(points) as s FROM users").fetchone()['s'] or 0)
    store_buys   = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM user_inventory").fetchone()['c'])
    groups_c     = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM groups").fetchone()['c'])
    premium_users= safe(lambda: conn.execute("SELECT COUNT(*) as c FROM users WHERE is_premium=1").fetchone()['c'])
    problems_solved = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM submissions WHERE status='accepted'").fetchone()['c'])
    blog_posts   = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM posts WHERE is_active=1").fetchone()['c'])
    active_today = safe(lambda: conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM analytics WHERE DATE(created_at)=DATE('now')").fetchone()['c'])
    active_week  = safe(lambda: conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM analytics WHERE created_at >= datetime('now','-7 days')").fetchone()['c'])
    new_users_week  = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM users WHERE created_at >= datetime('now','-7 days')").fetchone()['c'])
    new_users_today = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM users WHERE DATE(created_at)=DATE('now')").fetchone()['c'])
    chat_msgs    = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM chat_messages").fetchone()['c'])
    total_friends= safe(lambda: conn.execute("SELECT COUNT(*) as c FROM friends").fetchone()['c'])
    open_tickets = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM support_tickets WHERE status='open'").fetchone()['c'])
    games_count  = safe(lambda: conn.execute("SELECT COUNT(*) as c FROM games WHERE is_active=1").fetchone()['c'])
    streak_today = safe(lambda: conn.execute("SELECT COUNT(DISTINCT user_id) as c FROM streak_log WHERE activity_date=DATE('now')").fetchone()['c'])
    daily      = safe(lambda: list(conn.execute('''SELECT DATE(completed_at) as day,COUNT(*) as cnt FROM progress WHERE completed=1 AND completed_at IS NOT NULL GROUP BY DATE(completed_at) ORDER BY day DESC LIMIT 7''').fetchall()), [])
    popular    = safe(lambda: list(conn.execute('''SELECT c.title_uz as title,c.icon,COUNT(p.id) as cnt FROM courses c LEFT JOIN progress p ON c.slug=p.course_slug AND p.completed=1 WHERE c.is_active=1 GROUP BY c.slug ORDER BY cnt DESC''').fetchall()), [])
    top_users  = safe(lambda: list(conn.execute("SELECT username,full_name,points FROM users ORDER BY points DESC LIMIT 5").fetchall()), [])
    reg_daily  = safe(lambda: list(conn.execute('''SELECT DATE(created_at) as day, COUNT(*) as cnt FROM users WHERE created_at >= datetime('now','-7 days') GROUP BY DATE(created_at) ORDER BY day''').fetchall()), [])
    conn.close()
    return jsonify({'users':users,'courses':courses,'lessons':lessons,'views':views,
                    'completions':completions,'total_points':total_pts,'store_buys':store_buys,
                    'groups':groups_c,'premium_users':premium_users,'problems_solved':problems_solved,
                    'blog_posts':blog_posts,'active_today':active_today,'active_week':active_week,
                    'new_users_week':new_users_week,'new_users_today':new_users_today,
                    'chat_msgs':chat_msgs,'total_friends':total_friends,'open_tickets':open_tickets,
                    'games_count':games_count,'streak_today':streak_today,
                    'daily':[dict(r) for r in daily],'popular':[dict(r) for r in popular],
                    'top_users':[dict(r) for r in top_users],
                    'reg_daily':[dict(r) for r in reg_daily]})
def api_admin_users():
    conn = get_db()
    users = conn.execute('SELECT id,username,full_name,email,role,created_at,points,has_tick,active_title FROM users ORDER BY created_at DESC').fetchall()
    conn.close(); return jsonify([dict(u) for u in users])

@app.route('/api/admin/users/<int:uid>', methods=['DELETE'])
@admin_required
def api_admin_delete_user(uid):
    conn=get_db(); conn.execute("DELETE FROM users WHERE id=? AND role!='admin'",(uid,))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/grant-tick', methods=['POST'])
@admin_required
def api_admin_grant_tick():
    d = request.get_json()
    uid = d.get('user_id'); val = int(d.get('value',1))
    conn=get_db(); conn.execute('UPDATE users SET has_tick=? WHERE id=?',(val,uid))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/grant-title', methods=['POST'])
@admin_required
def api_admin_grant_title():
    d = request.get_json()
    uid = d.get('user_id'); title_key = d.get('title_key')
    conn=get_db()
    conn.execute('INSERT OR IGNORE INTO user_titles (user_id,title_key,granted_by) VALUES (?,?,?)',
                 (uid,title_key,session['user_id']))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/titles')
@admin_required
def api_admin_titles():
    conn=get_db(); titles=conn.execute('SELECT * FROM titles').fetchall(); conn.close()
    return jsonify([dict(t) for t in titles])

@app.route('/api/admin/courses', methods=['GET'])
@admin_required
def api_admin_courses():
    conn = get_db()
    courses = conn.execute('SELECT * FROM courses ORDER BY sort_order').fetchall()
    result = []
    for c in courses:
        bobs = conn.execute('SELECT COUNT(*) as cnt FROM bobs WHERE course_slug=?',(c['slug'],)).fetchone()['cnt']
        mavzu = conn.execute('SELECT COUNT(*) as cnt FROM mavzular WHERE course_slug=?',(c['slug'],)).fetchone()['cnt']
        d=dict(c); d['bob_count']=bobs; d['mavzu_count']=mavzu; result.append(d)
    conn.close(); return jsonify(result)

@app.route('/api/admin/courses', methods=['POST'])
@admin_required
def api_admin_create_course():
    d = request.get_json()
    conn = get_db()
    try:
        conn.execute('''INSERT INTO courses
            (slug,title_uz,title_ru,desc_uz,desc_ru,icon,color,level_uz,level_ru,duration,category_uz,category_ru,sort_order)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (d['slug'],d['title_uz'],d.get('title_ru',d['title_uz']),d.get('desc_uz',''),d.get('desc_ru',''),
             d.get('icon','📚'),d.get('color','#1B2A4A'),d.get('level_uz','Boshlangich'),d.get('level_ru','Начальный'),
             d.get('duration','10 soat'),d.get('category_uz','Dasturlash'),d.get('category_ru','Программирование'),d.get('sort_order',99)))
        conn.commit(); conn.close(); return jsonify({'success':True})
    except sqlite3.IntegrityError: conn.close(); return jsonify({'success':False,'error':'Bu slug band'})

@app.route('/api/admin/courses/<slug>', methods=['PUT'])
@admin_required
def api_admin_update_course(slug):
    d = request.get_json(); conn = get_db()
    conn.execute('''UPDATE courses SET title_uz=?,title_ru=?,desc_uz=?,desc_ru=?,icon=?,color=?,
        level_uz=?,level_ru=?,duration=?,category_uz=?,category_ru=?,sort_order=?,is_active=? WHERE slug=?''',
        (d.get('title_uz'),d.get('title_ru'),d.get('desc_uz'),d.get('desc_ru'),d.get('icon'),d.get('color'),
         d.get('level_uz'),d.get('level_ru'),d.get('duration'),d.get('category_uz'),d.get('category_ru'),
         d.get('sort_order',0),d.get('is_active',1),slug))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/courses/<slug>', methods=['DELETE'])
@admin_required
def api_admin_delete_course(slug):
    conn=get_db(); conn.execute('UPDATE courses SET is_active=0 WHERE slug=?',(slug,))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/bobs/<slug>')
@admin_required
def api_admin_bobs(slug):
    conn=get_db()
    bobs=conn.execute('SELECT * FROM bobs WHERE course_slug=? ORDER BY sort_order',(slug,)).fetchall()
    result=[]
    for b in bobs:
        cnt=conn.execute('SELECT COUNT(*) as c FROM mavzular WHERE bob_id=?',(b['id'],)).fetchone()['c']
        d=dict(b); d['mavzu_count']=cnt; result.append(d)
    conn.close(); return jsonify(result)

@app.route('/api/admin/bobs', methods=['POST'])
@admin_required
def api_admin_create_bob():
    d=request.get_json(); conn=get_db()
    conn.execute('INSERT INTO bobs (course_slug,title_uz,title_ru,sort_order) VALUES (?,?,?,?)',
                 (d['course_slug'],d['title_uz'],d.get('title_ru',d['title_uz']),d.get('sort_order',99)))
    conn.commit()
    bid=conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    conn.close(); return jsonify({'success':True,'id':bid})

@app.route('/api/admin/bobs/<int:bid>', methods=['PUT'])
@admin_required
def api_admin_update_bob(bid):
    d=request.get_json(); conn=get_db()
    conn.execute('UPDATE bobs SET title_uz=?,title_ru=?,sort_order=? WHERE id=?',
                 (d['title_uz'],d.get('title_ru',d['title_uz']),d.get('sort_order',0),bid))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/bobs/<int:bid>', methods=['DELETE'])
@admin_required
def api_admin_delete_bob(bid):
    conn=get_db()
    conn.execute('DELETE FROM quiz_questions WHERE mavzu_id IN (SELECT id FROM mavzular WHERE bob_id=?)',(bid,))
    conn.execute('DELETE FROM mavzular WHERE bob_id=?',(bid,))
    conn.execute('DELETE FROM bobs WHERE id=?',(bid,))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/mavzular/<int:bid>')
@admin_required
def api_admin_mavzular(bid):
    conn=get_db()
    mavzular=conn.execute('SELECT * FROM mavzular WHERE bob_id=? ORDER BY sort_order',(bid,)).fetchall()
    result=[]
    for m in mavzular:
        qcnt=conn.execute('SELECT COUNT(*) as c FROM quiz_questions WHERE mavzu_id=?',(m['id'],)).fetchone()['c']
        d=dict(m); d['quiz_count']=qcnt; result.append(d)
    conn.close(); return jsonify(result)

@app.route('/api/admin/mavzular', methods=['POST'])
@admin_required
def api_admin_create_mavzu():
    d=request.get_json(); conn=get_db()
    conn.execute('''INSERT INTO mavzular (bob_id,course_slug,title_uz,title_ru,content_uz,content_ru,code_example,video_url,video_url_uz,video_url_ru,video_url_en,sort_order,points_reward)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (d['bob_id'],d['course_slug'],d['title_uz'],d.get('title_ru',d['title_uz']),
         d.get('content_uz',''),d.get('content_ru',''),d.get('code_example',''),
         d.get('video_url',''),d.get('video_url_uz',''),d.get('video_url_ru',''),
         d.get('video_url_en',''),d.get('sort_order',99),d.get('points_reward',10)))
    conn.commit()
    mid=conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    conn.close(); return jsonify({'success':True,'id':mid})

@app.route('/api/admin/mavzular/<int:mid>', methods=['PUT'])
@admin_required
def api_admin_update_mavzu(mid):
    d=request.get_json(); conn=get_db()
    conn.execute('''UPDATE mavzular SET title_uz=?,title_ru=?,content_uz=?,content_ru=?,
        code_example=?,video_url=?,video_url_uz=?,video_url_ru=?,video_url_en=?,sort_order=?,points_reward=? WHERE id=?''',
        (d.get('title_uz'),d.get('title_ru'),d.get('content_uz',''),d.get('content_ru',''),
         d.get('code_example',''),d.get('video_url',''),d.get('video_url_uz',''),
         d.get('video_url_ru',''),d.get('video_url_en',''),d.get('sort_order',0),d.get('points_reward',10),mid))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/mavzular/<int:mid>', methods=['DELETE'])
@admin_required
def api_admin_delete_mavzu(mid):
    conn=get_db()
    conn.execute('DELETE FROM quiz_questions WHERE mavzu_id=?',(mid,))
    conn.execute('DELETE FROM mavzular WHERE id=?',(mid,))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/quiz/<int:mid>')
@admin_required
def api_admin_quiz(mid):
    conn=get_db(); qs=conn.execute('SELECT * FROM quiz_questions WHERE mavzu_id=?',(mid,)).fetchall()
    conn.close(); return jsonify([dict(q) for q in qs])

@app.route('/api/admin/quiz', methods=['POST'])
@admin_required
def api_admin_create_quiz():
    d=request.get_json()
    opts_uz=json.dumps(d.get('options_uz',[]),ensure_ascii=False)
    opts_ru=json.dumps(d.get('options_ru',[]),ensure_ascii=False)
    conn=get_db()
    conn.execute('''INSERT INTO quiz_questions
        (mavzu_id,question_uz,question_ru,options_uz,options_ru,correct_idx,explanation_uz,explanation_ru)
        VALUES (?,?,?,?,?,?,?,?)''',
        (d['mavzu_id'],d['question_uz'],d.get('question_ru',d['question_uz']),
         opts_uz,opts_ru,d['correct_idx'],d.get('explanation_uz',''),d.get('explanation_ru','')))
    conn.commit()
    qid=conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    conn.close(); return jsonify({'success':True,'id':qid})

@app.route('/api/admin/quiz/<int:qid>', methods=['PUT'])
@admin_required
def api_admin_update_quiz(qid):
    d=request.get_json()
    opts_uz=json.dumps(d.get('options_uz',[]),ensure_ascii=False)
    opts_ru=json.dumps(d.get('options_ru',[]),ensure_ascii=False)
    conn=get_db()
    conn.execute('''UPDATE quiz_questions SET question_uz=?,question_ru=?,options_uz=?,options_ru=?,
        correct_idx=?,explanation_uz=?,explanation_ru=? WHERE id=?''',
        (d['question_uz'],d.get('question_ru',d['question_uz']),opts_uz,opts_ru,
         d['correct_idx'],d.get('explanation_uz',''),d.get('explanation_ru',''),qid))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/quiz/<int:qid>', methods=['DELETE'])
@admin_required
def api_admin_delete_quiz(qid):
    conn=get_db(); conn.execute('DELETE FROM quiz_questions WHERE id=?',(qid,))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/upload-video/<int:mid>', methods=['POST'])
@admin_required
def api_admin_upload_video(mid):
    f = request.files.get('video')
    lang = request.form.get('lang', 'uz')  # uz | ru | en
    if not f: return jsonify({'success':False,'error':'Fayl yo\'q'})
    ext = f.filename.rsplit('.',1)[-1].lower()
    if ext not in ALLOWED_VIDEO: return jsonify({'success':False,'error':'Noto\'g\'ri format'})
    fname = secure_filename(f'{mid}_{lang}_{int(datetime.now().timestamp())}.{ext}')
    f.save(os.path.join(UPLOAD_VIDEO_DIR, fname))
    url = f'/assets/videos/{fname}'
    conn = get_db()
    # Save to lang-specific column AND main video_url (set main if empty)
    if lang == 'uz':
        conn.execute('UPDATE mavzular SET video_url=?, video_url_uz=? WHERE id=?', (url, url, mid))
    elif lang == 'ru':
        # Also set main video_url if currently empty
        conn.execute('UPDATE mavzular SET video_url_ru=? WHERE id=?', (url, mid))
        existing = conn.execute('SELECT video_url FROM mavzular WHERE id=?', (mid,)).fetchone()
        if not (existing and existing['video_url']):
            conn.execute('UPDATE mavzular SET video_url=? WHERE id=?', (url, mid))
    elif lang == 'en':
        conn.execute('UPDATE mavzular SET video_url_en=? WHERE id=?', (url, mid))
        existing = conn.execute('SELECT video_url FROM mavzular WHERE id=?', (mid,)).fetchone()
        if not (existing and existing['video_url']):
            conn.execute('UPDATE mavzular SET video_url=? WHERE id=?', (url, mid))
    else:
        conn.execute('UPDATE mavzular SET video_url=?, video_url_uz=? WHERE id=?', (url, url, mid))
    conn.commit(); conn.close()
    return jsonify({'success':True, 'video_url':url, 'lang':lang})

@app.route('/api/admin/store/items', methods=['GET'])
@admin_required
def api_admin_store_items():
    conn=get_db(); items=conn.execute('SELECT * FROM store_items ORDER BY id').fetchall(); conn.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/admin/store/items', methods=['POST'])
@admin_required
def api_admin_add_store_item():
    d=request.get_json(); conn=get_db()
    conn.execute('''INSERT INTO store_items (name_uz,name_ru,desc_uz,desc_ru,item_type,price_points,rarity)
        VALUES (?,?,?,?,?,?,?)''',
        (d['name_uz'],d.get('name_ru',d['name_uz']),d.get('desc_uz',''),d.get('desc_ru',''),
         d.get('item_type','cosmetic'),d.get('price_points',100),d.get('rarity','common')))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/store/items/<int:iid>', methods=['PUT'])
@admin_required
def api_admin_update_store_item(iid):
    d=request.get_json() or {}; conn=get_db()
    fields=[]; vals=[]
    for col in ('name_uz','name_ru','desc_uz','desc_ru','item_type','price_points','rarity','is_active'):
        if col in d:
            fields.append(f'{col}=?'); vals.append(d[col])
    if fields:
        vals.append(iid)
        conn.execute(f"UPDATE store_items SET {','.join(fields)} WHERE id=?", vals)
        conn.commit()
    conn.close(); return jsonify({'success':True})

@app.route('/api/admin/store/items/<int:iid>', methods=['DELETE'])
@admin_required
def api_admin_delete_store_item(iid):
    conn=get_db()
    conn.execute('UPDATE store_items SET is_active=0 WHERE id=?',(iid,))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/admin/store/items/<int:iid>/image', methods=['POST'])
@admin_required
def api_admin_store_item_image(iid):
    f = request.files.get('image')
    if not f: return jsonify({'success':False})
    fname = save_upload(f, UPLOAD_STORE_DIR, f'item_{iid}')
    if not fname: return jsonify({'success':False})
    url = f'/assets/store/{fname}'
    conn=get_db(); conn.execute('UPDATE store_items SET image=? WHERE id=?',(url,iid))
    conn.commit(); conn.close()
    return jsonify({'success':True,'url':url})

# ─────────────────────────────────────────
# STATIC SERVING
# ─────────────────────────────────────────
@app.route('/assets/videos/<path:fn>')
def serve_video(fn): return send_from_directory(UPLOAD_VIDEO_DIR,fn)
@app.route('/assets/avatars/<path:fn>')
def serve_avatar(fn): return send_from_directory(UPLOAD_AVATAR_DIR,fn)
@app.route('/assets/banners/<path:fn>')
def serve_banner(fn): return send_from_directory(UPLOAD_BANNER_DIR,fn)
@app.route('/assets/store/<path:fn>')
def serve_store(fn): return send_from_directory(UPLOAD_STORE_DIR,fn)
@app.route('/assets/group_media/<path:fn>')
def serve_group(fn): return send_from_directory(UPLOAD_GROUP_DIR,fn)
@app.route('/courses/<path:fn>')
def serve_course_file(fn): return send_from_directory(COURSES_DIR,fn)
@app.route('/games/<path:fn>')
def serve_game_file(fn): return send_from_directory(GAMES_DIR,fn)


# ─────────────────────────────────────────
# GAMES SYSTEM
# ─────────────────────────────────────────

@app.route('/games')
def games_page():
    if 'user_id' not in session: return redirect('/login')
    return render_template('games.html')

@app.route('/game/<int:game_id>')
def game_detail_page(game_id):
    if 'user_id' not in session: return redirect('/login')
    return render_template('game_detail.html')

# ── Upload game ──
@app.route('/api/games/upload', methods=['POST'])
@login_required
def api_games_upload():
    import zipfile, uuid as _uuid
    uid = session['user_id']
    conn = get_db()
    user = conn.execute('SELECT is_premium FROM users WHERE id=?', (uid,)).fetchone()
    conn.close()
    is_premium = bool(user and user['is_premium'])
    max_size = GAME_MAX_SIZE_PREMIUM if is_premium else GAME_MAX_SIZE

    title       = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    category    = (request.form.get('category') or 'Boshqa').strip()
    thumb_file  = request.files.get('thumbnail')
    game_file   = request.files.get('game_file')

    if not title:       return jsonify({'error': 'O\'yin nomini kiriting'}), 400
    if not game_file:   return jsonify({'error': 'O\'yin faylini yuklang'}), 400

    ext = game_file.filename.rsplit('.', 1)[-1].lower() if '.' in game_file.filename else ''
    if ext not in ALLOWED_GAME:
        return jsonify({'error': 'Faqat .zip yoki .html fayl yuklanadi'}), 400

    # Check file size
    game_file.seek(0, 2)
    fsize = game_file.tell()
    game_file.seek(0)
    if fsize > max_size:
        limit_mb = 100 if is_premium else 50
        return jsonify({'error': f'Fayl hajmi {limit_mb}MB dan oshmasin'}), 400

    game_id_str = _uuid.uuid4().hex[:12]
    game_folder = os.path.join(GAMES_DIR, game_id_str)
    os.makedirs(game_folder, exist_ok=True)

    entry_file = 'index.html'

    if ext == 'zip':
        zip_path = os.path.join(game_folder, 'game.zip')
        game_file.save(zip_path)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Security: sanitize file names
                members = []
                for m in zf.infolist():
                    safe_name = os.path.normpath(m.filename).lstrip('/')
                    if '..' in safe_name: continue
                    members.append(m)
                zf.extractall(game_folder, [m for m in members])
            os.remove(zip_path)
            # Detect entry point
            for candidate in ['index.html', 'game.html', 'main.html']:
                if os.path.exists(os.path.join(game_folder, candidate)):
                    entry_file = candidate; break
                # Check one level deep
                for sub in os.listdir(game_folder):
                    subpath = os.path.join(game_folder, sub, candidate)
                    if os.path.isfile(subpath):
                        entry_file = f'{sub}/{candidate}'; break
        except Exception as e:
            shutil.rmtree(game_folder, ignore_errors=True)
            return jsonify({'error': f'ZIP fayl yaroqsiz: {str(e)}'}), 400
    else:
        # Raw HTML file
        fname = secure_filename(game_file.filename) or 'index.html'
        save_path = os.path.join(game_folder, fname)
        game_file.save(save_path)
        entry_file = fname

    # Save thumbnail
    thumb_url = ''
    if thumb_file and thumb_file.filename:
        th_ext = thumb_file.filename.rsplit('.', 1)[-1].lower()
        if th_ext in ALLOWED_IMG:
            th_name = f'thumb_{game_id_str}.{th_ext}'
            thumb_file.save(os.path.join(GAMES_THUMB_DIR, th_name))
            thumb_url = f'/games/thumbnails/{th_name}'

    conn = get_db()
    conn.execute('''INSERT INTO games (title,description,category,author_id,thumbnail,file_path,game_entry,status)
        VALUES (?,?,?,?,?,?,?,?)''',
        (title, description, category, uid, thumb_url, game_id_str, entry_file, 'pending'))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': "O'yin moderatsiyaga yuborildi. Tasdiqlangandan so'ng chiqadi."})

# ── List published games ──
@app.route('/api/games')
def api_games_list():
    conn = get_db()
    cat = request.args.get('cat', '')
    q = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'newest')

    query = '''SELECT g.*, u.username, u.full_name, u.avatar, u.has_tick
               FROM games g JOIN users u ON g.author_id=u.id
               WHERE g.status='published' '''
    params = []
    if cat:
        query += ' AND g.category=?'; params.append(cat)
    if q:
        query += ' AND (g.title LIKE ? OR g.description LIKE ?)'; params += [f'%{q}%', f'%{q}%']
    if sort == 'popular':
        query += ' ORDER BY g.views DESC'
    elif sort == 'top_rated':
        query += ' ORDER BY g.rating_avg DESC, g.rating_count DESC'
    else:
        query += ' ORDER BY g.created_at DESC'

    games = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify([dict(g) for g in games])

# ── Get single game ──
@app.route('/api/games/<int:gid>')
def api_game_get(gid):
    uid = session.get('user_id')
    conn = get_db()
    g = conn.execute('''SELECT g.*, u.username, u.full_name, u.avatar, u.has_tick
        FROM games g JOIN users u ON g.author_id=u.id WHERE g.id=?''', (gid,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': "O'yin topilmadi"}), 404
    if g['status'] != 'published' and session.get('role') != 'admin' and g['author_id'] != uid:
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403

    user_rating = None
    if uid:
        r = conn.execute('SELECT rating FROM game_ratings WHERE game_id=? AND user_id=?', (gid, uid)).fetchone()
        if r: user_rating = r['rating']
    conn.close()

    result = dict(g)
    result['user_rating'] = user_rating
    result['game_url'] = f'/games/{g["file_path"]}/{g["game_entry"]}' if g['file_path'] else ''
    return jsonify(result)

# ── Increment view count ──
@app.route('/api/games/<int:gid>/view', methods=['POST'])
def api_game_view(gid):
    conn = get_db()
    conn.execute('UPDATE games SET views=views+1 WHERE id=? AND status=?', (gid, 'published'))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ── Rate a game ──
@app.route('/api/games/<int:gid>/rate', methods=['POST'])
@login_required
def api_game_rate(gid):
    uid = session['user_id']
    d = request.get_json() or {}
    rating = int(d.get('rating', 0))
    if rating < 1 or rating > 5:
        return jsonify({'error': 'Rating 1-5 orasida bo\'lishi kerak'}), 400
    conn = get_db()
    g = conn.execute('SELECT id FROM games WHERE id=? AND status=?', (gid, 'published')).fetchone()
    if not g: conn.close(); return jsonify({'error': "O'yin topilmadi"}), 404
    try:
        conn.execute('INSERT OR REPLACE INTO game_ratings (game_id,user_id,rating) VALUES (?,?,?)',
                     (gid, uid, rating))
    except: pass
    # Recalculate avg
    agg = conn.execute('SELECT AVG(rating) as avg, COUNT(*) as cnt FROM game_ratings WHERE game_id=?',
                       (gid,)).fetchone()
    conn.execute('UPDATE games SET rating_avg=?, rating_count=? WHERE id=?',
                 (round(agg['avg'], 2), agg['cnt'], gid))
    conn.commit()
    avg = agg['avg']; cnt = agg['cnt']
    conn.close()
    return jsonify({'success': True, 'rating_avg': round(avg, 2), 'rating_count': cnt})

@app.route('/api/games/<int:gid>/comments')
def api_game_comments(gid):
    conn = get_db()
    rows = conn.execute('''SELECT gc.*, u.username, u.full_name, u.avatar, u.has_tick
        FROM game_comments gc JOIN users u ON gc.user_id=u.id
        WHERE gc.game_id=? ORDER BY gc.created_at DESC LIMIT 50''', (gid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/games/<int:gid>/comments', methods=['POST'])
@login_required
def api_game_comment_post(gid):
    uid = session['user_id']
    d = request.get_json() or {}
    content = (d.get('content') or '').strip()[:500]
    if not content: return jsonify({'error': 'Izoh yozing'}), 400
    conn = get_db()
    g = conn.execute('SELECT id FROM games WHERE id=?', (gid,)).fetchone()
    if not g: conn.close(); return jsonify({'error': "O'yin topilmadi"}), 404
    conn.execute('INSERT INTO game_comments (game_id, user_id, content) VALUES (?,?,?)', (gid, uid, content))
    conn.commit()
    cid = conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    u = conn.execute('SELECT username, full_name, avatar, has_tick FROM users WHERE id=?', (uid,)).fetchone()
    conn.close()
    return jsonify({'success': True, 'id': cid, 'username': u['username'],
                    'full_name': u['full_name'], 'avatar': u['avatar'] or '',
                    'has_tick': u['has_tick'], 'content': content,
                    'created_at': __import__('datetime').datetime.now().isoformat()})
@app.route('/api/games/leaderboard')
def api_games_leaderboard():
    conn = get_db()
    cat = request.args.get('cat', 'views')
    if cat == 'rating':
        rows = conn.execute('''SELECT g.*, u.username, u.full_name, u.avatar
            FROM games g JOIN users u ON g.author_id=u.id
            WHERE g.status='published' AND g.rating_count > 0
            ORDER BY g.rating_avg DESC, g.rating_count DESC LIMIT 20''').fetchall()
    else:
        rows = conn.execute('''SELECT g.*, u.username, u.full_name, u.avatar
            FROM games g JOIN users u ON g.author_id=u.id
            WHERE g.status='published'
            ORDER BY g.views DESC LIMIT 20''').fetchall()
    conn.close()
    result = []
    for i, r in enumerate(rows):
        d = dict(r)
        d['rank'] = i + 1
        result.append(d)
    return jsonify(result)

# ─────────────────────────────────────────
# GAME MONETIZATSIYA
# ─────────────────────────────────────────

@app.route('/api/games/<int:gid>/monetization/status')
@login_required
def api_game_monetz_status(gid):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT * FROM games WHERE id=? AND author_id=?', (gid, uid)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'O\'yiningiz topilmadi'}), 403

    mon = conn.execute('SELECT * FROM game_monetization WHERE game_id=?', (gid,)).fetchone()
    views = g['views'] or 0
    rating_count = g['rating_count'] or 0
    days = conn.execute("SELECT JULIANDAY('now') - JULIANDAY(created_at) FROM games WHERE id=?", (gid,)).fetchone()[0] or 0

    requirements = [
        {'label': '1000+ O\'yin o\'ynalgan', 'current': views, 'target': 1000, 'met': views >= 1000},
        {'label': '50+ Baho olgan', 'current': rating_count, 'target': 50, 'met': rating_count >= 50},
        {'label': '4.0+ O\'rtacha baho', 'current': round(g['rating_avg'] or 0, 1), 'target': 4.0, 'met': (g['rating_avg'] or 0) >= 4.0},
        {'label': '30 kun faol', 'current': int(days), 'target': 30, 'met': days >= 30},
    ]
    all_met = all(r['met'] for r in requirements)
    conn.close()
    return jsonify({
        'game_title': g['title'],
        'requirements': requirements,
        'all_met': all_met,
        'status': mon['status'] if mon else 'none',
        'ad_title': mon['ad_title'] if mon else '',
        'ad_description': mon['ad_description'] if mon else '',
        'ad_link': mon['ad_link'] if mon else '',
        'ad_cta': mon['ad_cta'] if mon else "O'ynash",
        'total_ad_clicks': mon['total_ad_clicks'] if mon else 0,
        'views': views,
    })

@app.route('/api/games/<int:gid>/monetization/apply', methods=['POST'])
@login_required
def api_game_monetz_apply(gid):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT * FROM games WHERE id=? AND author_id=?', (gid, uid)).fetchone()
    if not g: conn.close(); return jsonify({'error': 'Topilmadi'}), 403

    views = g['views'] or 0
    rc = g['rating_count'] or 0
    ra = g['rating_avg'] or 0
    days = conn.execute("SELECT JULIANDAY('now') - JULIANDAY(created_at) FROM games WHERE id=?", (gid,)).fetchone()[0] or 0

    if not (views >= 1000 and rc >= 50 and ra >= 4.0 and days >= 30):
        conn.close(); return jsonify({'error': 'Talablar bajarilmagan'}), 400

    try:
        conn.execute('INSERT OR REPLACE INTO game_monetization (user_id,game_id,status,approved_at) VALUES (?,?,?,CURRENT_TIMESTAMP)',
                    (uid, gid, 'approved'))
        conn.commit(); conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close(); return jsonify({'error': str(e)}), 500

@app.route('/api/games/<int:gid>/monetization/settings', methods=['POST'])
@login_required
def api_game_monetz_settings(gid):
    uid = session['user_id']
    d = request.get_json() or {}
    conn = get_db()
    mon = conn.execute('SELECT id FROM game_monetization WHERE game_id=? AND user_id=? AND status=?',
                      (gid, uid, 'approved')).fetchone()
    if not mon: conn.close(); return jsonify({'error': 'Monetizatsiya yoqilmagan'}), 403
    conn.execute('''UPDATE game_monetization SET ad_title=?,ad_description=?,ad_link=?,ad_cta=? WHERE game_id=?''',
                (d.get('ad_title','')[:100], d.get('ad_description','')[:300],
                 d.get('ad_link','')[:500], d.get('ad_cta',"O'ynash")[:30], gid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/games/<int:gid>/monetization/ad')
def api_game_monetz_ad(gid):
    conn = get_db()
    mon = conn.execute("SELECT * FROM game_monetization WHERE game_id=? AND status=? AND ad_link!=?",
                      (gid, 'approved', '')).fetchone()
    conn.close()
    if not mon: return jsonify({'has_ad': False})
    return jsonify({
        'has_ad': True,
        'ad_title': mon['ad_title'],
        'ad_description': mon['ad_description'],
        'ad_link': mon['ad_link'],
        'ad_cta': mon['ad_cta'] or "O'ynash",
    })

@app.route('/api/games/<int:gid>/ad-click', methods=['POST'])
def api_game_ad_click(gid):
    conn = get_db()
    conn.execute('UPDATE game_monetization SET total_ad_clicks=total_ad_clicks+1 WHERE game_id=?', (gid,))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ── Admin: pending games list (admin + moderator) ──
@app.route('/api/admin/games/pending')
@login_required
def api_admin_games_pending():
    if session.get('role') not in ('admin', 'moderator'):
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    rows = conn.execute('''SELECT g.*, u.username, u.full_name
        FROM games g JOIN users u ON g.author_id=u.id
        WHERE g.status='pending' ORDER BY g.created_at DESC''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── Admin: all games ──
@app.route('/api/admin/games/all')
@login_required
def api_admin_games_all():
    if session.get('role') not in ('admin', 'moderator'):
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    rows = conn.execute('''SELECT g.*, u.username, u.full_name
        FROM games g JOIN users u ON g.author_id=u.id
        ORDER BY g.created_at DESC''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── Admin: preview pending game (moderator can test) ──
@app.route('/api/admin/games/<int:gid>/preview')
@login_required
def api_admin_game_preview(gid):
    if session.get('role') not in ('admin', 'moderator'):
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    g = conn.execute('''SELECT g.*, u.username, u.full_name, u.avatar
        FROM games g JOIN users u ON g.author_id=u.id WHERE g.id=?''', (gid,)).fetchone()
    conn.close()
    if not g: return jsonify({'error': "O'yin topilmadi"}), 404
    result = dict(g)
    result['game_url'] = f'/games/{g["file_path"]}/{g["game_entry"]}' if g['file_path'] else ''
    return jsonify(result)

# ── Admin: approve/reject game ──
@app.route('/api/admin/games/<int:gid>/approve', methods=['POST'])
@login_required
def api_admin_game_approve(gid):
    if session.get('role') not in ('admin', 'moderator'):
        return jsonify({'error': 'Forbidden'}), 403
    conn = get_db()
    g = conn.execute('SELECT title, author_id FROM games WHERE id=?', (gid,)).fetchone()
    conn.execute("UPDATE games SET status='published' WHERE id=?", (gid,))
    conn.commit(); conn.close()
    if g:
        add_notification(g['author_id'], 'game_approved',
            f"🎮 O'yiningiz tasdiqlandi!",
            f"'{g['title']}' o'yini saytda chiqdi. Barakalla!",
            f'/game/{gid}')
    return jsonify({'success': True})

@app.route('/api/admin/games/<int:gid>/reject', methods=['POST'])
@login_required
def api_admin_game_reject(gid):
    if session.get('role') not in ('admin', 'moderator'):
        return jsonify({'error': 'Forbidden'}), 403
    d = request.get_json() or {}
    reason = (d.get('reason') or '').strip()
    conn = get_db()
    g = conn.execute('SELECT file_path, thumbnail, title, author_id FROM games WHERE id=?', (gid,)).fetchone()
    if g:
        fp = os.path.join(GAMES_DIR, g['file_path']) if g['file_path'] else None
        if fp and os.path.isdir(fp): shutil.rmtree(fp, ignore_errors=True)
        if g['thumbnail']:
            th = os.path.join(BASE_DIR, g['thumbnail'].lstrip('/'))
            if os.path.isfile(th): os.remove(th)
        add_notification(g['author_id'], 'game_rejected',
            f"❌ O'yiningiz rad etildi",
            (f"Sabab: {reason}" if reason else f"'{g['title']}' rad etildi."),
            '')
    conn.execute("UPDATE games SET status='rejected', reject_reason=? WHERE id=?", (reason, gid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ── Admin: delete game ──
@app.route('/api/admin/games/<int:gid>/delete', methods=['POST'])
@admin_required
def api_admin_game_delete(gid):
    conn = get_db()
    g = conn.execute('SELECT file_path, thumbnail FROM games WHERE id=?', (gid,)).fetchone()
    if g:
        fp = os.path.join(GAMES_DIR, g['file_path']) if g['file_path'] else None
        if fp and os.path.isdir(fp): shutil.rmtree(fp, ignore_errors=True)
        if g['thumbnail']:
            th = os.path.join(BASE_DIR, g['thumbnail'].lstrip('/'))
            if os.path.isfile(th): os.remove(th)
    conn.execute('DELETE FROM game_ratings WHERE game_id=?', (gid,))
    conn.execute('DELETE FROM games WHERE id=?', (gid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ─────────────────────────────────────────
# NOTIFICATIONS API
# ─────────────────────────────────────────

@app.route('/api/notifications')
@login_required
def api_notifications():
    uid = session['user_id']
    conn = get_db()
    rows = conn.execute('''SELECT n.*, u.username as sender_username
        FROM notifications n
        LEFT JOIN users u ON n.sender_id=u.id AND n.sender_id > 0
        WHERE n.user_id=?
        ORDER BY n.created_at DESC LIMIT 30''', (uid,)).fetchall()
    conn.close()
    return jsonify({'notifications': [dict(r) for r in rows]})

@app.route('/api/notifications/count')
@login_required
def api_notifications_count():
    uid = session['user_id']
    conn = get_db()
    cnt = conn.execute('SELECT COUNT(*) as c FROM notifications WHERE user_id=? AND is_read=0', (uid,)).fetchone()['c']
    conn.close()
    return jsonify({'count': cnt})

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def api_notifications_mark_read():
    uid = session['user_id']
    nid = (request.get_json() or {}).get('id')
    conn = get_db()
    if nid:
        conn.execute('UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?', (nid, uid))
    else:
        conn.execute('UPDATE notifications SET is_read=1 WHERE user_id=?', (uid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ── SSE: Real-time notifications stream ──
import time as _time
@app.route('/api/notifications/stream')
@login_required
def api_notifications_stream():
    uid = session['user_id']
    def generate():
        last_id = 0
        try:
            conn = get_db()
            row = conn.execute('SELECT MAX(id) as m FROM notifications WHERE user_id=?', (uid,)).fetchone()
            last_id = row['m'] or 0
            conn.close()
        except: pass
        while True:
            try:
                conn = get_db()
                rows = conn.execute('''SELECT * FROM notifications WHERE user_id=? AND id>?
                    ORDER BY id ASC LIMIT 5''', (uid, last_id)).fetchall()
                conn.close()
                for r in rows:
                    last_id = r['id']
                    import json as _json
                    data = _json.dumps(dict(r), ensure_ascii=False)
                    yield f'data: {data}\n\n'
            except: pass
            _time.sleep(5)
    from flask import Response
    return Response(generate(), mimetype='text/event-stream',
        headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

# ── LEADERBOARD ──
@app.route('/api/leaderboard')
@login_required
def api_leaderboard():
    conn = get_db()
    cat = request.args.get('cat', 'points')  # points, lessons, friends
    if cat == 'lessons':
        rows = conn.execute('''SELECT u.id,u.username,u.full_name,u.avatar,u.has_tick,u.active_title,
            COUNT(p.id) as score FROM users u
            LEFT JOIN progress p ON p.user_id=u.id AND p.completed=1
            GROUP BY u.id ORDER BY score DESC LIMIT 50''').fetchall()
    elif cat == 'friends':
        rows = conn.execute('''SELECT u.id,u.username,u.full_name,u.avatar,u.has_tick,u.active_title,
            COUNT(f.id) as score FROM users u
            LEFT JOIN friends f ON f.user1_id=u.id OR f.user2_id=u.id
            GROUP BY u.id ORDER BY score DESC LIMIT 50''').fetchall()
    else:
        rows = conn.execute('''SELECT id,username,full_name,avatar,has_tick,active_title,
            points as score FROM users ORDER BY points DESC LIMIT 50''').fetchall()
    
    uid = session['user_id']
    result = []
    for i, r in enumerate(rows):
        d = dict(r)
        d['rank'] = i + 1
        d['is_me'] = (r['id'] == uid)
        result.append(d)
    conn.close()
    return jsonify(result)

@app.route('/leaderboard')
def leaderboard_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('leaderboard.html')


# ── ADMIN: Role management, ban ──
@app.route('/api/admin/users/<int:uid>/role', methods=['POST'])
@admin_required
def api_admin_set_role(uid):
    d = request.get_json()
    role = d.get('role','student')
    if role not in ('student','moderator','admin'): return jsonify({'error':'Invalid role'}),400
    conn = get_db()
    # Prevent removing the main admin
    u = conn.execute('SELECT username FROM users WHERE id=?',(uid,)).fetchone()
    if u and u['username'] == 'bobur' and role != 'admin':
        conn.close(); return jsonify({'error':'Bu adminni ozgartirib bolmaydi'}),403
    conn.execute('UPDATE users SET role=? WHERE id=?',(role,uid))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/admin/users/<int:uid>/ban', methods=['POST'])
@admin_required
def api_admin_ban_user(uid):
    d = request.get_json()
    banned = int(d.get('banned',1))
    conn = get_db()
    u = conn.execute('SELECT username FROM users WHERE id=?',(uid,)).fetchone()
    if u and u['username'] == 'bobur':
        conn.close(); return jsonify({'error':'Bu adminni ban qilib bolmaydi'}),403
    conn.execute('UPDATE users SET role=? WHERE id=?',('banned' if banned else 'student',uid))
    conn.commit(); conn.close()
    return jsonify({'success':True})

@app.route('/api/admin/users/<int:uid>/points', methods=['POST'])
@admin_required  
def api_admin_set_points(uid):
    d = request.get_json()
    delta = int(d.get('delta',0))
    conn = get_db()
    conn.execute('UPDATE users SET points=points+? WHERE id=?',(delta,uid))
    conn.execute('INSERT INTO point_log (user_id,delta,reason,ref_id) VALUES (?,?,?,?)',(uid,delta,'Admin adjustment',session['user_id']))
    conn.commit(); conn.close()
    return jsonify({'success':True})

# ── SOCIAL: Add friend by username ──
@app.route('/api/social/add-by-username', methods=['POST'])
@login_required
def api_add_by_username():
    username = (request.get_json() or {}).get('username','').strip()
    if not username: return jsonify({'error':'Username kiriting'}),400
    conn = get_db()
    target = conn.execute('SELECT id,full_name,username,avatar,has_tick FROM users WHERE username=?',(username,)).fetchone()
    if not target:
        conn.close(); return jsonify({'error':'Foydalanuvchi topilmadi'}),404
    uid = session['user_id']
    if target['id'] == uid:
        conn.close(); return jsonify({'error':'Ozingizga sorov yubora olmaysiz'}),400
    # Check already friends
    f = conn.execute('SELECT id FROM friends WHERE (user1_id=? AND user2_id=?) OR (user1_id=? AND user2_id=?)',(uid,target['id'],target['id'],uid)).fetchone()
    if f: conn.close(); return jsonify({'error':'Allaqachon dostlar'}),400
    try:
        conn.execute('INSERT INTO friend_requests (from_id,to_id) VALUES (?,?)',(uid,target['id']))
        conn.commit()
    except: conn.rollback()
    conn.close()
    return jsonify({'success':True,'name':target['full_name'],'username':target['username']})

# ── GROUP: Media upload (image, video, audio, gif, sticker) ──
@app.route('/api/groups/<slug>/upload-media', methods=['POST'])
@login_required
def api_group_upload_media(slug):
    conn = get_db()
    g = conn.execute('SELECT * FROM groups WHERE slug=?',(slug,)).fetchone()
    if not g: conn.close(); return jsonify({'error':'Guruh topilmadi'}),404
    uid = session['user_id']
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?',(g['id'],uid)).fetchone()
    if not mem: conn.close(); return jsonify({'error':'Siz aza emassiz'}),403
    if g['group_type'] == 'channel' and mem['role'] not in ('owner','admin'):
        conn.close(); return jsonify({'error':'Kanalda faqat adminlar yozishi mumkin'}),403
    
    file = request.files.get('file')
    if not file or not file.filename:
        conn.close(); return jsonify({'error':'Fayl yuklanmadi'}),400
    
    ext = file.filename.rsplit('.',1)[-1].lower() if '.' in file.filename else ''
    
    # Determine media type
    if ext in ('jpg','jpeg','png','gif','webp'):
        media_type = 'gif' if ext == 'gif' else 'image'
        save_dir = UPLOAD_GROUP_DIR
    elif ext in ('mp4','webm','mov','avi'):
        media_type = 'video'
        save_dir = UPLOAD_GROUP_DIR
    elif ext in ('mp3','ogg','wav','opus','m4a','aac'):
        media_type = 'audio'
        save_dir = UPLOAD_GROUP_DIR
    elif ext in ('tgs','webp'):
        media_type = 'sticker'
        save_dir = UPLOAD_GROUP_DIR
    else:
        conn.close(); return jsonify({'error':'Qollab-quvvatlanmaydigan format'}),400
    
    import uuid
    fname = f"{uuid.uuid4().hex}.{ext}"
    fpath = os.path.join(save_dir, fname)
    file.save(fpath)
    media_url = f'/assets/group_media/{fname}'
    
    conn.execute('INSERT INTO group_messages (group_id,user_id,content,msg_type,media_url) VALUES (?,?,?,?,?)',
                 (g['id'],uid,file.filename,media_type,media_url))
    conn.commit()
    msg_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    msg = conn.execute('SELECT m.*,u.username,u.full_name,u.avatar FROM group_messages m JOIN users u ON m.user_id=u.id WHERE m.id=?',(msg_id,)).fetchone()
    conn.close()
    return jsonify({'success':True,'message':dict(msg),'media_url':media_url,'media_type':media_type})

# ── YT/IG Follower fetch (uses public APIs) ──
@app.route('/api/social/fetch-followers', methods=['POST'])
@login_required
def api_fetch_followers():
    uid = session['user_id']
    conn = get_db()
    u = conn.execute('SELECT yt_link, ig_link FROM users WHERE id=?',(uid,)).fetchone()
    if not u: conn.close(); return jsonify({'error':'User not found'}),404
    
    yt_followers = 0
    ig_followers = 0
    
    # YouTube: try to fetch subscriber count from yt link
    yt_link = u['yt_link'] or ''
    if yt_link:
        try:
            import urllib.request, re as re_mod
            # Extract channel handle or ID
            handle = ''
            for pattern in [r'/@([^/?]+)', r'/channel/([^/?]+)', r'/c/([^/?]+)', r'/user/([^/?]+)']:
                m = re_mod.search(pattern, yt_link)
                if m: handle = m.group(1); break
            if handle:
                # Scrape YouTube page for subscriber count
                req = urllib.request.Request(
                    f'https://www.youtube.com/@{handle}',
                    headers={'User-Agent': 'Mozilla/5.0 (compatible)'}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                # Look for subscriber count in page
                patterns = [
                    r'"subscriberCountText":\{"simpleText":"([^"]+)"',
                    r'"subscribers":\{"simpleText":"([^"]+)"',
                    r'subscribers["\s]*:["\s]*"([^"]+)"',
                ]
                for pat in patterns:
                    m = re_mod.search(pat, html)
                    if m:
                        val_str = m.group(1).upper().replace(',','').replace(' ','')
                        if 'M' in val_str: yt_followers = int(float(val_str.replace('M','')) * 1_000_000)
                        elif 'K' in val_str: yt_followers = int(float(val_str.replace('K','')) * 1_000)
                        elif val_str.isdigit(): yt_followers = int(val_str)
                        if yt_followers > 0: break
        except Exception as e:
            pass  # silently fail, keep 0

    # Instagram: public page scrape
    ig_link = u['ig_link'] or ''
    if ig_link:
        try:
            import urllib.request, re as re_mod
            m = re_mod.search(r'instagram\.com/([^/?]+)', ig_link)
            if m:
                username = m.group(1).rstrip('/')
                req = urllib.request.Request(
                    f'https://www.instagram.com/{username}/?__a=1&__d=dis',
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data_str = resp.read().decode('utf-8', errors='ignore')
                m2 = re_mod.search(r'"edge_followed_by":\{"count":(\d+)', data_str)
                if m2: ig_followers = int(m2.group(1))
        except:
            pass

    # Update DB
    conn.execute('UPDATE users SET yt_followers=?, ig_followers=? WHERE id=?',(yt_followers, ig_followers, uid))
    conn.commit()
    conn.close()
    return jsonify({'success':True,'yt_followers':yt_followers,'ig_followers':ig_followers,'total':yt_followers+ig_followers})


# ═══════════════════════════════════════
# STREAK
# ═══════════════════════════════════════
@app.route('/api/streak/status')
@login_required
def api_streak_status():
    uid = session['user_id']
    conn = get_db()
    u = conn.execute('SELECT streak_days, last_activity_date, longest_streak FROM users WHERE id=?',(uid,)).fetchone()
    ud = dict(u) if u else {}
    conn.close()
    from datetime import date, timedelta
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    last = ud.get('last_activity_date','')
    active_today = last == today
    return jsonify({
        'streak_days': ud.get('streak_days', 0),
        'longest_streak': ud.get('longest_streak', 0),
        'last_activity_date': last,
        'active_today': active_today,
        'at_risk': last == yesterday and not active_today
    })

# ═══════════════════════════════════════
# CERTIFICATES
# ═══════════════════════════════════════
@app.route('/api/certificate/check/<course_slug>')
@login_required
def api_cert_check(course_slug):
    uid = session['user_id']
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) as c FROM mavzular WHERE course_slug=?',(course_slug,)).fetchone()['c']
    done = conn.execute('SELECT COUNT(*) as c FROM progress WHERE user_id=? AND course_slug=? AND completed=1',(uid,course_slug)).fetchone()['c']
    cert = conn.execute('SELECT * FROM certificates WHERE user_id=? AND course_slug=?',(uid,course_slug)).fetchone()
    conn.close()
    eligible = total > 0 and done >= total
    return jsonify({'eligible': eligible, 'done': done, 'total': total, 'has_cert': cert is not None,
                    'cert_code': cert['cert_code'] if cert else None})

@app.route('/api/certificate/issue/<course_slug>', methods=['POST'])
@login_required
def api_cert_issue(course_slug):
    uid = session['user_id']
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) as c FROM mavzular WHERE course_slug=?',(course_slug,)).fetchone()['c']
    done = conn.execute('SELECT COUNT(*) as c FROM progress WHERE user_id=? AND course_slug=? AND completed=1',(uid,course_slug)).fetchone()['c']
    if total == 0 or done < total:
        conn.close()
        return jsonify({'success':False,'error':'Kurs hali tugallanmagan'}), 400
    existing = conn.execute('SELECT cert_code FROM certificates WHERE user_id=? AND course_slug=?',(uid,course_slug)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success':True,'cert_code':existing['cert_code']})
    import uuid
    cert_code = 'BX-' + str(uuid.uuid4()).upper()[:12]
    conn.execute('INSERT INTO certificates (user_id,course_slug,cert_code) VALUES (?,?,?)',(uid,course_slug,cert_code))
    conn.commit()
    conn.close()
    return jsonify({'success':True,'cert_code':cert_code})

@app.route('/certificate/<cert_code>')
def view_certificate(cert_code):
    conn = get_db()
    cert = conn.execute('SELECT * FROM certificates WHERE cert_code=?',(cert_code,)).fetchone()
    if not cert: conn.close(); return "Sertifikat topilmadi", 404
    u = conn.execute('SELECT full_name, username FROM users WHERE id=?',(cert['user_id'],)).fetchone()
    course = conn.execute('SELECT title_uz FROM courses WHERE slug=?',(cert['course_slug'],)).fetchone()
    conn.close()
    full_name = u['full_name'] if u else 'Noma\'lum'
    course_title = course['title_uz'] if course else cert['course_slug']
    issued = cert['issued_at'][:10] if cert['issued_at'] else ''
    return f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8"><title>Sertifikat — {full_name}</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Outfit',sans-serif;background:#f0f0f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;}}
.cert{{background:white;width:900px;max-width:100%;border-radius:24px;padding:60px 70px;text-align:center;position:relative;box-shadow:0 24px 64px rgba(0,0,0,.15);border:2px solid #C9A84C;overflow:hidden;}}
.cert::before{{content:'';position:absolute;inset:8px;border:1px solid rgba(201,168,76,.3);border-radius:18px;pointer-events:none;}}
.cert-top{{background:linear-gradient(135deg,#1B2A4A,#2a3f6f);margin:-60px -70px 40px;padding:40px 70px 50px;clip-path:ellipse(110% 100% at 50% 0%);}}
.logo{{font-size:2rem;font-weight:900;color:white;letter-spacing:-1px;}}
.cert-title{{font-size:1rem;color:rgba(255,255,255,.65);margin-top:4px;letter-spacing:2px;text-transform:uppercase;}}
.star{{font-size:2.5rem;margin:20px 0 10px;}}
.cert-main{{font-size:.9rem;color:#6B7280;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;}}
.name{{font-size:2.8rem;font-weight:900;color:#1B2A4A;line-height:1.1;margin:8px 0 20px;}}
.course-label{{font-size:.85rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:2px;}}
.course{{font-size:1.6rem;font-weight:800;color:#C9A84C;margin:6px 0 28px;}}
.divider{{width:80px;height:3px;background:linear-gradient(90deg,#1B2A4A,#C9A84C);margin:0 auto 28px;border-radius:99px;}}
.meta{{display:flex;justify-content:center;gap:60px;margin-top:28px;}}
.meta-item{{text-align:center;}}
.meta-label{{font-size:.72rem;color:#9CA3AF;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;}}
.meta-val{{font-size:.88rem;font-weight:700;color:#1B2A4A;}}
.code{{margin-top:28px;font-size:.7rem;color:#D1D5DB;letter-spacing:2px;}}
.print-btn{{margin-top:24px;padding:12px 28px;background:linear-gradient(135deg,#1B2A4A,#2a3f6f);color:white;border:none;border-radius:12px;font-size:.9rem;font-weight:700;cursor:pointer;font-family:'Outfit',sans-serif;}}
@media print{{.print-btn{{display:none;}}body{{background:white;}}}}
</style></head><body>
<div>
<div class="cert">
  <div class="cert-top">
    <div class="logo">🎓 Bilimxon</div>
    <div class="cert-title">Muvaffaqiyat Sertifikati</div>
  </div>
  <div class="star">🏆</div>
  <div class="cert-main">Ushbu sertifikat taqdim etiladi</div>
  <div class="name">{full_name}</div>
  <div class="divider"></div>
  <div class="course-label">Kurs muvaffaqiyatli tugatildi</div>
  <div class="course">{course_title}</div>
  <div class="meta">
    <div class="meta-item">
      <div class="meta-label">Sana</div>
      <div class="meta-val">{issued}</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Platforma</div>
      <div class="meta-val">Bilimxon.uz</div>
    </div>
    <div class="meta-item">
      <div class="meta-label">Daraja</div>
      <div class="meta-val">&#10003; Tasdiqlangan</div>
    </div>
  </div>
  <div class="code">Sertifikat kodi: {cert_code}</div>
</div>
<div style="text-align:center;margin-top:16px;">
  <button class="print-btn" onclick="window.print()">🖨️ Chop etish / PDF saqlash</button>
</div>
</div>
</body></html>"""


# ═══════════════════════════════════════
# TOURNAMENTS  (Kahoot-style)
# ═══════════════════════════════════════

@app.route('/tournament')
@login_required
def tournament_page():
    return render_template('tournament.html')

@app.route('/tournament/<int:t_id>')
@login_required
def tournament_detail_page(t_id):
    return render_template('tournament_play.html', t_id=t_id)

# ── helpers ──────────────────────────────────────────────
def _tour_dict(t, uid, conn):
    td = dict(t)
    teams = conn.execute(
        'SELECT * FROM tournament_teams WHERE tournament_id=? ORDER BY total_points DESC', (t['id'],)
    ).fetchall()
    my_mem = conn.execute(
        'SELECT team_id FROM tournament_members WHERE tournament_id=? AND user_id=?', (t['id'], uid)
    ).fetchone()
    teams_out = []
    for tm in teams:
        mc = conn.execute('SELECT COUNT(*) as c FROM tournament_members WHERE team_id=?', (tm['id'],)).fetchone()['c']
        members = conn.execute(
            'SELECT u.full_name, u.avatar, tme.points_earned FROM tournament_members tme '
            'JOIN users u ON tme.user_id=u.id WHERE tme.team_id=? ORDER BY tme.points_earned DESC LIMIT 8',
            (tm['id'],)
        ).fetchall()
        teams_out.append({**dict(tm), 'member_count': mc, 'members': [dict(m) for m in members]})
    q_count = conn.execute('SELECT COUNT(*) as c FROM tournament_questions WHERE tournament_id=?', (t['id'],)).fetchone()['c']
    creator = conn.execute('SELECT full_name, username FROM users WHERE id=?', (t['created_by'],)).fetchone()
    td['teams'] = teams_out
    td['my_team_id'] = my_mem['team_id'] if my_mem else None
    td['question_count'] = q_count
    td['creator_name'] = creator['full_name'] if creator else '?'
    td['creator_username'] = creator['username'] if creator else '?'
    return td

# ── list / detail ─────────────────────────────────────────
@app.route('/api/tournaments')
@login_required
def api_tournaments():
    uid = session['user_id']
    conn = get_db()
    rows = conn.execute('SELECT * FROM tournaments ORDER BY created_at DESC LIMIT 30').fetchall()
    result = [_tour_dict(r, uid, conn) for r in rows]
    conn.close()
    return jsonify(result)

@app.route('/api/tournaments/<int:t_id>')
@login_required
def api_tournament_detail(t_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT * FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t: conn.close(); return jsonify({'error': 'Topilmadi'}), 404
    result = _tour_dict(t, uid, conn)
    conn.close()
    return jsonify(result)

# ── create tournament ─────────────────────────────────────
@app.route('/api/tournaments/create', methods=['POST'])
@login_required
def api_tournament_create():
    d = request.get_json() or {}
    uid = session['user_id']
    title = (d.get('title') or '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Sarlavha kiritilmadi'}), 400
    conn = get_db()
    t_id = conn.execute(
        'INSERT INTO tournaments (title,description,start_date,end_date,prize_points,entry_fee,created_by) VALUES (?,?,?,?,?,?,?)',
        (title, d.get('description',''), d.get('start_date',''), d.get('end_date',''),
         int(d.get('prize_points') or 0), int(d.get('entry_fee') or 0), uid)
    ).lastrowid
    conn.commit(); conn.close()
    return jsonify({'success': True, 'tournament_id': t_id})

# ── create team ────────────────────────────────────────────
@app.route('/api/tournaments/<int:t_id>/teams/create', methods=['POST'])
@login_required
def api_tournament_team_create(t_id):
    import string, random
    d = request.get_json() or {}
    uid = session['user_id']
    name = (d.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Jamoa nomini kiriting'}), 400
    is_private = 1 if d.get('is_private') else 0
    color = d.get('color', '#1B2A4A')
    join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) if is_private else ''
    conn = get_db()
    t = conn.execute('SELECT status, entry_fee FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t: conn.close(); return jsonify({'success': False, 'error': 'Musobaqa topilmadi'}), 404
    if t['status'] == 'finished': conn.close(); return jsonify({'success': False, 'error': 'Musobaqa tugagan'}), 400
    team_id = conn.execute(
        'INSERT INTO tournament_teams (tournament_id,name,color,is_private,join_code,owner_id) VALUES (?,?,?,?,?,?)',
        (t_id, name, color, is_private, join_code, uid)
    ).lastrowid
    # Auto-join creator
    fee = t['entry_fee'] or 0
    if fee > 0:
        me = conn.execute('SELECT points FROM users WHERE id=?', (uid,)).fetchone()
        if not me or me['points'] < fee:
            conn.close(); return jsonify({'success': False, 'error': f"Balans yetarli emas ({fee} ochko kerak)"}), 400
        conn.execute('UPDATE users SET points=points-? WHERE id=?', (fee, uid))
        conn.execute('INSERT INTO point_log (user_id,delta,reason) VALUES (?,?,?)', (uid, -fee, f'Musobaqa kirish: {t_id}'))
    conn.execute('INSERT OR IGNORE INTO tournament_members (tournament_id,team_id,user_id) VALUES (?,?,?)', (t_id, team_id, uid))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'team_id': team_id, 'join_code': join_code})

# ── join team ──────────────────────────────────────────────
@app.route('/api/tournaments/<int:t_id>/join', methods=['POST'])
@login_required
def api_tournament_join(t_id):
    d = request.get_json() or {}
    uid = session['user_id']
    team_id = d.get('team_id')
    join_code = (d.get('join_code') or '').strip().upper()
    conn = get_db()
    t = conn.execute('SELECT status, entry_fee FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t: conn.close(); return jsonify({'success': False, 'error': 'Topilmadi'}), 404
    if t['status'] == 'finished': conn.close(); return jsonify({'success': False, 'error': 'Musobaqa tugagan'}), 400
    existing = conn.execute('SELECT id FROM tournament_members WHERE tournament_id=? AND user_id=?', (t_id, uid)).fetchone()
    if existing: conn.close(); return jsonify({'success': False, 'error': "Allaqachon qo'shilgansiz"}), 400
    team = conn.execute('SELECT * FROM tournament_teams WHERE id=? AND tournament_id=?', (team_id, t_id)).fetchone()
    if not team: conn.close(); return jsonify({'success': False, 'error': 'Jamoa topilmadi'}), 404
    if team['is_private'] and team['join_code'] != join_code:
        conn.close(); return jsonify({'success': False, 'error': 'Noto\'g\'ri maxsus kod'}), 403
    fee = t['entry_fee'] or 0
    if fee > 0:
        me = conn.execute('SELECT points FROM users WHERE id=?', (uid,)).fetchone()
        if not me or me['points'] < fee:
            conn.close(); return jsonify({'success': False, 'error': f"Balans yetarli emas ({fee} ochko kerak)"}), 400
        conn.execute('UPDATE users SET points=points-? WHERE id=?', (fee, uid))
        conn.execute('INSERT INTO point_log (user_id,delta,reason) VALUES (?,?,?)', (uid, -fee, f'Musobaqa kirish #{t_id}'))
    conn.execute('INSERT INTO tournament_members (tournament_id,team_id,user_id) VALUES (?,?,?)', (t_id, team_id, uid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ── leave team ─────────────────────────────────────────────
@app.route('/api/tournaments/<int:t_id>/leave', methods=['POST'])
@login_required
def api_tournament_leave(t_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT status FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if t and t['status'] != 'active':
        conn.execute('DELETE FROM tournament_members WHERE tournament_id=? AND user_id=?', (t_id, uid))
        conn.commit()
    conn.close()
    return jsonify({'success': True})

# ── questions CRUD ─────────────────────────────────────────
@app.route('/api/tournaments/<int:t_id>/questions')
@login_required
def api_tournament_questions_get(t_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT created_by, status FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t: conn.close(); return jsonify([])
    is_creator = (t['created_by'] == uid) or session.get('role') == 'admin'
    # Hide correct_option from non-creators during active tournament
    rows = conn.execute('SELECT * FROM tournament_questions WHERE tournament_id=? ORDER BY order_num', (t_id,)).fetchall()
    result = []
    for r in rows:
        rd = dict(r)
        if not is_creator and t['status'] == 'active':
            # Show answered status for this user
            ans = conn.execute('SELECT selected_option, is_correct FROM tournament_answers WHERE question_id=? AND user_id=?', (r['id'], uid)).fetchone()
            rd['my_answer'] = ans['selected_option'] if ans else None
            rd['my_correct'] = ans['is_correct'] if ans else None
            del rd['correct_option']
        result.append(rd)
    conn.close()
    return jsonify(result)

@app.route('/api/tournaments/<int:t_id>/questions/add', methods=['POST'])
@login_required
def api_tournament_questions_add(t_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT created_by, status FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t: conn.close(); return jsonify({'success': False}), 404
    if t['created_by'] != uid and session.get('role') != 'admin':
        conn.close(); return jsonify({'success': False, 'error': 'Ruxsat yo\'q'}), 403
    if t['status'] == 'finished':
        conn.close(); return jsonify({'success': False, 'error': 'Musobaqa tugagan'}), 400
    d = request.get_json() or {}
    max_ord = conn.execute('SELECT COALESCE(MAX(order_num),0) as m FROM tournament_questions WHERE tournament_id=?', (t_id,)).fetchone()['m']
    q_id = conn.execute(
        'INSERT INTO tournament_questions (tournament_id,question_text,option_a,option_b,option_c,option_d,correct_option,points,time_limit,order_num) VALUES (?,?,?,?,?,?,?,?,?,?)',
        (t_id, d.get('question_text',''), d.get('option_a',''), d.get('option_b',''),
         d.get('option_c',''), d.get('option_d',''), d.get('correct_option','A'),
         int(d.get('points') or 10), int(d.get('time_limit') or 30), max_ord+1)
    ).lastrowid
    conn.commit(); conn.close()
    return jsonify({'success': True, 'question_id': q_id})

@app.route('/api/tournaments/<int:t_id>/questions/<int:q_id>/delete', methods=['POST'])
@login_required
def api_tournament_question_delete(t_id, q_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT created_by FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if t and (t['created_by'] == uid or session.get('role') == 'admin'):
        conn.execute('DELETE FROM tournament_questions WHERE id=? AND tournament_id=?', (q_id, t_id))
        conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/tournaments/<int:t_id>/questions/<int:q_id>/edit', methods=['POST'])
@login_required
def api_tournament_question_edit(t_id, q_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT created_by FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t or (t['created_by'] != uid and session.get('role') != 'admin'):
        conn.close(); return jsonify({'success': False, 'error': 'Ruxsat yo\'q'}), 403
    d = request.get_json() or {}
    conn.execute(
        'UPDATE tournament_questions SET question_text=?,option_a=?,option_b=?,option_c=?,option_d=?,correct_option=?,points=?,time_limit=? WHERE id=? AND tournament_id=?',
        (d.get('question_text',''), d.get('option_a',''), d.get('option_b',''),
         d.get('option_c',''), d.get('option_d',''), d.get('correct_option','A'),
         int(d.get('points') or 10), int(d.get('time_limit') or 30), q_id, t_id)
    )
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ── answer question ────────────────────────────────────────
@app.route('/api/tournaments/<int:t_id>/answer', methods=['POST'])
@login_required
def api_tournament_answer(t_id):
    uid = session['user_id']
    d = request.get_json() or {}
    q_id = d.get('question_id')
    chosen = (d.get('selected_option') or '').upper()
    conn = get_db()
    t = conn.execute('SELECT status FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t or t['status'] != 'active':
        conn.close(); return jsonify({'success': False, 'error': 'Musobaqa faol emas'}), 400
    mem = conn.execute('SELECT team_id FROM tournament_members WHERE tournament_id=? AND user_id=?', (t_id, uid)).fetchone()
    if not mem: conn.close(); return jsonify({'success': False, 'error': 'Siz bu musobaqada emassiz'}), 403
    existing = conn.execute('SELECT id FROM tournament_answers WHERE question_id=? AND user_id=?', (q_id, uid)).fetchone()
    if existing: conn.close(); return jsonify({'success': False, 'error': 'Allaqachon javob bergansiz'})
    q = conn.execute('SELECT correct_option, points FROM tournament_questions WHERE id=? AND tournament_id=?', (q_id, t_id)).fetchone()
    if not q: conn.close(); return jsonify({'success': False, 'error': 'Savol topilmadi'}), 404
    is_correct = 1 if chosen == q['correct_option'] else 0
    pts = q['points'] if is_correct else 0
    conn.execute(
        'INSERT INTO tournament_answers (question_id,tournament_id,user_id,team_id,selected_option,is_correct,points_earned) VALUES (?,?,?,?,?,?,?)',
        (q_id, t_id, uid, mem['team_id'], chosen, is_correct, pts)
    )
    if pts > 0:
        conn.execute('UPDATE tournament_members SET points_earned=points_earned+? WHERE tournament_id=? AND user_id=?', (pts, t_id, uid))
        conn.execute('UPDATE tournament_teams SET total_points=total_points+? WHERE id=?', (pts, mem['team_id']))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'is_correct': bool(is_correct), 'correct_option': q['correct_option'], 'points_earned': pts})

# ── leaderboard ────────────────────────────────────────────
@app.route('/api/tournaments/<int:t_id>/leaderboard')
@login_required
def api_tournament_leaderboard(t_id):
    conn = get_db()
    teams = conn.execute('SELECT * FROM tournament_teams WHERE tournament_id=? ORDER BY total_points DESC', (t_id,)).fetchall()
    result = []
    for tm in teams:
        top = conn.execute(
            'SELECT u.full_name, u.avatar, tme.points_earned FROM tournament_members tme '
            'JOIN users u ON tme.user_id=u.id WHERE tme.team_id=? ORDER BY tme.points_earned DESC LIMIT 5',
            (tm['id'],)
        ).fetchall()
        mc = conn.execute('SELECT COUNT(*) as c FROM tournament_members WHERE team_id=?', (tm['id'],)).fetchone()['c']
        result.append({**dict(tm), 'members': [dict(m) for m in top], 'member_count': mc})
    conn.close()
    return jsonify(result)

# ── activate / finish ──────────────────────────────────────
@app.route('/api/tournaments/<int:t_id>/activate', methods=['POST'])
@login_required
def api_tournament_activate(t_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT created_by FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t or (t['created_by'] != uid and session.get('role') != 'admin'):
        conn.close(); return jsonify({'success': False, 'error': 'Ruxsat yo\'q'}), 403
    conn.execute("UPDATE tournaments SET status='active' WHERE id=?", (t_id,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/tournaments/<int:t_id>/finish', methods=['POST'])
@login_required
def api_tournament_finish(t_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT created_by, prize_points FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t or (t['created_by'] != uid and session.get('role') != 'admin'):
        conn.close(); return jsonify({'success': False, 'error': 'Ruxsat yo\'q'}), 403
    conn.execute("UPDATE tournaments SET status='finished' WHERE id=?", (t_id,))
    winner = conn.execute('SELECT id FROM tournament_teams WHERE tournament_id=? ORDER BY total_points DESC LIMIT 1', (t_id,)).fetchone()
    if winner and t['prize_points']:
        for m in conn.execute('SELECT user_id FROM tournament_members WHERE team_id=?', (winner['id'],)).fetchall():
            add_points(m['user_id'], t['prize_points'], "Musobaqa g'alaba mukofoti")
            add_notification(m['user_id'], 'tournament', "🏆 Musobaqa g'olibisiz!", f"{t['prize_points']} ochko hisobingizga qo'shildi", f'/tournament/{t_id}')
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/tournaments/<int:t_id>/delete', methods=['POST'])
@login_required
def api_tournament_delete(t_id):
    uid = session['user_id']
    conn = get_db()
    t = conn.execute('SELECT created_by FROM tournaments WHERE id=?', (t_id,)).fetchone()
    if not t or (t['created_by'] != uid and session.get('role') != 'admin'):
        conn.close(); return jsonify({'success': False, 'error': 'Ruxsat yo\'q'}), 403
    conn.execute('DELETE FROM tournament_answers WHERE tournament_id=?', (t_id,))
    conn.execute('DELETE FROM tournament_members WHERE tournament_id=?', (t_id,))
    conn.execute('DELETE FROM tournament_teams WHERE tournament_id=?', (t_id,))
    conn.execute('DELETE FROM tournament_questions WHERE tournament_id=?', (t_id,))
    conn.execute('DELETE FROM tournaments WHERE id=?', (t_id,))
    conn.commit(); conn.close()
    return jsonify({'success': True})



# ══════════════════════════════════════════
# MASALALAR (PROBLEMS) PAGES & API
# ══════════════════════════════════════════

@app.route('/problems')
def problems_page():
    return render_template('problems.html')

@app.route('/problem/<int:pid>')
def problem_detail_page(pid):
    return render_template('problem_detail.html', pid=pid)

@app.route('/submissions')
def submissions_page():
    return render_template('submissions.html')

@app.route('/api/problems')
def api_problems():
    conn = get_db()
    uid = session.get('user_id', 0)
    diff = request.args.get('difficulty', '')
    rows = conn.execute('SELECT * FROM problems WHERE is_active=1 ORDER BY difficulty, points').fetchall()
    result = []
    for p in rows:
        if diff and p['difficulty'] != diff:
            continue
        solved = False
        if uid:
            s = conn.execute('SELECT id FROM submissions WHERE user_id=? AND problem_id=? AND status=?',
                             (uid, p['id'], 'accepted')).fetchone()
            solved = bool(s)
        result.append({
            'id': p['id'], 'title': p['title'], 'difficulty': p['difficulty'],
            'points': p['points'], 'solved': solved,
            'time_limit': p['time_limit'], 'memory_limit': p['memory_limit'],
            'category': p['category'] if 'category' in p.keys() else 'Asosiy'
        })
    conn.close()
    return jsonify(result)

@app.route('/api/problems/<int:pid>')
def api_problem_detail(pid):
    conn = get_db()
    p = conn.execute('SELECT * FROM problems WHERE id=? AND is_active=1', (pid,)).fetchone()
    if not p:
        conn.close(); return jsonify({'error': 'Masala topilmadi'}), 404
    uid = session.get('user_id', 0)
    solved = False
    if uid:
        s = conn.execute('SELECT id FROM submissions WHERE user_id=? AND problem_id=? AND status=?',
                         (uid, pid, 'accepted')).fetchone()
        solved = bool(s)
    conn.close()
    return jsonify({
        'id': p['id'], 'title': p['title'], 'description': p['description'],
        'input_format': p['input_format'], 'output_format': p['output_format'],
        'constraints': p['constraints'], 'example_input': p['example_input'],
        'example_output': p['example_output'], 'difficulty': p['difficulty'],
        'points': p['points'], 'time_limit': p['time_limit'],
        'memory_limit': p['memory_limit'], 'solved': solved
    })

@app.route('/api/submit', methods=['POST'])
@login_required
def api_submit():
    uid = session['user_id']
    d = request.get_json() or {}
    pid = int(d.get('problem_id', 0))
    language = d.get('language', 'python')
    code = d.get('code', '').strip()
    if not pid or not code:
        return jsonify({'error': "Masala va kod kerak"}), 400

    conn = get_db()
    p = conn.execute('SELECT * FROM problems WHERE id=? AND is_active=1', (pid,)).fetchone()
    if not p:
        conn.close(); return jsonify({'error': 'Masala topilmadi'}), 404

    import subprocess, tempfile, time as _time, sys as _sys, shutil as _shutil

    expected_out = (p['example_output'] or '').strip()
    sample_in = (p['example_input'] or '').strip()
    # Replace literal \n in stored strings with real newlines
    sample_in = sample_in.replace('\\n', '\n')
    time_limit = int(p['time_limit'] or 2)
    status = 'pending'
    runtime_ms = 0
    points_earned = 0
    _stderr_msg = ''
    _actual_out = ''

    def _normalize(s):
        """Normalize output for comparison: strip lines, remove trailing spaces"""
        return '\n'.join(line.rstrip() for line in s.strip().splitlines())

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            if language == 'python':
                code_file = os.path.join(tmpdir, 'sol.py')
                with open(code_file, 'w', encoding='utf-8') as cf:
                    cf.write(code)
                # Use the same Python executable that runs the server
                py_exe = _sys.executable or 'python3'
                t0 = _time.time()
                proc = subprocess.run(
                    [py_exe, code_file],
                    input=sample_in,
                    capture_output=True,
                    text=True,
                    timeout=time_limit + 5,
                    encoding='utf-8',
                    errors='replace'
                )
                runtime_ms = int((_time.time() - t0) * 1000)
                if proc.returncode != 0:
                    status = 'runtime_error'
                    _stderr_msg = (proc.stderr or '').strip()[:1000]
                else:
                    actual = _normalize(proc.stdout)
                    _actual_out = actual
                    status = 'accepted' if actual == _normalize(expected_out) else 'wrong_answer'

            elif language == 'cpp':
                # Check if g++ is available
                gpp = _shutil.which('g++') or _shutil.which('g++-12') or _shutil.which('g++-11') or _shutil.which('c++')
                if not gpp:
                    status = 'compile_error'
                    _stderr_msg = "Server da g++ (C++ kompilyatori) o'rnatilmagan. Python tilini ishlating."
                else:
                    src = os.path.join(tmpdir, 'sol.cpp')
                    exe = os.path.join(tmpdir, 'sol')
                    with open(src, 'w', encoding='utf-8') as cf:
                        cf.write(code)
                    comp = subprocess.run(
                        [gpp, '-O2', '-std=c++17', '-o', exe, src],
                        capture_output=True, text=True, timeout=20,
                        encoding='utf-8', errors='replace'
                    )
                    if comp.returncode != 0:
                        status = 'compile_error'
                        _stderr_msg = (comp.stderr or '').strip()[:1000]
                    else:
                        os.chmod(exe, 0o755)
                        t0 = _time.time()
                        proc = subprocess.run(
                            [exe],
                            input=sample_in,
                            capture_output=True,
                            text=True,
                            timeout=time_limit + 5,
                            encoding='utf-8',
                            errors='replace'
                        )
                        runtime_ms = int((_time.time() - t0) * 1000)
                        if proc.returncode != 0:
                            status = 'runtime_error'
                            _stderr_msg = (proc.stderr or '').strip()[:1000]
                        else:
                            actual = _normalize(proc.stdout)
                            _actual_out = actual
                            status = 'accepted' if actual == _normalize(expected_out) else 'wrong_answer'
            else:
                status = 'wrong_answer'
                _stderr_msg = f"'{language}' tili hozircha qo'llab-quvvatlanmaydi."

    except subprocess.TimeoutExpired:
        status = 'time_limit'
    except FileNotFoundError as e:
        status = 'compile_error'
        _stderr_msg = f"Dasturlash muhiti topilmadi: {e}. Python tilini sinab ko'ring."
    except PermissionError as e:
        status = 'runtime_error'
        _stderr_msg = f"Ruxsat xatosi: {e}"
    except Exception as e:
        status = 'runtime_error'
        _stderr_msg = str(e)[:500]

    already_solved = conn.execute(
        'SELECT id FROM submissions WHERE user_id=? AND problem_id=? AND status=?',
        (uid, pid, 'accepted')).fetchone()

    if status == 'accepted' and not already_solved:
        diff = (p['difficulty'] or 'easy').lower()
        if diff in ('medium', 'orta', 'o\'rta'):
            points_earned = 20
        elif diff in ('hard', 'qiyin'):
            points_earned = 40
        else:  # easy, oson, default
            points_earned = 10
        add_points(uid, points_earned, f"Masala hal qilindi: {p['title']}", pid)
        add_notification(uid, 'system', f"✅ Masala qabul qilindi!", f"{p['title']} — {points_earned} ball", f'/problem/{pid}')

    conn.execute('''INSERT INTO submissions (user_id,problem_id,language,code,status,runtime_ms,points_earned)
        VALUES (?,?,?,?,?,?,?)''', (uid, pid, language, code, status, runtime_ms, points_earned))
    conn.commit()
    sub_id = conn.execute('SELECT last_insert_rowid() as id').fetchone()['id']
    conn.close()

    status_labels = {
        'accepted': '✅ Qabul qilindi',
        'wrong_answer': '❌ Noto\'g\'ri javob',
        'runtime_error': '💥 Ishga tushirish xatosi',
        'compile_error': '🔧 Kompilyatsiya xatosi',
        'time_limit': '⏱️ Vaqt limiti oshdi',
    }
    return jsonify({
        'success': True,
        'status': status,
        'status_label': status_labels.get(status, status),
        'runtime_ms': runtime_ms,
        'points_earned': points_earned,
        'sub_id': sub_id,
        'stderr': _stderr_msg if status in ('runtime_error','compile_error') else '',
        'actual': _actual_out if status == 'wrong_answer' else '',
        'expected': expected_out if status == 'wrong_answer' else ''
    })

@app.route('/api/submissions')
@login_required
def api_my_submissions():
    uid = session['user_id']
    pid = request.args.get('problem_id')
    conn = get_db()
    q = '''SELECT s.*, p.title as problem_title, p.difficulty
           FROM submissions s JOIN problems p ON s.problem_id=p.id
           WHERE s.user_id=? '''
    params = [uid]
    if pid:
        q += ' AND s.problem_id=?'; params.append(int(pid))
    q += ' ORDER BY s.submitted_at DESC LIMIT 50'
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/problems/leaderboard')
def api_problems_leaderboard():
    conn = get_db()
    rows = conn.execute('''
        SELECT u.id, u.username, u.full_name, u.avatar, u.has_tick,
               COUNT(DISTINCT CASE WHEN s.status='accepted' THEN s.problem_id END) as solved_problems,
               COUNT(CASE WHEN s.status='accepted' THEN 1 END) as correct_submissions,
               SUM(CASE WHEN s.status='accepted' THEN s.points_earned ELSE 0 END) as total_points
        FROM users u
        LEFT JOIN submissions s ON u.id=s.user_id
        GROUP BY u.id
        HAVING solved_problems > 0
        ORDER BY solved_problems DESC, correct_submissions DESC, total_points DESC
        LIMIT 50
    ''').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ══════════════════════════════════════════
# GROUP INVITE LINKS
# ══════════════════════════════════════════

def _gen_invite_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

@app.route('/invite/<code>')
def invite_page(code):
    return render_template('invite.html', code=code)

@app.route('/api/groups/<slug>/invite-link', methods=['POST'])
@login_required
def api_group_invite_link(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT * FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if not mem or mem['role'] not in ('owner', 'admin'):
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403
    code = g['invite_code'] or _gen_invite_code()
    conn.execute('UPDATE groups SET invite_code=? WHERE id=?', (code, g['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'code': code, 'link': f'/invite/{code}'})

@app.route('/api/invite/<code>')
def api_invite_info(code):
    conn = get_db()
    g = conn.execute('SELECT id,name,slug,description,group_category,member_count,is_public,avatar FROM groups WHERE invite_code=?', (code,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Taklif topilmadi'}), 404
    conn.close()
    return jsonify(dict(g))

@app.route('/api/invite/<code>/join', methods=['POST'])
@login_required
def api_invite_join(code):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT * FROM groups WHERE invite_code=?', (code,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Taklif topilmadi'}), 404
    existing = conn.execute('SELECT id FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if existing:
        conn.close(); return jsonify({'success': True, 'slug': g['slug'], 'already': True})
    conn.execute('INSERT OR IGNORE INTO group_members (group_id,user_id,role) VALUES (?,?,?)', (g['id'], uid, 'member'))
    conn.execute('UPDATE groups SET member_count=member_count+1 WHERE id=?', (g['id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'slug': g['slug']})

# ══════════════════════════════════════════
# GROUP MODERATION (BAN, KICK, MUTE)
# ══════════════════════════════════════════

@app.route('/api/groups/<slug>/ban', methods=['POST'])
@login_required
def api_group_ban(slug):
    uid = session['user_id']
    d = request.get_json() or {}
    target_id = int(d.get('user_id', 0))
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if not mem or mem['role'] not in ('owner', 'admin'):
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403
    conn.execute('UPDATE group_members SET is_banned=1 WHERE group_id=? AND user_id=?', (g['id'], target_id))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/groups/<slug>/unban', methods=['POST'])
@login_required
def api_group_unban(slug):
    uid = session['user_id']
    d = request.get_json() or {}
    target_id = int(d.get('user_id', 0))
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if not mem or mem['role'] not in ('owner', 'admin'):
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403
    conn.execute('UPDATE group_members SET is_banned=0 WHERE group_id=? AND user_id=?', (g['id'], target_id))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/groups/<slug>/kick', methods=['POST'])
@login_required
def api_group_kick(slug):
    uid = session['user_id']
    d = request.get_json() or {}
    target_id = int(d.get('user_id', 0))
    conn = get_db()
    g = conn.execute('SELECT id,owner_id FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    if g['owner_id'] == target_id:
        conn.close(); return jsonify({'error': 'Owner-ni chiqarib bo\'lmaydi'}), 403
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if not mem or mem['role'] not in ('owner', 'admin'):
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403
    conn.execute('DELETE FROM group_members WHERE group_id=? AND user_id=?', (g['id'], target_id))
    conn.execute('UPDATE groups SET member_count=MAX(1,member_count-1) WHERE id=?', (g['id'],))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/groups/<slug>/mute', methods=['POST'])
@login_required
def api_group_mute(slug):
    uid = session['user_id']
    d = request.get_json() or {}
    target_id = int(d.get('user_id', 0))
    muted = int(d.get('muted', 1))
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if not mem or mem['role'] not in ('owner', 'admin'):
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403
    conn.execute('UPDATE group_members SET is_muted=? WHERE group_id=? AND user_id=?', (muted, g['id'], target_id))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/groups/<slug>/restrict', methods=['POST'])
@login_required
def api_group_restrict(slug):
    uid = session['user_id']
    d = request.get_json() or {}
    target_id = int(d.get('user_id', 0))
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if not mem or mem['role'] not in ('owner', 'admin'):
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403
    restrict_media = int(d.get('restrict_media', 0))
    restrict_tag = int(d.get('restrict_tag', 0))
    conn.execute('UPDATE group_members SET restrict_media=?,restrict_tag=? WHERE group_id=? AND user_id=?',
                 (restrict_media, restrict_tag, g['id'], target_id))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/groups/<slug>/members-moderation')
@login_required
def api_group_members_mod(slug):
    uid = session['user_id']
    conn = get_db()
    g = conn.execute('SELECT id FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if not mem or mem['role'] not in ('owner', 'admin'):
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403
    rows = conn.execute('''
        SELECT u.id, u.username, u.full_name, u.avatar, u.has_tick,
               gm.role, gm.is_muted, gm.is_banned, gm.restrict_media, gm.restrict_tag
        FROM group_members gm JOIN users u ON gm.user_id=u.id
        WHERE gm.group_id=? ORDER BY gm.role DESC, u.full_name
    ''', (g['id'],)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ══════════════════════════════════════════
# INVITE USER BY USERNAME
# ══════════════════════════════════════════

@app.route('/api/groups/<slug>/invite-user', methods=['POST'])
@login_required
def api_group_invite_user(slug):
    uid = session['user_id']
    d = request.get_json() or {}
    username = d.get('username', '').strip()
    conn = get_db()
    g = conn.execute('SELECT id,name FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    mem = conn.execute('SELECT role FROM group_members WHERE group_id=? AND user_id=?', (g['id'], uid)).fetchone()
    if not mem or mem['role'] not in ('owner', 'admin'):
        conn.close(); return jsonify({'error': 'Ruxsat yo\'q'}), 403
    target = conn.execute('SELECT id, username FROM users WHERE username=?', (username,)).fetchone()
    if not target:
        conn.close(); return jsonify({'error': 'Foydalanuvchi topilmadi'}), 404
    existing = conn.execute('SELECT id FROM group_members WHERE group_id=? AND user_id=?',
                            (g['id'], target['id'])).fetchone()
    if existing:
        conn.close(); return jsonify({'error': 'Bu foydalanuvchi allaqachon a\'zo'}), 400
    me = conn.execute('SELECT username FROM users WHERE id=?', (uid,)).fetchone()
    gid = g['id']
    add_notification(target['id'], 'system',
                     f"📨 Guruhga taklif",
                     f"@{me['username']} sizi «{g['name']}» guruhiga taklif qildi.",
                     f'/invite/{code}')
    conn.close()
    return jsonify({'success': True, 'message': f"@{username} ga taklif yuborildi"})

# ══════════════════════════════════════════
# GROUP LEADERBOARD (Study groups)
# ══════════════════════════════════════════

@app.route('/group/<slug>/leaderboard')
def group_leaderboard_page(slug):
    return render_template('group_leaderboard.html', slug=slug)

@app.route('/api/groups/<slug>/leaderboard')
def api_group_leaderboard(slug):
    conn = get_db()
    g = conn.execute('SELECT id,name,group_category FROM groups WHERE slug=?', (slug,)).fetchone()
    if not g:
        conn.close(); return jsonify({'error': 'Guruh topilmadi'}), 404
    rows = conn.execute('''
        SELECT u.id, u.username, u.full_name, u.avatar, u.has_tick,
               COUNT(DISTINCT CASE WHEN s.status='accepted' THEN s.problem_id END) as solved_problems,
               COUNT(CASE WHEN s.status='accepted' THEN 1 END) as correct_submissions,
               SUM(CASE WHEN s.status='accepted' THEN s.points_earned ELSE 0 END) as total_points
        FROM group_members gm
        JOIN users u ON gm.user_id=u.id
        LEFT JOIN submissions s ON u.id=s.user_id
        WHERE gm.group_id=? AND gm.is_banned=0
        GROUP BY u.id
        ORDER BY solved_problems DESC, correct_submissions DESC, total_points DESC
    ''', (g['id'],)).fetchall()
    conn.close()
    return jsonify({'group': dict(g), 'leaderboard': [dict(r) for r in rows]})






# ─────────────────────────────────────────
# BLOG / SHORTS / VIDEOS
# ─────────────────────────────────────────

UPLOAD_POST_VIDEO_DIR = os.path.join(ASSETS_DIR, 'post_videos')
UPLOAD_POST_THUMB_DIR = os.path.join(ASSETS_DIR, 'post_thumbs')
os.makedirs(UPLOAD_POST_VIDEO_DIR, exist_ok=True)
os.makedirs(UPLOAD_POST_THUMB_DIR, exist_ok=True)

@app.route('/blog')
def blog_page():
    return render_template('blog.html')

# ── Follow / Unfollow ──
@app.route('/api/follow/<int:uid>', methods=['POST'])
@login_required
def api_follow(uid):
    me = session['user_id']
    if me == uid:
        return jsonify({'error': "O'zingizni follow qilib bo'lmaydi"}), 400
    conn = get_db()
    existing = conn.execute('SELECT id FROM follows WHERE follower_id=? AND following_id=?', (me, uid)).fetchone()
    if existing:
        conn.execute('DELETE FROM follows WHERE follower_id=? AND following_id=?', (me, uid))
        conn.commit(); conn.close()
        return jsonify({'following': False})
    else:
        conn.execute('INSERT OR IGNORE INTO follows (follower_id, following_id) VALUES (?,?)', (me, uid))
        conn.commit(); conn.close()
        return jsonify({'following': True})

@app.route('/api/follow/status/<int:uid>')
@login_required
def api_follow_status(uid):
    me = session['user_id']
    conn = get_db()
    following = conn.execute('SELECT id FROM follows WHERE follower_id=? AND following_id=?', (me, uid)).fetchone()
    followers = conn.execute('SELECT COUNT(*) as c FROM follows WHERE following_id=?', (uid,)).fetchone()['c']
    following_count = conn.execute('SELECT COUNT(*) as c FROM follows WHERE follower_id=?', (uid,)).fetchone()['c']
    conn.close()
    return jsonify({'following': bool(following), 'followers': followers, 'following_count': following_count})

# ── Post Create ──
@app.route('/api/blog/post', methods=['POST'])
@login_required
def api_blog_post():
    uid = session['user_id']
    post_type = request.form.get('post_type', 'text')
    content = request.form.get('content', '').strip()
    title = request.form.get('title', '').strip()
    tags_raw = request.form.get('tags', '[]')
    promo_link = request.form.get('promo_link', '').strip()

    conn = get_db()
    # Premium check for promo_link
    if promo_link:
        user = conn.execute('SELECT role FROM users WHERE id=?', (uid,)).fetchone()
        if not user or user['role'] not in ('premium', 'admin'):
            conn.close()
            return jsonify({'error': 'Promo link faqat Premium foydalanuvchilar uchun!'}), 403

    if not content and post_type == 'text':
        conn.close()
        return jsonify({'error': 'Kontent kerak'}), 400

    media_url = ''
    thumbnail_url = ''

    if post_type in ('video', 'short'):
        vf = request.files.get('video')
        if vf and vf.filename:
            ext = vf.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_VIDEO:
                fname = f"pv_{uid}_{int(__import__('time').time())}.{ext}"
                vf.save(os.path.join(UPLOAD_POST_VIDEO_DIR, fname))
                media_url = f'/assets/post_videos/{fname}'
        tf = request.files.get('thumbnail')
        if tf and tf.filename:
            ext = tf.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_IMG:
                tname = f"pt_{uid}_{int(__import__('time').time())}.{ext}"
                tf.save(os.path.join(UPLOAD_POST_THUMB_DIR, tname))
                thumbnail_url = f'/assets/post_thumbs/{tname}'
    elif post_type == 'image':
        imgf = request.files.get('image')
        if imgf and imgf.filename:
            ext = imgf.filename.rsplit('.', 1)[-1].lower()
            if ext in ALLOWED_IMG:
                fname = f"pi_{uid}_{int(__import__('time').time())}.{ext}"
                imgf.save(os.path.join(UPLOAD_POST_THUMB_DIR, fname))
                media_url = f'/assets/post_thumbs/{fname}'

    try:
        tags = json.loads(tags_raw)
        if not isinstance(tags, list): tags = []
    except: tags = []

    conn.execute('''INSERT INTO posts (user_id,post_type,content,media_url,thumbnail_url,title,promo_link,tags)
        VALUES (?,?,?,?,?,?,?,?)''', (uid, post_type, content, media_url, thumbnail_url, title, promo_link, json.dumps(tags, ensure_ascii=False)))
    conn.commit()

    # Update user interests
    for tag in tags[:5]:
        conn.execute('''INSERT INTO user_interests (user_id,tag,weight) VALUES (?,?,1)
            ON CONFLICT(user_id,tag) DO UPDATE SET weight=weight+1''', (uid, tag))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ── Following list ──
@app.route('/api/following-list')
@login_required
def api_following_list():
    uid = session['user_id']
    conn = get_db()
    rows = conn.execute('''
        SELECT u.id, u.username, u.full_name, u.avatar, u.has_tick
        FROM follows f JOIN users u ON f.following_id=u.id
        WHERE f.follower_id=? ORDER BY f.created_at DESC LIMIT 20
    ''', (uid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

# ── Blog Feed ──
@app.route('/api/blog/feed')
def api_blog_feed():
    uid = session.get('user_id')
    page = int(request.args.get('page', 1))
    feed_type = request.args.get('type', 'all')
    q = request.args.get('q', '').strip()
    limit = 12
    offset = (page - 1) * limit

    conn = get_db()
    params = []
    where_parts = ["p.post_type != 'short'"]

    if feed_type == 'following' and uid:
        where_parts.append("p.user_id IN (SELECT following_id FROM follows WHERE follower_id=?)")
        params.append(uid)
    elif feed_type == 'my' and uid:
        where_parts.append("p.user_id=?")
        params.append(uid)

    if q:
        where_parts.append("(p.title LIKE ? OR p.content LIKE ? OR p.tags LIKE ?)")
        params += [f'%{q}%', f'%{q}%', f'%{q}%']

    where = 'WHERE ' + ' AND '.join(where_parts)

    rows = conn.execute(f'''
        SELECT p.*, u.username, u.full_name, u.avatar, u.has_tick, u.active_title
        FROM posts p JOIN users u ON p.user_id=u.id
        {where}
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
    ''', params + [limit, offset]).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        if uid:
            d['liked'] = bool(conn.execute('SELECT id FROM post_likes WHERE post_id=? AND user_id=?', (r['id'], uid)).fetchone())
            d['following'] = bool(conn.execute('SELECT id FROM follows WHERE follower_id=? AND following_id=?', (uid, r['user_id'])).fetchone())
        else:
            d['liked'] = False
            d['following'] = False
        try: d['tags'] = json.loads(r['tags'] or '[]')
        except: d['tags'] = []
        result.append(d)
    conn.close()
    return jsonify(result)

# ── Shorts Feed ──
@app.route('/api/shorts/feed')
def api_shorts_feed():
    uid = session.get('user_id')
    page = int(request.args.get('page', 1))
    q = request.args.get('q', '').strip()
    limit = 5
    offset = (page - 1) * limit

    conn = get_db()
    if q:
        rows = conn.execute('''
            SELECT p.*, u.username, u.full_name, u.avatar, u.has_tick
            FROM posts p JOIN users u ON p.user_id=u.id
            WHERE p.post_type='short' AND (p.title LIKE ? OR p.content LIKE ? OR p.tags LIKE ?)
            ORDER BY p.views DESC, p.likes_count DESC
            LIMIT ? OFFSET ?
        ''', (f'%{q}%', f'%{q}%', f'%{q}%', limit, offset)).fetchall()
    elif uid:
        # Interest-based: get user tags
        interests = conn.execute('SELECT tag FROM user_interests WHERE user_id=? ORDER BY weight DESC LIMIT 10', (uid,)).fetchall()
        interest_tags = [r['tag'] for r in interests]
        if interest_tags:
            placeholders = ','.join('?' * len(interest_tags))
            rows = conn.execute(f'''
                SELECT DISTINCT p.*, u.username, u.full_name, u.avatar, u.has_tick
                FROM posts p JOIN users u ON p.user_id=u.id
                WHERE p.post_type='short'
                ORDER BY (CASE WHEN {' + '.join([f"(p.tags LIKE ?)" for _ in interest_tags])} > 0 THEN 1 ELSE 0 END) DESC,
                         p.views DESC, p.created_at DESC
                LIMIT ? OFFSET ?
            ''', [f'%{t}%' for t in interest_tags] + [limit, offset]).fetchall()
        else:
            rows = conn.execute('SELECT p.*, u.username, u.full_name, u.avatar, u.has_tick FROM posts p JOIN users u ON p.user_id=u.id WHERE p.post_type=\'short\' ORDER BY p.views DESC, p.created_at DESC LIMIT ? OFFSET ?', (limit, offset)).fetchall()
    else:
        rows = conn.execute('SELECT p.*, u.username, u.full_name, u.avatar, u.has_tick FROM posts p JOIN users u ON p.user_id=u.id WHERE p.post_type=\'short\' ORDER BY p.views DESC, p.created_at DESC LIMIT ? OFFSET ?', (limit, offset)).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        if uid:
            d['liked'] = bool(conn.execute('SELECT id FROM post_likes WHERE post_id=? AND user_id=?', (r['id'], uid)).fetchone())
            d['following'] = bool(conn.execute('SELECT id FROM follows WHERE follower_id=? AND following_id=?', (uid, r['user_id'])).fetchone())
        else:
            d['liked'] = False
            d['following'] = False
        try: d['tags'] = json.loads(r['tags'] or '[]')
        except: d['tags'] = []
        result.append(d)
    conn.close()
    return jsonify(result)

# ── Post Like / Unlike ──
@app.route('/api/blog/like/<int:pid>', methods=['POST'])
@login_required
def api_post_like(pid):
    uid = session['user_id']
    conn = get_db()
    existing = conn.execute('SELECT id FROM post_likes WHERE post_id=? AND user_id=?', (pid, uid)).fetchone()
    if existing:
        conn.execute('DELETE FROM post_likes WHERE post_id=? AND user_id=?', (pid, uid))
        conn.execute('UPDATE posts SET likes_count=MAX(0,likes_count-1) WHERE id=?', (pid,))
        conn.commit(); conn.close()
        return jsonify({'liked': False})
    else:
        conn.execute('INSERT OR IGNORE INTO post_likes (post_id,user_id) VALUES (?,?)', (pid, uid))
        conn.execute('UPDATE posts SET likes_count=likes_count+1 WHERE id=?', (pid,))
        conn.commit(); conn.close()
        return jsonify({'liked': True})

# ── Post View count ──
@app.route('/api/blog/view/<int:pid>', methods=['POST'])
def api_post_view(pid):
    conn = get_db()
    conn.execute('UPDATE posts SET views=views+1 WHERE id=?', (pid,))
    conn.commit(); conn.close()
    return jsonify({'ok': True})

# ── Post Comments ──
@app.route('/api/blog/comments/<int:pid>')
def api_post_comments(pid):
    conn = get_db()
    rows = conn.execute('''
        SELECT c.*, u.username, u.full_name, u.avatar, u.has_tick
        FROM post_comments c JOIN users u ON c.user_id=u.id
        WHERE c.post_id=? ORDER BY c.created_at ASC LIMIT 50
    ''', (pid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/blog/comment/<int:pid>', methods=['POST'])
@login_required
def api_post_comment(pid):
    uid = session['user_id']
    d = request.get_json() or {}
    content = d.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Izoh yozing'}), 400
    conn = get_db()
    conn.execute('INSERT INTO post_comments (post_id,user_id,content) VALUES (?,?,?)', (pid, uid, content))
    conn.execute('UPDATE posts SET comments_count=comments_count+1 WHERE id=?', (pid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ── Delete Post ──
@app.route('/api/blog/post/<int:pid>', methods=['DELETE'])
@login_required
def api_delete_post(pid):
    uid = session['user_id']
    conn = get_db()
    p = conn.execute('SELECT user_id FROM posts WHERE id=?', (pid,)).fetchone()
    if not p:
        conn.close(); return jsonify({'error': 'Post topilmadi'}), 404
    user = conn.execute('SELECT role FROM users WHERE id=?', (uid,)).fetchone()
    if p['user_id'] != uid and user['role'] != 'admin':
        conn.close(); return jsonify({'error': "Ruxsat yo'q"}), 403
    conn.execute('DELETE FROM posts WHERE id=?', (pid,))
    conn.execute('DELETE FROM post_likes WHERE post_id=?', (pid,))
    conn.execute('DELETE FROM post_comments WHERE post_id=?', (pid,))
    conn.commit(); conn.close()
    return jsonify({'success': True})

# ── Profile Videos ──
@app.route('/api/profile/<int:uid>/videos')
def api_profile_videos(uid):
    conn = get_db()
    rows = conn.execute('''
        SELECT p.*, u.username, u.full_name, u.avatar
        FROM posts p JOIN users u ON p.user_id=u.id
        WHERE p.user_id=? AND p.post_type IN ('video','short')
        ORDER BY p.created_at DESC
    ''', (uid,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try: d['tags'] = json.loads(r['tags'] or '[]')
        except: d['tags'] = []
        result.append(d)
    return jsonify(result)

# ── Serve post videos/thumbs ──
@app.route('/assets/post_videos/<path:fn>')
def serve_post_video(fn): return send_from_directory(UPLOAD_POST_VIDEO_DIR, fn)

@app.route('/assets/post_thumbs/<path:fn>')
def serve_post_thumb(fn): return send_from_directory(UPLOAD_POST_THUMB_DIR, fn)



# ─────────────────────────────────────────
# YOUTUBE SHORTS
# ─────────────────────────────────────────

@app.route('/api/yt-shorts')
def api_yt_shorts():
    page = int(request.args.get('page', 1))
    q = request.args.get('q', '').strip()
    limit = 5
    offset = (page - 1) * limit
    conn = get_db()
    if q:
        rows = conn.execute('''SELECT * FROM yt_shorts WHERE is_active=1
            AND (title LIKE ? OR tags LIKE ?) ORDER BY RANDOM() LIMIT ? OFFSET ?''',
            (f'%{q}%', f'%{q}%', limit, offset)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM yt_shorts WHERE is_active=1 ORDER BY RANDOM() LIMIT ? OFFSET ?',
                           (limit, offset)).fetchall()
    conn.execute('UPDATE yt_shorts SET views=views+1 WHERE id IN ({})'.format(
        ','.join(str(r['id']) for r in rows) or '0'))
    conn.commit(); conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try: d['tags'] = json.loads(r['tags'] or '[]')
        except: d['tags'] = []
        result.append(d)
    return jsonify(result)

@app.route('/api/admin/yt-shorts', methods=['GET','POST','DELETE'])
@login_required
def api_admin_yt_shorts():
    conn = get_db()
    user = conn.execute('SELECT role FROM users WHERE id=?', (session['user_id'],)).fetchone()
    if not user or user['role'] not in ('admin','moderator'):
        conn.close(); return jsonify({'error':'Ruxsat yo\'q'}), 403
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM yt_shorts ORDER BY created_at DESC').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    elif request.method == 'POST':
        d = request.get_json() or {}
        yt_url = d.get('youtube_url','').strip()
        title = d.get('title','').strip()
        tags = d.get('tags','[]')
        # Extract video ID from URL
        import re as _re
        yt_id = None
        patterns = [r'shorts/([a-zA-Z0-9_-]+)', r'v=([a-zA-Z0-9_-]+)', r'youtu\.be/([a-zA-Z0-9_-]+)', r'^([a-zA-Z0-9_-]{11})$']
        for pat in patterns:
            m = _re.search(pat, yt_url)
            if m: yt_id = m.group(1); break
        if not yt_id:
            conn.close(); return jsonify({'error': 'Noto\'g\'ri YouTube URL'}), 400
        try:
            conn.execute('INSERT INTO yt_shorts (youtube_id,title,tags,added_by) VALUES (?,?,?,?)',
                        (yt_id, title or yt_id, tags, session['user_id']))
            conn.commit(); conn.close()
            return jsonify({'success': True, 'youtube_id': yt_id})
        except Exception as e:
            conn.close(); return jsonify({'error': str(e)}), 400
    elif request.method == 'DELETE':
        yt_id = request.args.get('id')
        conn.execute('DELETE FROM yt_shorts WHERE id=?', (yt_id,))
        conn.commit(); conn.close()
        return jsonify({'success': True})

# ─────────────────────────────────────────
# VIDEO STATISTICS
# ─────────────────────────────────────────

@app.route('/api/video/stats/<int:pid>')
def api_video_stats(pid):
    conn = get_db()
    p = conn.execute('SELECT * FROM posts WHERE id=?', (pid,)).fetchone()
    if not p: conn.close(); return jsonify({'error': 'Topilmadi'}), 404

    # Daily views last 14 days
    daily = conn.execute('''
        SELECT DATE(viewed_at) as day, COUNT(*) as cnt
        FROM video_stats WHERE post_id=? AND viewed_at >= DATE('now','-14 days')
        GROUP BY day ORDER BY day ASC
    ''', (pid,)).fetchall()

    # Total unique viewers
    unique_viewers = conn.execute('SELECT COUNT(DISTINCT viewer_id) FROM video_stats WHERE post_id=?', (pid,)).fetchone()[0]
    total_watch_sec = conn.execute('SELECT SUM(watch_seconds) FROM video_stats WHERE post_id=?', (pid,)).fetchone()[0] or 0
    avg_watch_sec = conn.execute('SELECT AVG(watch_seconds) FROM video_stats WHERE post_id=? AND watch_seconds>0', (pid,)).fetchone()[0] or 0

    # Ad clicks
    ad_clicks = conn.execute('SELECT COUNT(*) FROM ad_clicks WHERE post_id=?', (pid,)).fetchone()[0]

    conn.close()
    return jsonify({
        'views': p['views'] or 0,
        'likes': p['likes_count'] or 0,
        'comments': p['comments_count'] or 0,
        'shares': p['shares_count'] or 0,
        'unique_viewers': unique_viewers,
        'total_watch_min': round(total_watch_sec / 60, 1),
        'avg_watch_sec': round(avg_watch_sec, 0),
        'ad_clicks': ad_clicks,
        'daily_views': [{'day': r['day'], 'views': r['cnt']} for r in daily],
        'post_type': p['post_type'],
        'title': p['title'] or p['content'] or 'Video',
        'created_at': p['created_at'],
    })

@app.route('/api/video/watch/<int:pid>', methods=['POST'])
def api_video_watch(pid):
    uid = session.get('user_id', 0)
    d = request.get_json() or {}
    secs = min(int(d.get('seconds', 0)), 3600)
    conn = get_db()
    conn.execute('INSERT INTO video_stats (post_id,viewer_id,watch_seconds) VALUES (?,?,?)', (pid, uid, secs))
    conn.execute('UPDATE posts SET watch_seconds_total=COALESCE(watch_seconds_total,0)+? WHERE id=?', (secs, pid))
    # Update user total_video_views
    owner = conn.execute('SELECT user_id FROM posts WHERE id=?', (pid,)).fetchone()
    if owner:
        conn.execute('UPDATE users SET total_video_views=COALESCE(total_video_views,0)+1 WHERE id=?', (owner['user_id'],))
        # Check content creator
        _check_content_creator(conn, owner['user_id'])
    conn.commit(); conn.close()
    return jsonify({'ok': True})

@app.route('/api/ad/click/<int:pid>', methods=['POST'])
def api_ad_click(pid):
    uid = session.get('user_id', 0)
    conn = get_db()
    owner = conn.execute('SELECT user_id FROM posts WHERE id=?', (pid,)).fetchone()
    if owner:
        mon = conn.execute('SELECT id FROM monetization WHERE user_id=? AND status=?', (owner['user_id'], 'approved')).fetchone()
        if mon:
            conn.execute('INSERT INTO ad_clicks (post_id,monetization_id,viewer_id) VALUES (?,?,?)', (pid, mon['id'], uid))
            conn.execute('UPDATE monetization SET total_ad_clicks=total_ad_clicks+1 WHERE id=?', (mon['id'],))
            conn.commit()
    conn.close()
    return jsonify({'ok': True})

# ─────────────────────────────────────────
# CONTENT CREATOR CHECK
# ─────────────────────────────────────────

def _check_content_creator(conn, user_id):
    """Auto-grant Content Creator if criteria met"""
    try:
        u = conn.execute('''SELECT is_content_creator, total_video_views,
            (SELECT COUNT(*) FROM follows WHERE following_id=?) as subs,
            JULIANDAY('now') - JULIANDAY(created_at) as days_active
            FROM users WHERE id=?''', (user_id, user_id)).fetchone()
        if not u or u['is_content_creator']: return
        subs = u['subs'] or 0
        views = u['total_video_views'] or 0
        days = u['days_active'] or 0
        if subs >= 1000 and views >= 100000 and days >= 30:
            conn.execute('UPDATE users SET is_content_creator=1 WHERE id=?', (user_id,))
            # Add notification
            try:
                conn.execute('''INSERT INTO notifications (user_id,notif_type,title,body,ref_url)
                    VALUES (?,?,?,?,?)''', (user_id, 'system',
                    '◈ Content Creator!',
                    '1000+ obunachi va 100K+ ko\'rishga eting! Monetizatsiyani yoqing.',
                    '/profile/' + str(user_id)))
            except: pass
    except: pass

# ─────────────────────────────────────────
# MONETIZATSIYA
# ─────────────────────────────────────────

@app.route('/api/monetization/status')
@login_required
def api_monetization_status():
    uid = session['user_id']
    conn = get_db()
    u = conn.execute('''SELECT u.*, 
        JULIANDAY('now') - JULIANDAY(u.created_at) as days_active,
        (SELECT COUNT(*) FROM follows WHERE following_id=u.id) as subs,
        (SELECT COUNT(*) FROM posts WHERE user_id=u.id AND post_type IN ('video','short')) as video_count
        FROM users u WHERE u.id=?''', (uid,)).fetchone()
    if not u: conn.close(); return jsonify({'error': 'Topilmadi'}), 404

    mon = conn.execute('SELECT * FROM monetization WHERE user_id=?', (uid,)).fetchone()
    subs = u['subs'] or 0
    views = u['total_video_views'] or 0
    days = int(u['days_active'] or 0)
    videos = u['video_count'] or 0

    requirements = [
        {'label': '1000+ Obunachi', 'current': subs, 'target': 1000, 'met': subs >= 1000},
        {'label': '100K+ Umumiy ko\'rishlar', 'current': views, 'target': 100000, 'met': views >= 100000},
        {'label': '30 kun faol', 'current': days, 'target': 30, 'met': days >= 30},
    ]
    all_met = all(r['met'] for r in requirements)

    conn.close()
    return jsonify({
        'is_content_creator': bool(u['is_content_creator']),
        'requirements': requirements,
        'all_met': all_met,
        'status': mon['status'] if mon else 'none',
        'ad_title': mon['ad_title'] if mon else '',
        'ad_description': mon['ad_description'] if mon else '',
        'ad_link': mon['ad_link'] if mon else '',
        'ad_cta': mon['ad_cta'] if mon else 'Batafsil',
        'ad_bg_color': mon['ad_bg_color'] if mon else '#1a1a2e',
        'total_ad_clicks': mon['total_ad_clicks'] if mon else 0,
        'total_view_coins': mon['total_view_coins'] if mon else 0,
        'subs': subs, 'views': views, 'days': days, 'videos': videos,
    })

@app.route('/api/monetization/apply', methods=['POST'])
@login_required
def api_monetization_apply():
    uid = session['user_id']
    conn = get_db()
    u = conn.execute('''SELECT u.total_video_views, JULIANDAY('now') - JULIANDAY(u.created_at) as days_active,
        (SELECT COUNT(*) FROM follows WHERE following_id=u.id) as subs
        FROM users u WHERE u.id=?''', (uid,)).fetchone()
    if not u: conn.close(); return jsonify({'error': 'Topilmadi'}), 404

    subs = u['subs'] or 0
    views = u['total_video_views'] or 0
    days = int(u['days_active'] or 0)

    if not (subs >= 1000 and views >= 100000 and days >= 30):
        conn.close()
        return jsonify({'error': 'Talablar bajarilmagan. 1000+ obunachi, 100K+ ko\'rishlar va 30 kun faol bo\'lish kerak.'}), 400

    existing = conn.execute('SELECT id, status FROM monetization WHERE user_id=?', (uid,)).fetchone()
    if existing and existing['status'] == 'approved':
        conn.close(); return jsonify({'error': 'Monetizatsiya allaqachon yoqilgan'}), 400

    if existing:
        conn.execute('UPDATE monetization SET status=?, applied_at=CURRENT_TIMESTAMP WHERE user_id=?', ('approved', uid))
    else:
        conn.execute('INSERT INTO monetization (user_id, status, approved_at) VALUES (?,?,CURRENT_TIMESTAMP)', (uid, 'approved'))

    conn.execute('UPDATE users SET is_content_creator=1 WHERE id=?', (uid,))
    conn.commit(); conn.close()
    return jsonify({'success': True, 'message': 'Monetizatsiya muvaffaqiyatli yoqildi! ✅'})

@app.route('/api/monetization/settings', methods=['POST'])
@login_required
def api_monetization_settings():
    uid = session['user_id']
    d = request.get_json() or {}
    conn = get_db()
    mon = conn.execute('SELECT id FROM monetization WHERE user_id=? AND status=?', (uid, 'approved')).fetchone()
    if not mon: conn.close(); return jsonify({'error': 'Monetizatsiya yoqilmagan'}), 403

    conn.execute('''UPDATE monetization SET ad_title=?, ad_description=?, ad_link=?, ad_cta=?, ad_bg_color=?
        WHERE user_id=?''', (
        d.get('ad_title','')[:100],
        d.get('ad_description','')[:300],
        d.get('ad_link','')[:500],
        d.get('ad_cta','Batafsil')[:30],
        d.get('ad_bg_color','#1a1a2e')[:20],
        uid))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/monetization/ad/<int:uid_owner>')
def api_get_ad(uid_owner):
    conn = get_db()
    mon = conn.execute('SELECT * FROM monetization WHERE user_id=? AND status=? AND ad_link!=?',
                      (uid_owner, 'approved', '')).fetchone()
    conn.close()
    if not mon: return jsonify({'has_ad': False})
    return jsonify({
        'has_ad': True,
        'ad_title': mon['ad_title'],
        'ad_description': mon['ad_description'],
        'ad_link': mon['ad_link'],
        'ad_cta': mon['ad_cta'] or 'Batafsil',
        'ad_bg_color': mon['ad_bg_color'] or '#1a1a2e',
    })



# ─────────────────────────────────────────
# ─────────────────────────────────────────
# VACANCY POSITIONS
# ─────────────────────────────────────────

@app.route('/api/vacancies')
def api_get_vacancies():
    conn = get_db()
    rows = conn.execute('SELECT * FROM vacancy_positions WHERE is_active=1 ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/vacancies', methods=['GET','POST','DELETE'])
@login_required
def api_admin_vacancies():
    role = session.get('role','student')
    if role != 'admin':
        return jsonify({'error': 'Faqat admin'}), 403
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT * FROM vacancy_positions ORDER BY created_at DESC').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    elif request.method == 'POST':
        d = request.get_json() or {}
        title = d.get('title','').strip()[:200]
        description = d.get('description','').strip()[:1000]
        requirements = d.get('requirements','').strip()[:500]
        if not title: conn.close(); return jsonify({'error': 'Lavozim nomi kerak'}), 400
        conn.execute('INSERT INTO vacancy_positions (title,description,requirements,created_by) VALUES (?,?,?,?)',
                    (title, description, requirements, session['user_id']))
        conn.commit(); conn.close()
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        vid = request.args.get('id')
        conn.execute('DELETE FROM vacancy_positions WHERE id=?', (vid,))
        conn.commit(); conn.close()
        return jsonify({'success': True})

# TECH SUPPORT / TICKETS
# ─────────────────────────────────────────

@app.route('/api/support/submit', methods=['POST'])
def api_support_submit():
    d = request.get_json() or {}
    ticket_type = d.get('type', 'question')  # bug | vacancy | question
    subject = d.get('subject', '').strip()[:200]
    message = d.get('message', '').strip()[:2000]
    if not subject or not message:
        return jsonify({'error': 'Mavzu va xabar kerak'}), 400
    if ticket_type not in ('bug', 'vacancy', 'question'):
        return jsonify({'error': 'Noto\'g\'ri tur'}), 400

    uid = session.get('user_id', 0)
    uname = ''
    if uid:
        conn2 = get_db()
        u = conn2.execute('SELECT username FROM users WHERE id=?', (uid,)).fetchone()
        if u: uname = u['username']
        conn2.close()

    conn = get_db()
    conn.execute('''INSERT INTO support_tickets (user_id,username,ticket_type,subject,message)
        VALUES (?,?,?,?,?)''', (uid, uname, ticket_type, subject, message))

    # Send notification to admin/moderator
    # bug & question -> moderator+admin, vacancy -> admin only
    if ticket_type == 'vacancy':
        # Notify admins only
        admins = conn.execute("SELECT id FROM users WHERE role='admin'").fetchall()
        for a in admins:
            try:
                conn.execute('''INSERT INTO notifications (user_id,notif_type,title,body,ref_url)
                    VALUES (?,?,?,?,?)''', (a['id'], 'system',
                    f'💼 Yangi vakansiya arizasi', f'{subject}', '/admin'))
            except: pass
    else:
        # Notify moderators + admins
        staff = conn.execute("SELECT id FROM users WHERE role IN ('admin','moderator')").fetchall()
        icon = '🐛' if ticket_type == 'bug' else '❓'
        type_label = 'Bug xabari' if ticket_type == 'bug' else 'Savol'
        for s in staff:
            try:
                conn.execute('''INSERT INTO notifications (user_id,notif_type,title,body,ref_url)
                    VALUES (?,?,?,?,?)''', (s['id'], 'system',
                    f'{icon} {type_label}: {subject[:50]}',
                    f'Foydalanuvchi: {uname or "Mehmon"}', '/admin'))
            except: pass

    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/support/tickets')
@login_required
def api_support_tickets():
    uid = session['user_id']
    role = session.get('role', 'student')
    conn = get_db()
    if role == 'admin':
        # Admin sees all
        rows = conn.execute('SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT 100').fetchall()
    elif role == 'moderator':
        # Moderator sees bug and question only
        rows = conn.execute("SELECT * FROM support_tickets WHERE ticket_type IN ('bug','question') ORDER BY created_at DESC LIMIT 100").fetchall()
    else:
        # User sees their own
        rows = conn.execute('SELECT * FROM support_tickets WHERE user_id=? ORDER BY created_at DESC LIMIT 20', (uid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/support/reply/<int:tid>', methods=['POST'])
@login_required
def api_support_reply(tid):
    role = session.get('role', 'student')
    if role not in ('admin', 'moderator'):
        return jsonify({'error': 'Ruxsat yo\'q'}), 403
    d = request.get_json() or {}
    reply = d.get('reply', '').strip()
    if not reply: return jsonify({'error': 'Javob yozing'}), 400
    conn = get_db()
    t = conn.execute('SELECT * FROM support_tickets WHERE id=?', (tid,)).fetchone()
    if not t: conn.close(); return jsonify({'error': 'Topilmadi'}), 404
    conn.execute("UPDATE support_tickets SET reply=?,status='resolved',replied_by=?,replied_at=CURRENT_TIMESTAMP WHERE id=?",
                (reply, session['user_id'], tid))
    # Notify user
    if t['user_id']:
        try:
            conn.execute('''INSERT INTO notifications (user_id,notif_type,title,body,ref_url)
                VALUES (?,?,?,?,?)''', (t['user_id'], 'system',
                '✅ Murojatingizga javob berildi',
                f'"{t["subject"][:50]}" — Javob: {reply[:80]}', '/settings'))
        except: pass
    conn.commit(); conn.close()
    return jsonify({'success': True})


def ensure_cpp_compiler():
    """Try to ensure g++ is available, auto-install if on Debian/Ubuntu"""
    import shutil as _sh
    if _sh.which('g++') or _sh.which('g++-12') or _sh.which('g++-11'):
        return
    try:
        import subprocess as _sp
        print("  ⚙️  g++ topilmadi, o'rnatilmoqda...")
        r = _sp.run(['apt-get','install','-y','g++','build-essential'],
                    capture_output=True, timeout=90)
        if r.returncode == 0:
            print("  ✅  g++ muvaffaqiyatli o'rnatildi!")
        else:
            print("  ⚠️  g++ o'rnatilmadi (sudo kerak bo'lishi mumkin)")
    except Exception as e:
        print(f"  ⚠️  g++ o'rnatishda xato: {e}")

if __name__ == '__main__':
    os.makedirs(COURSES_DIR,exist_ok=True)
    init_db()
    ensure_cpp_compiler()
    print("="*55)
    print("  🎓  Bilimxon v3.0  —  Social Learning Platform")
    print("="*55)
    print("  🌐  http://localhost:5000")
    print("  👑  Admin : bobur / bobur_2012admin")
    print("  👤  Demo  : student / demo123")
    print("="*55)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
