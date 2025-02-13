import sqlite3
import logging
import time
import paramiko
import threading
import datetime
import subprocess
from .migration_history import log_migration
# ログ設定
logging.basicConfig(level=logging.INFO)

# データベース接続を作成して返す
def create_connection():
    conn = sqlite3.connect("raspberries.db", timeout=10)  # タイムアウトを設定してロックを避ける
    conn.row_factory = sqlite3.Row  # 結果を辞書のように扱う
    return conn

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
        #logging.info(f"Connecting to {host}...")
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
                    "INSERT INTO cpu_temperature_logs (raspberry_id, cpu_temperature, timestamp) VALUES (?, ?, ?)",
                    (id, temperature, timestamp),
                )
            else:
                logging.error(f"Failed to get temperature for Raspberry Pi {id}")

            # 温度が70度を超えたらmigration_logic.pyを実行
            if temperature > 70:
                logging.info(f"Temperature is {temperature}°C, exceeding threshold. Triggering migration logic.")
                subprocess.run(["python3", "./app/migration_logic.py"])
                

                

            
        except Exception as e:
            logging.error(f"Failed to log temperature for Raspberry Pi {id}: {str(e)}")

    conn.commit()

def get_remote_cpu_usage(host, username, password, timeout=10):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        #logging.info(f"Connecting to {host}...")
        client.connect(hostname=host, username=username, password=password, timeout=timeout)

        # top コマンドの出力を取得
        stdin, stdout, stderr = client.exec_command("top -bn1 | grep 'Cpu(s)'")
        output = stdout.read().decode('utf-8').strip()

        client.close()

        # 出力をログに記録して、形式を確認
        #logging.info(f"Output from top command: {output}")

        if not output:  # 出力が空であった場合のエラーハンドリング
            logging.error(f"Empty output received from {host}")
            return None

        # 出力例: '%Cpu(s): 94.3 us,  5.7 sy,  0.0 ni,  0.0 id,  0.0 wa,  0.0 hi,  0.0 si,  0.0 st'
        cpu_info = output.split(",")

        #logging.info(f"CPU info split: {cpu_info}")  # 各項目がどう分割されているかログに出力

        cpu_usage = 0.0
        # 最初の項目の 'us' を取り出して処理
        first_item = cpu_info[0].split()
        if len(first_item) >= 3 and first_item[2] == 'us':
            usage = float(first_item[1].replace("%", ""))
            #logging.info(f"Adding {usage} for us")
            cpu_usage += usage
        
        # 残りの項目を処理
        for item in cpu_info[1:]:
            parts = item.split()
            #logging.info(f"Parsing item: {parts}")  

            try:
                # 'sy', 'ni', 'wa', 'hi', 'si' の部分を集計
                if len(parts) >= 2:
                    usage_type = parts[1]  # 例えば 'us', 'sy' など
                    if usage_type in ['sy', 'ni', 'wa', 'hi', 'si']:
                        usage = float(parts[0].replace("%", ""))
                        #ogging.info(f"Adding {usage} for {usage_type}")
                        cpu_usage += usage
            except Exception as e:
                logging.error(f"Error parsing item '{item}' from CPU info: {e}")
        
        return cpu_usage

    except Exception as e:
        logging.error(f"Failed to get CPU usage from {host}: {str(e)}")
        return None







def log_cpu_usage(conn, cursor):
    """
    データベース内の Raspberry Pi 情報に基づいて CPU 使用率を取得し、記録する。
    """
    # Raspberry Pi の情報を取得
    cursor.execute("SELECT id, ip_address FROM raspberries")
    
    raspberries = cursor.fetchall()

    for raspberry in raspberries:
        id, ip_address = raspberry
        try:
            # リモートの CPU 使用率を取得
            cpu_usage = get_remote_cpu_usage(ip_address, "ubuntu", "ubuntu")

            if cpu_usage is not None:
                # 取得した CPU 使用率と現在時刻をデータベースに保存
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO cpu_usage_logs (raspberry_id, cpu_usage, timestamp) VALUES (?, ?, ?)",
                    (id, cpu_usage, timestamp),
                )
            else:
                logging.error(f"Failed to get CPU usage for Raspberry Pi {id}")

        except Exception as e:
            logging.error(f"Failed to log CPU usage for Raspberry Pi {id}: {str(e)}")

    conn.commit()


# 温度と CPU 使用率を一定間隔で記録
def log_periodically(interval):
    """
    一定間隔で温度と CPU 使用率を記録
    """
    while True:  # 無限ループ
        try:
            # データベース接続とカーソルの作成
            conn = create_connection()
            conn.execute('PRAGMA busy_timeout = 10000')
            cursor = conn.cursor()
            

            log_temperature(conn, cursor)  # 温度を記録
            log_cpu_usage(conn, cursor)  # CPU 使用率を記録

            conn.commit()

            conn.close()  # データベース接続を閉じる
        except Exception as e:
            logging.error(f"Error logging temperature or CPU usage: {e}")
        time.sleep(interval)

# 定期的に温度とCPU使用率を記録
#logging_thread = threading.Thread(target=log_periodically, args=(60,))
#logging_thread.start()

