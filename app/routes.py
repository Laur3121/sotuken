from flask import Blueprint, jsonify
from .utils import get_local_temperature, get_remote_temperature
from flask import Blueprint, jsonify, render_template

main = Blueprint("main", __name__)

# ホームページ
@main.route("/")
def home():
    return render_template("index.html")

# 温度データを返す
@main.route("/temperature")
def temperature():
    local_temp = get_local_temperature()
    if isinstance(local_temp, str):
        return jsonify({"error": local_temp}), 500
    
    # リモートRaspberry Piの温度を取得（ここでは仮のIPアドレスとユーザー名を使用）
    remote_host = "192.168.0.17"  # ここにリモートRaspberry PiのIPアドレスを設定
    remote_username = "ubuntu"  # リモートのユーザー名
    remote_password = "ubuntu"  # リモートのパスワード

    remote_temp = get_remote_temperature(remote_host, remote_username, remote_password)
    if isinstance(remote_temp, str):
        return jsonify({"error": remote_temp}), 500

    return jsonify({
        "local_temperature": local_temp,
        "remote_temperature": remote_temp
    })
