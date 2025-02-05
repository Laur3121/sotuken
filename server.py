import logging
import time
import threading
from flask import Flask
from app.utils import log_periodically
from app.routes import main # log_cpu_usage_periodically をインポート
from app import create_app  # create_app をインポート

# paramiko のログレベルを抑制
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

# Flask アプリケーションを作成
app = create_app()  # create_app() 関数を使ってアプリケーションを作成

# 温度記録を停止するイベント
stop_event = threading.Event()

if __name__ == "__main__":
    # 温度記録を一定間隔で開始する
    logging.info("Starting temperature logging...")

    # 温度記録用のスレッドを開始
    temperature_thread = threading.Thread(target=log_periodically, args=(60,))
    temperature_thread.start()


    # Flask サーバーの起動
    app.run(debug=False, host='0.0.0.0', port=5000)