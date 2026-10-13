import sqlite3

DB_NAME = "bot_database.db"

def init_db():
    """Создает таблицу для заявок с поддержкой статуса оплаты"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            name TEXT,
            phone TEXT,
            item_name TEXT,
            price INTEGER,
            is_paid INTEGER DEFAULT 0,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_request(user_id, username, name, phone, item_name="Консультация", price=0, is_paid=0):
    """Сохраняет заявку (или покупку) в базу данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requests (user_id, username, name, phone, item_name, price, is_paid) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, username, name, phone, item_name, price, is_paid)
    )
    conn.commit()
    conn.close()

def get_all_requests():
    """Выгружает все заявки и покупки для админа"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, phone, item_name, price, is_paid, date FROM requests ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
