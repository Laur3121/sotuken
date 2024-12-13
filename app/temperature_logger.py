import sqlite3
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)

# 温度取得関数（仮の実装、実際の関数に合わせてください）
def get_local_temperature():
    # ローカルの温度取得処理を実装
    return 45.0  # 仮の温度

def get_remote_temperature(ip_address, username, password):
    # SSH経由でリモート温度を取得する処理を実装
    # 仮の戻り値として温度を返す
    return 50.0  # 仮の温度

def log_temperature():
    conn = sqlite3.connect("raspberries.db")
    cursor = conn.cursor()
    
    # Raspberry Pi の情報を取得
    cursor.execute("SELECT id, ip_address FROM raspberries")
    raspberries = cursor.fetchall()

    for raspberry in raspberries:
        id, ip_address = raspberry
        try:
            # IPアドレスが `localhost` の場合はローカルの温度を取得
            if ip_address == "localhost":
                temperature = get_local_temperature()
            else:
                # SSH接続でリモートの温度を取得
                temperature = get_remote_temperature(ip_address, "username", "password")

            # 取得した温度が数値であればログ出力してデータベースに保存
            if isinstance(temperature, float):
                logging.info(f"Temperature for Raspberry Pi {id} (IP: {ip_address}): {temperature}°C")
                cursor.execute(
                    "INSERT INTO temperature_logs (raspberry_id, temperature) VALUES (?, ?)",
                    (id, temperature),
                )
            else:
                logging.error(f"Failed to get temperature for Raspberry Pi {id}: {temperature}")
        except Exception as e:
            logging.error(f"Failed to log temperature for Raspberry Pi {id}: {str(e)}")

    conn.commit()
    conn.close()
