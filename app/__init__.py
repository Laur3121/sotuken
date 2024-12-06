from flask import Flask

def create_app():
    app = Flask(__name__)

    # routes.py で定義されたブループリントをインポートして登録
    from .routes import main
    app.register_blueprint(main)

    # 必要に応じて追加の初期化を行う
    return app