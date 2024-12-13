import subprocess
import paramiko

# ローカルのRaspberry Piの温度を取得
def get_local_temperature():
    try:
        result = subprocess.run(
            ["vcgencmd", "measure_temp"], capture_output=True, text=True, check=True
        )
        temp_str = result.stdout.strip().replace("temp=", "").replace("'C", "")
        return float(temp_str)
    except subprocess.CalledProcessError:
        return "Error: Unable to get temperature from the system"
    except Exception as e:
        return f"Error: {str(e)}"

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
        print(f"Failed to get temperature from {host}: {str(e)}")  # 詳細なエラーメッセージを表示
        return f"Error: Unable to get temperature from {host}, {str(e)}"

