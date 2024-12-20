# app/init_db.py
import sqlite3

def init_db():
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS raspberries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        status TEXT NOT NULL,
        location INTEGER CHECK(location >= 1 AND location <= 9) NOT NULL
    )''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
