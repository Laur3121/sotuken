import time
import logging
import sqlite3
import paramiko

# ログ設定
logging.basicConfig(level=logging.INFO)

# 温度取得関数（リモートの Raspberry Pi の温度を取得）
def get_remote_temperature(host, username, password):
    try:
        # SSHクライアントの初期化
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # SSH接続
        client.connect(hostname=host, username=username, password=password)

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

# 温度をログとして記録し、データベースに保存する関数
def log_temperature():
    conn = sqlite3.connect("raspberries.db")
    cursor = conn.cursor()
    
    # Raspberry Pi の情報を取得
    cursor.execute("SELECT id, ip_address FROM raspberries")
    raspberries = cursor.fetchall()

    for raspberry in raspberries:
        id, ip_address = raspberry
        try:
            # SSH接続でリモートの温度を取得
            temperature = get_remote_temperature(ip_address, "ubuntu", "ubuntu")
            
            if temperature is not None:
                # 取得した温度をログ出力
                logging.info(f"Temperature for Raspberry Pi {id} (IP: {ip_address}): {temperature}°C")

                # データベースに保存
                cursor.execute(
                    "INSERT INTO temperature_logs (raspberry_id, temperature) VALUES (?, ?)",
                    (id, temperature),
                )
            else:
                logging.error(f"Failed to get temperature for Raspberry Pi {id}")
        except Exception as e:
            logging.error(f"Failed to log temperature for Raspberry Pi {id}: {str(e)}")

    conn.commit()
    conn.close()

# 一定時間ごとに温度を取得してログに記録するループ
def run_periodic_logging(interval):
    while True:
        log_temperature()
        logging.info(f"Waiting {interval} seconds before the next update...")
        time.sleep(interval)

# 10分（600秒）ごとに温度を取得して更新
run_periodic_logging(10)


# 実行部分
if __name__ == "__main__":
    get_remote_temperature_from_db()
