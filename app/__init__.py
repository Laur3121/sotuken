from flask import Flask
from flask_socketio import SocketIO
from .routes import main  # ここでmainをインポート
socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    # 必要に応じて設定を追加
    app.config["SECRET_KEY"] = "your-secret-key"

    # Blueprint（ルーティング）を登録
    app.register_blueprint(main)  # mainを登録

    # SocketIOをFlaskアプリケーションに統合
    socketio.init_app(app)

    return app

