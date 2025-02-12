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

# 評価する Raspberry Pi のデータを格納
raspberries = []
for row in rows:
    raspi = {
        'id': row[0],
        'name': row[1],
        'location': row[2],
        'temperature': row[3],
        'cpu_usage': row[4]
    }
    raspberries.append(raspi)

# 重み
w_t = 1  # 温度の重み
w_u = 1  # CPU使用率の重み
w_d = 1  # 位置の重み

# マイグレーション対象 Raspberry Pi を選ぶ
migration_scores = []
for raspi_x in raspberries:
    if raspi_x['temperature'] > 70:  # 70度を超える場合にスコアを計算
        for raspi_y in raspberries:
            if raspi_x['id'] != raspi_y['id']:  # 同じ Raspberry Pi への移動を避ける
                score = evaluate_migration(raspi_x, raspi_y, w_t, w_u, w_d)
                migration_scores.append({'from': raspi_x['name'], 'to': raspi_y['name'], 'score': score})

# 全てのスコアを表示
for migration in migration_scores:
    print(f"Score for migration from {migration['from']} to {migration['to']}: {migration['score']}")

# スコアが一番高いものを選ぶ
if migration_scores:
    best_migration = max(migration_scores, key=lambda x: x['score'])
    print(f"\nBest migration: {best_migration['from']} -> {best_migration['to']} with score: {best_migration['score']}")
else:
    print("\nNo Raspberry Pi exceeded 70°C.")