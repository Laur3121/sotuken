import sqlite3
import re

# ユークリッド距離を計算する関数
def euclidean_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)

# スコア計算の関数
def evaluate_migration(raspi_x, raspi_y, w_t, w_u, w_d):
    temp_diff = raspi_x['temperature'] - raspi_y['temperature']
    cpu_usage_x = raspi_x['cpu_usage']
    cpu_usage_y = raspi_y['cpu_usage']
    cpu_diff = (1 - cpu_usage_y / 100)
    
    location_x = raspi_x['location']
    location_y = raspi_y['location']
    if location_x and location_y:
        match_x = re.search(r'x(\d+)y(\d+)', location_x)
        match_y = re.search(r'x(\d+)y(\d+)', location_y)
        if match_x and match_y:
            x1, y1 = int(match_x.group(1)), int(match_x.group(2))
            x2, y2 = int(match_y.group(1)), int(match_y.group(2))
            location_diff = euclidean_distance(x1, y1, x2, y2)
        else:
            location_diff = 0
    else:
        location_diff = 0

    # 評価式
    score = (w_t * temp_diff) + (w_u * cpu_diff) + (w_d * location_diff)
    return score

# SQLiteデータベース接続とデータ取得
conn = sqlite3.connect('raspberries.db')
conn.row_factory = sqlite3.Row  # 行を辞書型として取得
cursor = conn.cursor()

# 最新の温度とCPU使用率を取得するSQLクエリ
query = """
SELECT r.id, r.name, r.location, 
       (SELECT cpu_temperature FROM cpu_temperature_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_temp,
       (SELECT cpu_usage FROM cpu_usage_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_cpu_usage
FROM raspberries r
WHERE r.status = 'Active';
"""

# クエリを実行
cursor.execute(query)
rows = cursor.fetchall()

# 70度を超える場合のスコア計算
for row in rows:
    temperature = row['latest_temp']
    if temperature > 70:
        # サンプルとして、重みを指定
        w_t = 1  # 温度の重み
        w_u = 0.5  # CPU使用率の重み
        w_d = 0.2  # 位置情報の重み

        # 同じ場所のデバイスと比較するために、同じ温度を持つ他のデバイスを探してスコア計算
        for compare_row in rows:
            if row['id'] != compare_row['id']:
                score = evaluate_migration(
                    {'temperature': row['latest_temp'], 'cpu_usage': row['latest_cpu_usage'], 'location': row['location']},
                    {'temperature': compare_row['latest_temp'], 'cpu_usage': compare_row['latest_cpu_usage'], 'location': compare_row['location']},
                    w_t, w_u, w_d
                )
                print(f"Score for migration from {row['name']} to {compare_row['name']}: {score}")

# 接続を閉じる
conn.close()
