/* ═══════════════════════════════════════════════
   Bilimxon — i18n.js (Internationalization)
   Supported: uz (default), ru
═══════════════════════════════════════════════ */
const TRANSLATIONS = {
  uz: {
    // Nav
    nav_home: 'Bosh sahifa',
    nav_dashboard: 'Dashboard',
    nav_courses: 'Kurslar',
    nav_games: "O'yinlar",
    nav_leaderboard: 'Reyting',
    nav_problems: 'Masalalar',
    nav_blog: 'Blog',
    nav_chat: 'Chat',
    nav_social: "Do'stlar",
    nav_store: "Do'kon",
    nav_groups: 'Guruhlar',
    nav_ai: 'AI Yordamchi',
    nav_profile: 'Profil',
    nav_admin: 'Admin Panel',
    nav_login: 'Kirish',
    nav_logout: 'Chiqish',

    // Hero
    hero_badge: "O'zbekistonning #1 IT Ta'lim Platformasi",
    hero_title: 'Kelajak uchun dasturlash o\'rganing',
    hero_sub: 'HTML dan AI gacha — zamonaviy, interaktiv darslar bilan IT mutaxassis bo\'ling.',
    hero_start: 'Bepul Boshlash',
    hero_courses: 'Kurslarni Ko\'rish',
    hero_students: 'Talabalar',
    hero_courses_label: 'Kurslar',
    hero_completion: 'Bajarilish darajasi',

    // Courses
    courses_title: 'Barcha Kurslar',
    courses_sub: 'Zamonaviy IT sohasidagi eng muhim yo\'nalishlar',
    course_lessons: 'dars',
    course_start: 'Boshlash',
    course_continue: 'Davom etish',
    course_completed: '✅ Tugatildi',

    // Dashboard
    dash_title: 'Mening Dashboardim',
    dash_total: 'Jami Mavzular',
    dash_completed: 'Bajarilgan',
    dash_score: "O'rtacha Ball",
    dash_progress: 'Mening Rivojlanishim',
    dash_no_progress: 'Hali birorta kurs boshlanmagan',
    dash_go_courses: 'Kurslarni Ko\'rish',

    // Leaderboard
    lb_title: 'Reyting Jadvali',
    lb_sub: 'Eng yaxshi o\'quvchilar bilan raqobatlashing!',

    // Auth
    login_title: 'Xush kelibsiz!',
    login_sub: 'Bilimxon\'ga kiring',
    login_username: 'Foydalanuvchi nomi',
    login_password: 'Parol',
    login_btn: 'Kirish',
    auth_login: 'LOGIN',
    register_title: "Ro'yxatdan o'tish",
    register_btn: "Ro'yxatdan o'tish",
    auth_register: 'REGISTER',

    // Common
    save: 'Saqlash',
    cancel: 'Bekor qilish',
    close: 'Yopish',
    loading: 'Yuklanmoqda...',
    error: 'Xatolik',
    success: 'Muvaffaqiyat',
    no_data: 'Ma\'lumot yo\'q',
    points: 'ochko',
    yes: 'Ha',
    no: "Yo'q",

    // Store
    store_title: "Do'kon",
    store_sub: 'Ochkolar bilan profilingizni bezating',
    store_items: '🎁 Tovarlar',
    store_premium: '💎 Premium',
    store_gift: '🎁 Hadya',
    store_boxes: '📦 Qutichalar',
    store_howto: '❓ Qanday',
    store_themes: '🎨 Temalar',
    store_buy: 'Sotib Ol',
    store_owned: 'Mavjud',
    store_pts: 'ball',

    // Problems
    prob_title: '🧩 Masalalar',
    prob_sub: 'Algoritmik masalalarni yeching va ball to\'plang',
    prob_all: 'Hamma',
    prob_easy: '🟢 Oson',
    prob_medium: "🟡 O'rta",
    prob_hard: '🔴 Qiyin',
    prob_solved: 'Hal qilingan',
    prob_total: 'Jami masala',
    prob_my_sols: 'Mening Yechimlarim',
    prob_rating: 'Reyting',
    prob_search: 'Masala qidirish...',

    // Groups
    groups_title: 'Guruhlar va Kanallar',
    groups_sub: 'Qiziqishlaringizga mos guruhga qo\'shiling',
    groups_all: 'Barchasi',
    groups_my: 'Meniki',
    groups_create: '+ Yaratish',
    groups_join: 'Qo\'shilish',
    groups_joined: 'A\'zo',
    groups_members: 'a\'zo',
    groups_search: 'Guruh qidirish...',
    groups_empty: 'Guruh topilmadi',

    // Blog
    blog_feed: 'Tavsiya etilgan',
    blog_subs: 'Obunalar',
    blog_my: 'Mening postlarim',
    blog_upload: 'Yuklash',
    blog_follow: '+ Obuna',
    blog_following: '✓ Obunasiz',
    blog_shorts: 'Shorts',

    // Games
    games_title: 'O\'yinlar',
    games_sub: 'HTML5 o\'yinlar platformasi',
    games_upload: '🚀 O\'yin Yuklash',
    games_all: 'Hammasi',
    games_new: 'Yangi',
    games_popular: 'Mashhur',
    games_top: 'Top',

    // Settings
    settings_title: '⚙️ Sozlamalar',
    settings_sub: 'Sayt ko\'rinishini va xatti-harakatlarini o\'zingizga moslang',
    settings_save: '✅ Sozlamalarni Saqlash',
    settings_reset: '↺ Standart Ko\'rinishga Qaytarish',

    // Profile
    profile_about: 'Bosh sahifa',
    profile_videos: 'Videolar',
    profile_friends: 'Do\'stlar',
    profile_titles: 'Unvonlar',
    profile_inventory: 'Inventar',
    profile_income: '💰 Daromad',
    profile_edit: '⚙️ Tahrirlash',
    profile_followers: 'obunachi',
  },
  ru: {
    nav_home: 'Главная',
    nav_dashboard: 'Дашборд',
    nav_courses: 'Курсы',
    nav_games: 'Игры',
    nav_leaderboard: 'Рейтинг',
    nav_problems: 'Задачи',
    nav_blog: 'Блог',
    nav_chat: 'Чат',
    nav_social: 'Друзья',
    nav_store: 'Магазин',
    nav_groups: 'Группы',
    nav_ai: 'ИИ Помощник',
    nav_profile: 'Профиль',
    nav_admin: 'Панель Админа',
    nav_login: 'Войти',
    nav_logout: 'Выйти',

    hero_badge: '#1 IT Платформа Узбекистана',
    hero_title: 'Программирование для будущего',
    hero_sub: 'От HTML до AI — станьте IT специалистом с интерактивными уроками.',
    hero_start: 'Начать бесплатно',
    hero_courses: 'Смотреть курсы',
    hero_students: 'Студентов',
    hero_courses_label: 'Курсов',
    hero_completion: 'Процент завершения',

    courses_title: 'Все Курсы',
    courses_sub: 'Важнейшие направления в современной IT',
    course_lessons: 'урок',
    course_start: 'Начать',
    course_continue: 'Продолжить',
    course_completed: '✅ Завершён',

    dash_title: 'Мой Дашборд',
    dash_total: 'Всего Тем',
    dash_completed: 'Завершено',
    dash_score: 'Средний Балл',
    dash_progress: 'Мой Прогресс',
    dash_no_progress: 'Ещё ни один курс не начат',
    dash_go_courses: 'Смотреть курсы',

    lb_title: 'Таблица Лидеров',
    lb_sub: 'Соревнуйтесь с лучшими учениками!',

    login_title: 'Добро пожаловать!',
    login_sub: 'Войдите в Bilimxon',
    login_username: 'Имя пользователя',
    login_password: 'Пароль',
    login_btn: 'Войти',
    auth_login: 'ВХОД',
    register_title: 'Регистрация',
    register_btn: 'Зарегистрироваться',
    auth_register: 'РЕГИСТРАЦИЯ',

    save: 'Сохранить',
    cancel: 'Отмена',
    close: 'Закрыть',
    loading: 'Загрузка...',
    error: 'Ошибка',
    success: 'Успех',
    no_data: 'Нет данных',
    points: 'очко',
    yes: 'Да',
    no: 'Нет',

    // Store
    store_title: 'Магазин',
    store_sub: 'Украсьте профиль с помощью очков',
    store_items: 'Товары',
    store_premium: 'Премиум',
    store_gift: 'Подарок',
    store_boxes: 'Ящики',
    store_howto: 'Как это',
    store_themes: 'Темы',
    store_buy: 'Купить',
    store_owned: 'Куплено',
    store_pts: 'очков',

    // Problems
    prob_title: 'Задачи',
    prob_sub: 'Решайте алгоритмические задачи и зарабатывайте очки',
    prob_all: 'Все',
    prob_easy: 'Лёгкие',
    prob_medium: 'Средние',
    prob_hard: 'Сложные',
    prob_solved: 'Решено',
    prob_total: 'Всего задач',
    prob_my_sols: 'Мои решения',
    prob_rating: 'Рейтинг',
    prob_search: 'Поиск задачи...',

    // Groups
    groups_title: 'Группы и Каналы',
    groups_sub: 'Вступайте в группу или создайте свою',
    groups_all: 'Все',
    groups_my: 'Мои группы',
    groups_create: '+ Создать',
    groups_join: 'Вступить',
    groups_joined: 'Вступил',
    groups_members: 'участников',
    groups_search: 'Поиск группы...',
    groups_empty: 'Группы не найдены',

    // Blog
    blog_feed: 'Лента',
    blog_subs: 'Подписки',
    blog_my: 'Мои посты',
    blog_upload: 'Загрузить',
    blog_like: 'Нравится',
    blog_comment: 'Комментарии',
    blog_share: 'Поделиться',
    blog_follow: '+ Подписаться',
    blog_following: '✓ Подписан',
    blog_shorts: 'Shorts',
    blog_post_title: 'Заголовок',
    blog_post_content: 'Описание',
    blog_post_tags: 'Теги',

    // Games
    games_title: 'Игры',
    games_sub: 'Играй, оценивай, загружай свои HTML5 игры',
    games_upload: '🚀 Загрузить игру',
    games_play: 'Играть',
    games_all: 'Все игры',
    games_new: 'Новые',
    games_popular: 'Популярные',
    games_top: 'Топ',

    // Chat
    chat_title: 'Чат',
    chat_placeholder: 'Напишите сообщение...',
    chat_send: 'Отправить',
    chat_search: 'Поиск...',
    chat_friends: 'Друзья',
    chat_no_msgs: 'Нет сообщений',
    chat_start: 'Начните переписку',

    // Settings
    settings_title: 'Настройки',
    settings_sub: 'Настройте внешний вид и поведение сайта',
    settings_bg: 'Фон страницы',
    settings_accent: 'Акцентный цвет',
    settings_font: 'Шрифт',
    settings_effects: 'Эффекты',
    settings_notif: 'Уведомления',
    settings_privacy: 'Конфиденциальность',
    settings_account: 'Аккаунт',
    settings_save: 'Сохранить настройки',
    settings_reset: 'Сбросить',
    settings_support: 'Поддержка',

    // Support
    support_bug: 'Сообщить об ошибке',
    support_vacancy: 'Вакансия в команде',
    support_question: 'Задать вопрос',
    support_send: 'Отправить',
    support_sent: 'Отправлено!',

    // Profile
    profile_edit: 'Редактировать',
    profile_followers: 'подписчиков',
    profile_following: 'подписок',
    profile_videos: 'Видео',
    profile_friends: 'Друзья',
    profile_titles: 'Звания',
    profile_inventory: 'Инвентарь',
    profile_income: 'Доходы',
    profile_about: 'Главная',

    // Topbar
    topbar_points: 'очков',
    topbar_notifications: 'Уведомления',
  },

  en: {
    // Nav
    nav_home: 'Home',
    nav_dashboard: 'Dashboard',
    nav_courses: 'Courses',
    nav_games: 'Games',
    nav_leaderboard: 'Leaderboard',
    nav_problems: 'Problems',
    nav_blog: 'Blog',
    nav_chat: 'Chat',
    nav_social: 'Friends',
    nav_store: 'Store',
    nav_groups: 'Groups',
    nav_ai: 'AI Assistant',
    nav_profile: 'Profile',
    nav_admin: 'Admin Panel',
    nav_login: 'Login',
    nav_logout: 'Logout',

    // Hero
    hero_badge: "Uzbekistan's #1 IT Learning Platform",
    hero_title: 'Learn programming for the future',
    hero_sub: 'From HTML to AI — become an IT professional with modern, interactive lessons.',
    hero_start: 'Start Free',
    hero_courses: 'View Courses',
    hero_students: 'Students',
    hero_courses_label: 'Courses',
    hero_completion: 'Completion Rate',

    // Courses
    courses_title: 'All Courses',
    courses_sub: 'The most important directions in modern IT',
    course_lessons: 'lessons',
    course_start: 'Start',
    course_continue: 'Continue',
    course_completed: '✅ Completed',

    // Dashboard
    dash_title: 'My Dashboard',
    dash_total: 'Total Topics',
    dash_completed: 'Completed',
    dash_score: 'Average Score',
    dash_progress: 'My Progress',
    dash_no_progress: 'No course started yet',
    dash_go_courses: 'View Courses',

    // Problems
    prob_title: 'Algorithmic Problems',
    prob_sub: 'Solve algorithmic problems and earn points',
    prob_filter_all: 'All',
    prob_filter_easy: 'Easy',
    prob_filter_med: 'Medium',
    prob_filter_hard: 'Hard',
    prob_solved: 'Solved',
    prob_submit: 'Submit',
    prob_run: 'Run',
    prob_result: 'Result',

    // Store
    store_title: 'Store',
    store_sub: 'Customize your profile with points',
    store_buy: 'Buy',
    store_bought: 'Purchased',
    store_open: 'Open',
    store_points: 'points',

    // Groups
    groups_title: 'Groups',
    groups_create: 'Create Group',
    groups_join: 'Join',
    groups_members: 'members',
    groups_select: 'Select a group',
    groups_select_hint: 'Select a group from the left',

    // Chat
    chat_title: 'Chat',
    chat_placeholder: 'Type a message...',
    chat_send: 'Send',
    chat_search: 'Search...',
    chat_friends: 'Friends',
    chat_no_msgs: 'No messages',
    chat_start: 'Start a conversation',

    // Settings
    settings_title: 'Settings',
    settings_sub: 'Customize the site appearance and behavior',
    settings_bg: 'Page background',
    settings_accent: 'Accent color',
    settings_font: 'Font',
    settings_effects: 'Effects',
    settings_notif: 'Notifications',
    settings_privacy: 'Privacy',
    settings_account: 'Account',
    settings_save: 'Save settings',
    settings_reset: 'Reset',
    settings_support: 'Support',

    // Support
    support_bug: 'Report a bug',
    support_vacancy: 'Job vacancy',
    support_question: 'Ask a question',
    support_send: 'Send',
    support_sent: 'Sent!',

    // Profile
    profile_edit: 'Edit',
    profile_followers: 'followers',
    profile_following: 'following',
    profile_videos: 'Posts',
    profile_friends: 'Friends',
    profile_titles: 'Titles',
    profile_inventory: 'Inventory',
    profile_income: 'Income',
    profile_about: 'About',

    // Topbar
    topbar_points: 'points',
    topbar_notifications: 'Notifications',
  }
};

// Detect lang from cookie or default to uz
let CURRENT_LANG = (document.cookie.match(/lang=([^;]+)/) || [])[1] || 'uz';
if (!TRANSLATIONS[CURRENT_LANG]) CURRENT_LANG = 'uz';

function t(key) {
  return (TRANSLATIONS[CURRENT_LANG] || TRANSLATIONS.uz)[key] || TRANSLATIONS.uz[key] || key;
}

function applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const k = el.getAttribute('data-i18n');
    const val = t(k);
    if (val) el.textContent = val;
  });
}


/* ─────────────────────────────────────────
   DYNAMIC PAGE CONTENT TRANSLATIONS
   ───────────────────────────────────────── */
const PAGE_TRANSLATIONS_RU = {
  // Store
  "Do'kon": "Магазин",
  "Ochkolar bilan profilingizni bezating": "Украшайте профиль с помощью очков",
  "Tovarlar": "Товары",
  "Premium": "Премиум",
  "Hadya": "Подарок",
  "Qutichalar": "Ящики",
  "Qanday": "Как это",
  "Temalar": "Темы",
  "Sotib Ol": "Купить",
  "Mavjud": "Куплено",
  "Ochish": "Открыть",
  "ball": "очков",
  "Mystery Qutichalar": "Таинственные Ящики",
  "Har bir qutidan tasodifiy sovg'a chiqadi!": "Из каждого ящика выпадает случайный подарок!",

  // Problems
  "Masalalar": "Задачи",
  "Algoritmik masalalarni yeching va ball to'plang": "Решайте алгоритмические задачи и зарабатывайте очки",
  "Mening Yechimlarim": "Мои Решения",
  "Reyting": "Рейтинг",
  "Jami masala": "Всего задач",
  "Hal qilingan": "Решено",
  "Foiz": "Процент",
  "Masala qidirish...": "Поиск задачи...",
  "Barcha darajalar": "Все уровни",
  "Oson": "Лёгкие",
  "O'rta": "Средние",
  "Qiyin": "Сложные",
  "Hamma": "Все",
  "# Bo'lim": "# Категория",
  "Daraja": "Уровень",
  "Ball": "Очки",
  "Hal qilingan?": "Решено?",

  // Groups
  "Guruhlar va Kanallar": "Группы и Каналы",
  "Qiziqishlaringizga mos guruhga qo'shiling yoki o'zingiznikini yarating": "Вступайте в группу по интересам или создайте свою",
  "Guruh qidirish...": "Поиск группы...",
  "Barchasi": "Все",
  "Meniki": "Мои",
  "Guruhlar": "Группы",
  "Kanallar": "Каналы",
  "+ Yaratish": "+ Создать",
  "Guruhni tanlang": "Выберите группу",
  "Chap tarafdan guruh tanlang": "Выберите группу слева",
  "yoki yangi guruh yarating": "или создайте новую",
  "+ Guruh Yaratish": "+ Создать группу",

  // Games
  "O'yinlar": "Игры",
  "HTML5 o'yinlar platformasi": "Платформа HTML5 игр",
  "Hammasi": "Все",
  "Mashhur": "Популярные",
  "Yangi": "Новые",
  "Top": "Топ",
  "O'yin Yuklash": "Загрузить игру",
  "Yaqinda o'ynagan": "Недавно играл",

  // Blog
  "Tavsiya etilgan": "Рекомендуемые",
  "Obunalar": "Подписки",
  "Mening postlarim": "Мои посты",
  "Yuklash": "Загрузить",
  "Shorts": "Шортс",
  "Hammasini ko'rish →": "Смотреть всё →",
  "Yuklanmoqda...": "Загрузка...",

  // Chat
  "Chat": "Чат",
  "Do'stlar": "Друзья",

  // Settings
  "Sozlamalar": "Настройки",
  "Sayt ko'rinishini va xatti-harakatlarini o'zingizga moslang": "Настройте внешний вид и поведение сайта",
  "Sayt Orqa Foni": "Фон страницы",
  "Asosiy Rang (Accent)": "Акцентный цвет",
  "Shrift va Ko'rinish": "Шрифт и вид",
  "Effektlar": "Эффекты",
  "Bildirishnomalar": "Уведомления",
  "Maxfiylik": "Конфиденциальность",
  "Hisob": "Аккаунт",
  "Ko'rinish": "Отображение",
  "Sozlamalarni Saqlash": "Сохранить настройки",
  "Standart Ko'rinishga Qaytarish": "Сбросить настройки",

  // Leaderboard
  "Reyting Jadvali": "Таблица Лидеров",
  "Eng yaxshi o'quvchilar bilan raqobatlashing!": "Соревнуйтесь с лучшими учениками!",

  // Profile
  "Bosh sahifa": "Главная",
  "Videolar": "Видео",
  "Unvonlar": "Звания",
  "Inventar": "Инвентарь",
  "Tahrirlash": "Редактировать",
  "Daromad": "Доходы",

  // Support widget
  "Qo'llab-Quvvatlash": "Поддержка",
  "Bug xabari": "Сообщить об ошибке",
  "Savol": "Вопрос",
  "Ish": "Вакансия",
  "Mavzu": "Тема",
  "Xabar": "Сообщение",
  "Yuborish": "Отправить",
  "Yuborildi!": "Отправлено!",
  "Tez orada javob beramiz.": "Мы скоро ответим.",
  "Yopish": "Закрыть",
  "Mening murojaatlarim": "Мои обращения",
  "Javob:": "Ответ:",

  // Common
  "Yuklanmoqda": "Загрузка",
  "hozir": "только что",
  "Hozir": "Сейчас",
  "Obuna bo'ldingiz!": "Вы подписаны!",
  "Bekor qilindi": "Отменено",
  "Xato!": "Ошибка!",
  "Saqlandi": "Сохранено",
  "O'chirildi": "Удалено",
};

// ─── PAGE TRANSLATIONS EN ───────────────────────────────────
const PAGE_TRANSLATIONS_EN = {
  // Nav & common
  "Do'kon": "Store", "Bosh sahifa": "Home", "Reyting": "Leaderboard",
  "Masalalar": "Problems", "Guruhlar": "Groups", "O'yinlar": "Games",
  "Blog": "Blog", "Chat": "Chat", "Sozlamalar": "Settings",
  "Profil": "Profile", "Kirish": "Login", "Chiqish": "Logout",
  "Dashboard": "Dashboard", "Kurslar": "Courses", "Do'stlar": "Friends",

  // Store
  "Ochkolar bilan profilingizni bezating": "Customize your profile with points",
  "Tovarlar": "Items", "Premium": "Premium", "Hadya": "Gift",
  "Qutichalar": "Boxes", "Qanday": "How it works", "Temalar": "Themes",
  "Sotib Ol": "Buy", "Mavjud": "Owned", "Ochish": "Open",
  "ball": "points", "Mystery Qutichalar": "Mystery Boxes",

  // Problems
  "Algoritmik masalalarni yeching va ball to'plang": "Solve algorithmic problems and earn points",
  "Mening Yechimlarim": "My Solutions", "Jami masala": "Total problems",
  "Hal qilingan": "Solved", "Foiz": "Percentage",
  "Masala qidirish...": "Search problem...", "Barcha darajalar": "All levels",
  "Oson": "Easy", "O'rta": "Medium", "Qiyin": "Hard", "Hamma": "All",
  "# Bo'lim": "# Category", "Daraja": "Level", "Ball": "Points",
  "Hal qilingan?": "Solved?",

  // Groups
  "Guruhlar va Kanallar": "Groups & Channels",
  "Qiziqishlaringizga mos guruhga qo'shiling yoki o'zingiznikini yarating": "Join a group matching your interests or create your own",
  "Guruh qidirish...": "Search group...", "Barchasi": "All", "Meniki": "Mine",
  "Kanallar": "Channels", "+ Yaratish": "+ Create",
  "Guruhni tanlang": "Select a group", "Chap tarafdan guruh tanlang": "Select group from left",
  "yoki yangi guruh yarating": "or create a new one", "+ Guruh Yaratish": "+ Create Group",

  // Games
  "HTML5 o'yinlar platformasi": "HTML5 Games Platform",
  "Hammasi": "All", "Mashhur": "Popular", "Yangi": "New", "Top": "Top",
  "O'yin Yuklash": "Upload Game", "Yaqinda o'ynagan": "Recently played",
  "Aksiya": "Action", "Jumboq": "Puzzle", "Sport": "Sports",
  "Poyga": "Racing", "Strategiya": "Strategy", "Qo'rqinchli": "Horror",
  "Boshqa": "Other", "Top Rated": "Top Rated",

  // Blog
  "Tavsiya etilgan": "Recommended", "Obunalar": "Subscriptions",
  "Mening postlarim": "My posts", "Yuklash": "Upload",
  "Maqola yozish": "Write article",

  // Chat
  "Xabar yozing...": "Type a message...",
  "Birinchi xabarni yuboring 👋": "Send the first message 👋",

  // Settings
  "Sozlamalar": "Settings",
  "Sayt ko'rinishini va xatti-harakatlarini o'zingizga moslang": "Customize the site appearance",
  "Sayt Orqa Foni": "Page Background", "Asosiy Rang (Accent)": "Accent Color",
  "Shrift va Ko'rinish": "Font & Appearance", "Effektlar": "Effects",
  "Bildirishnomalar": "Notifications", "Maxfiylik": "Privacy",
  "Hisob": "Account", "Ko'rinish": "Display",
  "Sozlamalarni Saqlash": "Save Settings", "Standart Ko'rinishga Qaytarish": "Reset",
  "Til va Mintaqa": "Language & Region",

  // Leaderboard
  "Reyting Jadvali": "Leaderboard",
  "Eng yaxshi o'quvchilar bilan raqobatlashing!": "Compete with the best students!",

  // Profile
  "Videolar": "Posts", "Unvonlar": "Titles", "Inventar": "Inventory",
  "Tahrirlash": "Edit", "Daromad": "Income",

  // Lesson
  "Darsni tugatish ✅": "Complete Lesson ✅",
  "Testga o'tish 📝": "Take Quiz 📝", "← Orqaga": "← Back",
  "Keyingisi →": "Next →", "Natijani ko'rish 🏆": "See Results 🏆",
  "Tekshirish ✓": "Check ✓", "To'g'ri!": "Correct!",
  "Noto'g'ri": "Wrong", "Keyingi dars →": "Next lesson →",
  "Kursga qaytish 🎉": "Back to course 🎉", "Zo'r! Dars tugadi!": "Great! Lesson done!",
  "Davom eting!": "Keep going!", "XP to'plandi": "XP earned",
  "To'g'ri javob": "Correct answers", "Qoldi": "Remaining",
  "Kod namunasi": "Code example", "📋 Nusxa": "📋 Copy",
  "✅ Nusxalandi!": "✅ Copied!", "💻 Kod bor": "💻 Has code",
  "📝 Test bor": "📝 Has quiz", "🎬 Video bor": "🎬 Has video",

  // Course page
  "Umumiy progress": "Overall progress", "mavzu bajarildi": "topics done",
  "Dars boshlash": "Start Lesson", "Davom etish": "Continue",

  // Support widget
  "Qo'llab-Quvvatlash": "Support", "Bug xabari": "Report bug",
  "Savol": "Question", "Ish": "Job", "Mavzu": "Subject",
  "Xabar": "Message", "Yuborish": "Send", "Yuborildi!": "Sent!",
  "Tez orada javob beramiz.": "We will respond soon.",
  "Yopish": "Close", "Mening murojaatlarim": "My requests",

  // About/Legal pages
  "Biz haqimizda": "About Us", "Aloqa": "Contact",
  "Maxfiylik siyosati": "Privacy Policy", "Foydalanish shartlari": "Terms of Service",
  "Cookie siyosati": "Cookie Policy", "Yangiliklar": "News",
  "Platforma": "Platform", "Kompaniya": "Company", "Huquqiy": "Legal",
  "Barcha huquqlar himoyalangan.": "All rights reserved.",
  "Muhim sahifalar": "Important pages",

  // Streak
  "kunlik streak": "day streak", "Eng uzun streak": "Longest streak",
  "Jami faol kunlar": "Total active days", "Bugun faol": "Active today",
  "Bugun dars qilib streakni davom ettiring!": "Do a lesson today to continue your streak!",
  "Streak Mukofotlar": "Streak Rewards", "Erishildi!": "Achieved!",

  // Dashboard
  "Mening Dashboardim": "My Dashboard", "Jami Mavzular": "Total Topics",
  "Bajarilgan": "Completed", "O'rtacha Ball": "Average Score",
  "Mening Rivojlanishim": "My Progress",

  // Common
  "Yuklanmoqda...": "Loading...", "Yuklanmoqda": "Loading",
  "Qayta urinish": "Retry", "Bekor qilish": "Cancel",
  "Saqlash": "Save", "O'chirish": "Delete", "Qo'shish": "Add",
  "Tahrirlash": "Edit", "Ko'proq": "More", "Kam": "Less",
  "Ha": "Yes", "Yo'q": "No", "OK": "OK",
};

// Apply dynamic translation to all visible text nodes
function applyDynamicTranslation() {
  const dict = CURRENT_LANG === 'ru' ? PAGE_TRANSLATIONS_RU : CURRENT_LANG === 'en' ? PAGE_TRANSLATIONS_EN : null;
  if (!dict) return;

  // data-i18n elements
  applyI18n();

  const selectors = [
    '.page-title', '.page-sub', '.store-brand-title', '.store-brand-sub',
    '.stab', '.gs-title', '.gs-filter', '.section-title',
    '.feed-tab', '.cat-chip', '.sort-btn',
    'button[onclick*="stab"]', '.tab-btn', 'h1', 'h2', 'h3', 'h4',
    '.hero-title', '.hero-sub', '.stat-lbl', '.stat-card-lbl',
    '.ch-tab', '.g-cat', '.g-section-title', '.g-sitem-label',
    'label', '.scard-title', '.srow-label', '.srow-sub',
    '.type-name', '.type-desc', '.modal-head-title',
    '.gs-main-empty h3', '.gs-main-empty p',
    'th', '.admin-section-title', '.nav-label',
    '.dl-quiz-q', '.dl-result-title', '.dl-result-hint',
    '.dl-finish-title', '.dl-finish-sub', '.dl-stat-pill .lbl',
    '.dl-lesson-title', '.dl-btn', '.cr-unit-title h3',
    'button', 'a', 'span', 'p', 'div',
  ];

  const seen = new WeakSet();
  selectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      if (seen.has(el)) return;
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SCRIPT') return;
      if (el.children.length > 3) return;
      seen.add(el);
      const txt = el.textContent.trim();
      if (!txt || txt.length < 2 || txt.length > 200) return;
      if (dict[txt]) {
        for (let node of el.childNodes) {
          if (node.nodeType === 3 && node.textContent.trim() === txt) {
            node.textContent = dict[txt]; return;
          }
        }
        if (el.children.length === 0) el.textContent = dict[txt];
      }
    });
  });
}

function translatePlaceholders() {
  const dict = CURRENT_LANG === 'ru' ? PAGE_TRANSLATIONS_RU : CURRENT_LANG === 'en' ? PAGE_TRANSLATIONS_EN : null;
  if (!dict) return;
  document.querySelectorAll('[placeholder]').forEach(el => {
    const p = el.getAttribute('placeholder');
    if (dict[p]) el.setAttribute('placeholder', dict[p]);
  });
}

document.addEventListener('DOMContentLoaded', function() {
  applyI18n();
  if (CURRENT_LANG !== 'uz') {
    setTimeout(applyDynamicTranslation, 200);
    setTimeout(translatePlaceholders, 200);
    setTimeout(applyDynamicTranslation, 1000);
    setTimeout(applyDynamicTranslation, 2500);
  }
});

