import sqlite3
from datetime import datetime

def log_migration(source, destination, reason, temperature):
    """
    マイグレーション履歴を新しいデータベースに記録する関数
    """
    # 新しいデータベースに接続
    conn = sqlite3.connect('migration_history.db')  # 新しいデータベースファイルを指定
    cursor = conn.cursor()
    
    # マイグレーション情報を準備
    migration_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    query = """
    INSERT INTO migration_history (source_device, destination_device, reason, temperature, migration_time)
    VALUES (?, ?, ?, ?, ?)
    """
    values = (source, destination, reason, temperature, migration_time)
    
    # データを挿入
    cursor.execute(query, values)
    conn.commit()
    
    # 接続を閉じる
    conn.close()
    
    print(f"マイグレーション履歴を保存しました：{migration_time}")
