import sqlite3

DB_NAME = "bot_database.db"

def init_db():
    """Создает таблицу для заявок, если её еще нет"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            name TEXT,
            phone TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_request(user_id, username, name, phone):
    """Сохраняет новую заявку от клиента в базу данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO requests (user_id, username, name, phone) VALUES (?, ?, ?, ?)",
        (user_id, username, name, phone)
    )
    conn.commit()
    conn.close()

def get_all_requests():
    """Выгружает все заявки для админ-панели"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, name, phone, date FROM requests ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
