#!/usr/bin/env python3
"""
Bilimxon kurslarini senariydan to'ldirish
Bu skriptni bilimxon_final/ papkasida ishga tushiring:
  python seed_courses.py
"""
import sqlite3, json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bilimxon.db')
COURSES_DIR = os.path.join(BASE_DIR, 'courses')

def get_db():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

BOB_STRUCTURES = {
    "python": [
        {
            "title_uz": "1-Bob: Dasturlashga Kirish (Junior)",
            "title_ru": "1-Глава: Введение в программирование (Junior)",
            "mavzular": [
                "Dasturlash nima? Kompyuter qanday ishlaydi?",
                "O'zgaruvchilar va ma'lumot turlari",
                "Shartli operatorlar: if, elif, else",
                "Tsikllar: for va while",
                "Funksiyalar: def, parametrlar, return"
            ]
        },
        {
            "title_uz": "2-Bob: Ma'lumot Tuzilmalari (Junior-Middle)",
            "title_ru": "2-Глава: Структуры данных (Junior-Middle)",
            "mavzular": [
                "Ro'yxatlar (List) va ularni boshqarish",
                "Lug'atlar (Dictionary)",
                "To'plamlar (Set) va Kortejlar (Tuple)"
            ]
        },
        {
            "title_uz": "3-Bob: OOP — Ob'yektga Yo'naltirilgan Dasturlash (Middle)",
            "title_ru": "3-Глава: ООП — Объектно-ориентированное программирование (Middle)",
            "mavzular": [
                "Klasslar va Ob'yektlar",
                "Meros (Inheritance) va Polimorfizm",
                "Inkapsulatsiya va Abstraksiya"
            ]
        },
        {
            "title_uz": "Algoritmlar va Murakkablik (Middle-Senior)",
            "title_ru": "4-Глава: Алгоритмы и сложность (Middle-Senior)",
            "mavzular": [
                "Saralash algoritmlari: Bubble, Merge, Quick Sort",
                "Qidiruv algoritmlari: Linear va Binary Search"
            ]
        },
        {
            "title_uz": "Dizayn Naqshlari — Design Patterns (Senior)",
            "title_ru": "5-Глава: Паттерны проектирования (Senior)",
            "mavzular": [
                "Singleton va Factory Pattern",
                "Observer va Strategy Pattern",
                "SOLID Prinsiplari"
            ]
        }
    ],
    "csharp": [
        {
            "title_uz": "1-Bob: C# ga Kirish (Junior)",
            "title_ru": "1-Глава: Введение в C# (Junior)",
            "mavzular": [
                "C# nima? .NET platformasi va birinchi dastur",
                "O'zgaruvchilar, Ma'lumot Turlari va var",
                "Shartli Operatorlar, Switch Expression",
                "Tsikllar va LINQ asoslari",
                "Funksiyalar, Metodlar va Expression-bodied Members"
            ]
        },
        {
            "title_uz": "2-Bob: OOP — C# da Ob'yektga Yo'naltirilgan Dasturlash (Junior-Middle)",
            "title_ru": "2-Глава: ООП в C# (Junior-Middle)",
            "mavzular": [
                "Klasslar, Xususiyatlar (Properties) va Konstruktorlar",
                "Meros, Interface va Abstract Klass",
                "Generics, Collections va Exception Handling"
            ]
        },
        {
            "title_uz": "3-Bob: Zamonaviy C# Imkoniyatlari (Middle)",
            "title_ru": "3-Глава: Современные возможности C# (Middle)",
            "mavzular": [
                "Delegates, Events va Lambda",
                "Async/Await va Task Parallel Library",
                "Pattern Matching va Record Types (C# 9-12)"
            ]
        },
        {
            "title_uz": "4-Bob: ASP.NET Core va Entity Framework (Middle-Senior)",
            "title_ru": "4-Глава: ASP.NET Core и Entity Framework (Middle-Senior)",
            "mavzular": [
                "ASP.NET Core Web API — REST API yaratish",
                "Entity Framework Core — ORM bilan ishlash"
            ]
        },
        {
            "title_uz": "5-Bob: Arxitektura va Senior Mavzular (Senior)",
            "title_ru": "5-Глава: Архитектура и Senior темы (Senior)",
            "mavzular": [
                "SOLID Prinsiplari C# da Amaliy",
                "Design Patterns: Repository, CQRS, Mediator",
                "Performance Optimization va Memory Management"
            ]
        }
    ],
    "cpp": [
        {
            "title_uz": "1-Bob: C++ ga Kirish (Junior)",
            "title_ru": "1-Глава: Введение в C++ (Junior)",
            "mavzular": [
                "C++ nima? Birinchi dastur",
                "O'zgaruvchilar va Ma'lumot Turlari",
                "Kiritish/Chiqarish: cin, cout, getline",
                "Shartli Operatorlar va Switch",
                "Tsikllar: for, while, do-while",
                "Funksiyalar: parametrlar, qaytarish qiymati, overloading"
            ]
        },
        {
            "title_uz": "2-Bob: Massivlar, Ko'rsatkichlar va Xotira (Junior-Middle)",
            "title_ru": "2-Глава: Массивы, Указатели и Память (Junior-Middle)",
            "mavzular": [
                "Massivlar (Arrays) va std::vector",
                "Ko'rsatkichlar (Pointers) — C++ ning yuragi",
                "Dinamik Xotira: new, delete va Smart Pointers",
                "Satrlar: C-style string va std::string"
            ]
        },
        {
            "title_uz": "3-Bob: OOP — Ob'yektga Yo'naltirilgan Dasturlash (Middle)",
            "title_ru": "3-Глава: ООП в C++ (Middle)",
            "mavzular": [
                "Klasslar va Ob'yektlar, Konstruktor, Destruktor",
                "Meros (Inheritance) va Polimorfizm",
                "Operator Overloading va Copy Semantics"
            ]
        },
        {
            "title_uz": "4-Bob: Templates va STL (Middle-Senior)",
            "title_ru": "4-Глава: Шаблоны и STL (Middle-Senior)",
            "mavzular": [
                "Templates: funksiya va sinf shablonlari",
                "STL Konteynerlar: map, set, queue, stack, deque",
                "STL Algoritmlar va Lambda Funksiyalar"
            ]
        },
        {
            "title_uz": "5-Bob: Zamonaviy C++ va Senior Mavzular (Senior)",
            "title_ru": "5-Глава: Современный C++ и Senior темы (Senior)",
            "mavzular": [
                "Move Semantics va Perfect Forwarding",
                "Concurrency: Thread, Mutex, Atomic",
                "Zamonaviy C++20: Concepts, Ranges, Coroutines"
            ]
        }
    ],
    "html": [
        {
            "title_uz": "1-Bob: HTML — Veb-sahifaning Skeleti (Junior)",
            "title_ru": "1-Глава: HTML — Скелет веб-страницы (Junior)",
            "mavzular": [
                "HTML nima? Birinchi veb-sahifa",
                "Matn teglari: h1-h6, p, strong, em, br",
                "Havolalar va Rasmlar: a, img",
                "Ro'yxatlar va Jadvallar: ul, ol, li, table",
                "Formalar: form, input, button, select",
                "Semantik HTML: header, nav, main, section, article, footer"
            ]
        },
        {
            "title_uz": "2-Bob: CSS — Veb-sahifani Bezash (Junior-Middle)",
            "title_ru": "2-Глава: CSS — Оформление веб-страницы (Junior-Middle)",
            "mavzular": [
                "CSS nima? Selektorlar va xususiyatlar",
                "Box Model: margin, padding, border, width, height",
                "Flexbox — Moslashuvchan Tartib",
                "CSS Grid — 2D Tartib",
                "Responsive Design: Media Queries va Mobile First",
                "CSS Animatsiyalar va Tranzitsiyalar"
            ]
        },
        {
            "title_uz": "3-Bob: JavaScript — Veb-sahifani Jonlantirish (Junior-Middle)",
            "title_ru": "3-Глава: JavaScript — Оживление веб-страницы (Junior-Middle)",
            "mavzular": [
                "JS asoslari: o'zgaruvchilar, turlar, operatorlar",
                "DOM bilan ishlash: getElementById, querySelector",
                "Hodisalar (Events): click, input, submit, keydown",
                "Massivlar va Ob'yektlar bilan ishlash",
                "Asinxron JS: Promise, async/await, Fetch API"
            ]
        },
        {
            "title_uz": "4-Bob: Amaliy Loyihalar — HTML+CSS+JS Birgalikda (Middle)",
            "title_ru": "4-Глава: Практические проекты (Middle)",
            "mavzular": [
                "To-Do List: DOM + Events + LocalStorage",
                "Fetch API bilan foydalanuvchilar ro'yxati"
            ]
        },
        {
            "title_uz": "5-Bob: Zamonaviy JS va Senior Mavzular",
            "title_ru": "5-Глава: Современный JS и Senior темы",
            "mavzular": [
                "ES6+ — Zamonaviy JavaScript Imkoniyatlari",
                "Performance va Optimizatsiya: Debounce, Throttle, Lazy Loading",
                "Web API lar: Geolocation, WebStorage, Canvas, Web Workers"
            ]
        }
    ]
}

def seed():
    conn = get_db()
    cur = conn.cursor()
    
    for slug, bobs in BOB_STRUCTURES.items():
        print(f"\n🔄 {slug.upper()} kursi yangilanmoqda...")
        
        # Delete existing bobs and mavzular for this course
        cur.execute("DELETE FROM quiz_questions WHERE mavzu_id IN (SELECT id FROM mavzular WHERE course_slug=?)", (slug,))
        cur.execute("DELETE FROM mavzular WHERE course_slug=?", (slug,))
        cur.execute("DELETE FROM bobs WHERE course_slug=?", (slug,))
        
        lesson_num = 1
        for bob_idx, bob in enumerate(bobs, 1):
            cur.execute(
                "INSERT INTO bobs (course_slug, title_uz, title_ru, sort_order) VALUES (?,?,?,?)",
                (slug, bob["title_uz"], bob["title_ru"], bob_idx)
            )
            bob_id = cur.lastrowid
            print(f"  📚 {bob['title_uz']}")
            
            for mavzu_idx, mavzu_title in enumerate(bob["mavzular"], 1):
                # Read lesson content
                ldir = os.path.join(COURSES_DIR, slug, f"lesson{lesson_num}")
                content = ""
                quiz_data = {"questions": []}
                code_example = ""
                
                if os.path.exists(ldir):
                    txt_path = os.path.join(ldir, "lesson.txt")
                    if os.path.exists(txt_path):
                        with open(txt_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        # Extract code block
                        import re
                        code_match = re.search(r"```\n(.+?)\n```", content, re.DOTALL)
                        if code_match:
                            code_example = code_match.group(1)
                    
                    quiz_path = os.path.join(ldir, "quiz.json")
                    if os.path.exists(quiz_path):
                        with open(quiz_path, "r", encoding="utf-8") as f:
                            quiz_data = json.load(f)
                
                cur.execute("""
                    INSERT INTO mavzular 
                    (bob_id, course_slug, title_uz, title_ru, content_uz, content_ru, code_example, sort_order, points_reward)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (bob_id, slug, mavzu_title, mavzu_title, content, content, code_example, mavzu_idx, 10))
                mavzu_id = cur.lastrowid
                
                # Insert quiz questions
                for q in quiz_data.get("questions", []):
                    opts_json = json.dumps(q.get("options", []), ensure_ascii=False)
                    cur.execute("""
                        INSERT INTO quiz_questions 
                        (mavzu_id, question_uz, question_ru, options_uz, options_ru, correct_idx, explanation_uz, explanation_ru)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (
                        mavzu_id,
                        q.get("question", ""),
                        q.get("question", ""),
                        opts_json, opts_json,
                        q.get("correct", 0),
                        q.get("explanation", ""),
                        q.get("explanation", ""),
                    ))
                
                print(f"    ✅ {mavzu_title[:60]} [{len(quiz_data.get('questions',[]))} savol]")
                lesson_num += 1
    
    conn.commit()
    conn.close()
    print("\n✅ Barcha kurslar muvaffaqiyatli yangilandi!")
    print("📌 Eslatma: Agar server ishlab turgan bo'lsa, uni qayta ishga tushiring.")

if __name__ == "__main__":
    seed()
