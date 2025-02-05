import re
import logging

# 重みを設定する
w_t = 1  # 温度の重み
w_u = 1  # CPU使用率の重み
w_d = 1  # 位置の重み

# 仮データ
raspi_x = {
    'temperature': 55,  # 温度
    'cpu_usage': 45,  # CPU使用率
    'location': 'r1x1y1',  # 位置
}

raspi_y = {
    'temperature': 40,  # 温度
    'cpu_usage': 50,  # CPU使用率
    'location': 'r1x2y2',  # 位置
}

# ユークリッド距離を計算する関数
def euclidean_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)

# 評価式を計算する関数
def evaluate_migration(raspi_x, raspi_y, w_t, w_u, w_d):
    # 温度の差
    temp_diff = raspi_x['temperature'] - raspi_y['temperature']
    
    # CPU使用率の差
    cpu_usage_x = raspi_x['cpu_usage']
    cpu_usage_y = raspi_y['cpu_usage']
    cpu_diff = (1 - cpu_usage_y / 100)
    
    # 位置の距離
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

# スコアを計算して表示
score = evaluate_migration(raspi_x, raspi_y, w_t, w_u, w_d)
print(f"Calculated migration score: {score}")