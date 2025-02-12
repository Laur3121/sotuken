import sqlite3
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from .utils import get_local_temperature, get_remote_temperature

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler("temperature_logs.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_handler)

# データベース接続関数
def get_db_connection():
    return sqlite3.connect("raspberries.db")

# 温度取得関数（ローカル/リモート）
def get_temperature_for_raspberry(id, ip_address):
    try:
        # IPアドレスが `localhost` の場合はローカルの温度を取得
        if ip_address == "localhost":
            temperature = get_local_temperature()
        else:
            # SSH接続でリモートの温度を取得
            temperature = get_remote_temperature(ip_address, "username", "password")
        
        # 取得した温度が数値であれば返す
        if isinstance(temperature, float):
            return (id, temperature)
        else:
            logging.error(f"Failed to get temperature for Raspberry Pi {id} (IP: {ip_address}): {temperature}")
            return None
    except Exception as e:
        logging.error(f"Error while getting temperature for Raspberry Pi {id} (IP: {ip_address}): {e}")
        return None

# 温度データをデータベースに保存
def save_temperature_to_db(raspberry_id, temperature):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO temperature_logs (raspberry_id, temperature) VALUES (?, ?)",
                (raspberry_id, temperature),
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Failed to save temperature for Raspberry Pi {raspberry_id}: {e}")

# 定期的に温度を取得して保存する関数
def log_temperature_periodically(interval=60):
    while True:
        try:
            conn = sqlite3.connect("raspberries.db")
            cursor = conn.cursor()
            
            # Raspberry Pi の情報を取得
            cursor.execute("SELECT id, ip_address FROM raspberries")
            raspberries = cursor.fetchall()
            conn.commit()
            conn.close()

            # ThreadPoolExecutorを使って並列で温度を取得
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for raspberry in raspberries:
                    id, ip_address = raspberry
                    futures.append(executor.submit(get_temperature_for_raspberry, id, ip_address))
                
                for future in futures:
                    result = future.result()
                    if result:
                        raspberry_id, temperature = result
                        save_temperature_to_db(raspberry_id, temperature)
        
            # 60秒ごとに温度を取得
            time.sleep(interval)

        except Exception as e:
            logging.error(f"Error in log_temperature_periodically: {e}")
            time.sleep(interval)


