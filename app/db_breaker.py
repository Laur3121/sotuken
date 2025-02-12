import sqlite3

def init_db():
    conn = sqlite3.connect("raspberries.db")
    cursor = conn.cursor()

    conn.execute("PRAGMA journal_mode=WAL;")


    # 既存テーブルを削除
    cursor.execute('DROP TABLE IF EXISTS raspberries')
    cursor.execute('DROP TABLE IF EXISTS temperature_logs')
    cursor.execute('DROP TABLE IF EXISTS cpu_usage_logs')
    cursor.execute('DROP TABLE IF EXISTS cpu_temperature_logs')

    # raspberriesテーブル再作成
    cursor.execute('''
    CREATE TABLE raspberries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT "Inactive",
        current_temperature REAL DEFAULT NULL,
        location TEXT DEFAULT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # temperature_logsテーブル再作成（logged_atをtimestampに変更）
    cursor.execute('''
    CREATE TABLE temperature_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raspberry_id INTEGER NOT NULL,
        temperature REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- logged_atをtimestampに変更
        FOREIGN KEY(raspberry_id) REFERENCES raspberries(id)
    )
    ''')

    # cpu_usage_logsテーブルにtimestampカラムがあることを確認
    cursor.execute('''
    CREATE TABLE cpu_usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raspberry_id INTEGER NOT NULL,
        cpu_usage REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- timestampカラムの追加
        FOREIGN KEY(raspberry_id) REFERENCES raspberries(id)
    )
    ''')

    # cpu_temperature_logsテーブルにtimestampカラムがあることを確認
    cursor.execute('''
    CREATE TABLE cpu_temperature_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raspberry_id INTEGER NOT NULL,
        cpu_temperature REAL NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- timestampカラムの追加
        FOREIGN KEY(raspberry_id) REFERENCES raspberries(id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database reset and initialized successfully.")

# 実行例
if __name__ == "__main__":
    init_db()
