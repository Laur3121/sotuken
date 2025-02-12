import sqlite3
import re
import subprocess
import paramiko

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

def get_docker_container(ip_address, username, password):
    # 移行元 (raspi8) のコンテナ情報を取得するコマンド
    command = "docker ps --format '{{.Names}}'"  # コンテナ名のみを取得
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip_address, username=username, password=password)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode().strip()
    ssh.close()
    
    print(f"Output from docker ps on {ip_address}:\n{output}")  # デバッグ用に出力
    
    # コンテナ名をリストに格納、空白を取り除く
    containers = [name.strip() for name in output.split('\n') if name.strip()]
    
    print(f"Containers found: {containers}")  # コンテナ名を表示
    
    if not containers:
        raise ValueError("No running containers found")
    
    return containers[0]  # 最初のコンテナ名を返す

# SQLiteデータベース接続とデータ取得
conn = sqlite3.connect('raspberries.db')
conn.row_factory = sqlite3.Row  # 行を辞書型として取得
cursor = conn.cursor()

# 最新の温度とCPU使用率を取得するSQLクエリ
query = """
SELECT r.id, r.name, r.location,r.ip_address, 
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
        'ip_address':row[3],
        'temperature': row[4],
        'cpu_usage': row[5]
    }
    raspberries.append(raspi)

# 重み
w_t = 1  # 温度の重み
w_u = 1  # CPU使用率の重み
w_d = 1  # 位置の重み

# マイグレーション対象 Raspberry Pi を選ぶ
migration_scores = []
for raspi_x in raspberries:
    # 温度が文字列の場合、数値に変換
    temperature_x = float(raspi_x['temperature'])  # 温度を数値に変換
    
    if temperature_x > 70:  # 70度を超える場合にスコアを計算
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

    source_raspberry = next(raspi for raspi in raspberries if raspi['name'] == best_migration['from'])
    best_raspberry = next(raspi for raspi in raspberries if raspi['name'] == best_migration['to'])

    # IP アドレスを取得
    source_ip = source_raspberry['ip_address']
    destination_ip = best_raspberry['ip_address']
    
    # マイグレーション処理を実行
    source = best_migration['from']
    destination = best_migration['to']
    print(f"\nMigrating container from {source} to {destination}...")

    # 実際のコンテナマイグレーション処理（例: Docker）
    # ここでは Docker を使ってコンテナを移動するコマンドの一例を示します
    # コンテナ名を取得
    container_name = get_docker_container(source_ip, 'ubuntu', 'ubuntu')
    
    print(container_name)
    
    password = 'ubuntu'  # 実際のパスワードに置き換えてください

try:
    subprocess.run(['sshpass', '-p', password, 'ssh', source_ip, f'docker stop {container_name}'], check=True)
    subprocess.run(['sshpass', '-p', password, 'ssh', source_ip, f'docker commit {container_name} {container_name}_image'], check=True)
    subprocess.run(['sshpass', '-p', password, 'ssh', source_ip, f'docker save {container_name}_image | gzip > {container_name}.tar.gz'], check=True)
    subprocess.run(['sshpass', '-p', password, 'ssh', source_ip, f'docker rm {container_name}'], check=True)
    subprocess.run(['sshpass', '-p', password, 'scp', f'{source_ip}:{container_name}.tar.gz', f'{destination_ip}:~'], check=True)
    subprocess.run(['sshpass', '-p', password, 'ssh', destination_ip, f'docker load < {container_name}.tar.gz'], check=True)
    subprocess.run(['sshpass', '-p', password, 'ssh', destination_ip, f'docker run -d --name {container_name} {container_name}_image'], check=True)
    
    print(f"Successfully migrated container from {source_raspberry['name']} to {best_raspberry['name']}")
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
else:
    print("No suitable migration target found.")
