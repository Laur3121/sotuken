import sqlite3
import logging
import time
import paramiko
import threading

# ログ設定
logging.basicConfig(level=logging.INFO)

# データベースから最新の温度情報を取得する関数
def get_latest_temperatures():
    conn = sqlite3.connect("raspberries.db")
    cursor = conn.cursor()

    # 最新の温度データを取得
    cursor.execute("""
        SELECT r.ip_address, t.temperature, t.timestamp
        FROM temperature_logs t
        JOIN raspberries r ON t.raspberry_id = r.id
        ORDER BY t.timestamp DESC
        LIMIT 5
    """)
    temperatures = cursor.fetchall()
    conn.close()

    return temperatures

# 温度取得関数（リモートの Raspberry Pi の温度を取得）
def get_remote_temperature(host, username, password, timeout=10):
    """
    リモートデバイスから温度を取得する。
    """
    try:
        # SSHクライアントの初期化
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # SSH接続
        logging.info(f"Connecting to {host}...")
        client.connect(hostname=host, username=username, password=password, timeout=timeout)

        # vcgencmdコマンドを実行して温度を取得
        stdin, stdout, stderr = client.exec_command("vcgencmd measure_temp")
        output = stdout.read().decode('utf-8').strip()

        # 接続を閉じる
        client.close()

        # 結果をパースして温度を返す
        temp_str = output.replace("temp=", "").replace("'C", "")
        return float(temp_str)
    except Exception as e:
        logging.error(f"Failed to get temperature from {host}: {str(e)}")
        return None

# データベース接続の作成
def create_connection():
    """
    データベース接続を作成して返す
    """
    conn = sqlite3.connect("raspberries.db")
    return conn

import datetime

def log_temperature(conn, cursor):
    """
    データベース内の Raspberry Pi 情報に基づいて温度を取得し、記録する。
    """
    # Raspberry Pi の情報を取得
    cursor.execute("SELECT id, ip_address FROM raspberries")
    raspberries = cursor.fetchall()

    for raspberry in raspberries:
        id, ip_address = raspberry
        try:
            # SSH接続でリモートの温度を取得
            temperature = get_remote_temperature(ip_address, "ubuntu", "ubuntu")

            if temperature is not None:
                # 取得した温度と現在時刻をデータベースに保存
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO temperature_logs (raspberry_id, temperature, timestamp) VALUES (?, ?, ?)",
                    (id, temperature, timestamp),
                )
            else:
                logging.error(f"Failed to get temperature for Raspberry Pi {id}")
        except Exception as e:
            logging.error(f"Failed to log temperature for Raspberry Pi {id}: {str(e)}")

    conn.commit()


# 一定間隔で温度を記録
def log_temperature_periodically(interval):
    """
    一定間隔で温度を記録
    """
    while True:  # ここで無限ループにする
        try:
            # データベース接続とカーソルの作成
            conn = create_connection()
            cursor = conn.cursor()

            log_temperature(conn, cursor)  # 温度を記録

            conn.close()  # データベース接続を閉じる
        except Exception as e:
            logging.error(f"Error logging temperature: {e}")
        time.sleep(interval)




# 温度記録を停止
def stop_logging():
    """
    温度記録を停止
    """
    stop_event.set()
