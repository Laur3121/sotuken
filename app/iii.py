import sqlite3

# 新しいデータベースに接続
conn = sqlite3.connect('migration_history.db')
cursor = conn.cursor()

# マイグレーション履歴テーブルを作成
cursor.execute("""
CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_device TEXT,
    destination_device TEXT,
    reason TEXT,
    temperature REAL,
    migration_time TEXT
);
""")
conn.commit()
conn.close()
