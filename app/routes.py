from flask import Flask, jsonify, request, render_template, redirect, url_for
import sqlite3
from flask import Blueprint
import logging
import os
import paramiko
import time
import datetime
import threading
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go






# ログの基本設定
logging.basicConfig(level=logging.DEBUG)

# Blueprintの作成
main = Blueprint("main", __name__)

# Flaskアプリの初期化
app = Flask(__name__)

# データベースから最新の温度情報を取得する関数
def get_latest_temperatures():
    conn = sqlite3.connect("raspberries.db")
    cursor = conn.cursor()

    conn.execute("PRAGMA journal_mode=WAL;")


    # 最新の温度データを取得
    cursor.execute("""
        SELECT r.ip_address, t.temperature, t.timestamp
        FROM temperature_logs t
        JOIN raspberries r ON t.raspberry_id = r.id
        ORDER BY t.timestamp DESC
        LIMIT 5
    """)
    temperatures = cursor.fetchall()
    conn.commit()
    conn.close()

    return temperatures

import subprocess

import pexpect

import pexpect

# CPU 使用率を取得する関数
def get_cpu_usage(raspi_id):
    conn = create_connection()
    cursor = conn.cursor()

    conn.execute("PRAGMA journal_mode=WAL;")


    # 最新の CPU 使用率を取得
    cursor.execute("""
        SELECT cpu_temperature, timestamp FROM cpu_temperature_logs
        WHERE raspberry_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (raspi_id,))
    cpu_data = cursor.fetchone()
    conn.commit()
    conn.close()

    if cpu_data:
        # 例えば、CPU 使用率の最後の値を取り出して返す
        return cpu_data[0]  # cpu_temperature を使用している場合
    return None




def get_docker_containers(ip_address, username, password):
    command = "docker ps --format '{{.Names}}'"
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip_address, username=username, password=password)
    
    stdin, stdout, stderr = ssh.exec_command(command)
    containers = stdout.read().decode().strip().split('\n')
    ssh.close()
    return ", ".join(containers)


# データベースの初期化
def init_db():
    conn = sqlite3.connect("raspberries.db")
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS raspberries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT "Inactive",
        current_temperature REAL DEFAULT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS temperature_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raspberry_id INTEGER NOT NULL,
        temperature REAL NOT NULL,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(raspberry_id) REFERENCES raspberries(id)
    )
    ''')
    conn.commit()
    conn.close()

@main.route('/reset_database', methods=['POST'])
def reset_database():
    db_path = 'raspberries.db'
    
    # 既存のデータベースがあれば削除
    if os.path.exists(db_path):
        os.remove(db_path)

    # 新しいデータベースを作成
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")


    # テーブルの作成
    cursor.execute('''
    CREATE TABLE raspberries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ip_address TEXT NOT NULL,
        status TEXT NOT NULL,
        location INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    cursor.execute('''
    CREATE TABLE temperature_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raspberry_id INTEGER,
        temperature REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (raspberry_id) REFERENCES raspberries (id)
    );
    ''')

    conn.commit()
    conn.close()

    return redirect(url_for('main.dashboard'))


@main.route("/")
def dashboard():
    # ソートパラメータを取得（デフォルトはID順）
    sort_order = request.args.get('sort', 'id')

    # ソート条件に応じてORDER BYを設定
    order_by = "r.id"  # デフォルト
    if sort_order == 'ip':
        order_by = "r.ip_address"
    elif sort_order == 'name':
        order_by = "r.name"
    elif sort_order == 'status':
        order_by = "r.status"

    # データベース接続
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")


    # クエリにORDER BYを追加
    query = f'''
    SELECT r.id, r.name, r.ip_address, r.status, r.location,
           (SELECT cpu_temperature FROM cpu_temperature_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_temp
    FROM raspberries r
    ORDER BY {order_by}
    '''
    cursor.execute(query)
    raspberries = cursor.fetchall()
    conn.commit()
    conn.close()

    # ダッシュボードに温度情報を含めて返す
    return render_template("dashboard.html", raspberries=raspberries)



@main.route("/add_raspi", methods=["GET", "POST"])
def add_raspi():
    if request.method == "POST":
        name = request.form.get("name")
        ip_address = request.form.get("ip_address")
        location = request.form.get("location")  # 位置情報を取得

        if not name or not ip_address:
            return "Name and IP address are required!", 400

        conn = sqlite3.connect('raspberries.db')
        conn.execute('PRAGMA busy_timeout = 20000')
        cursor = conn.cursor()
        

        cursor.execute(
            "INSERT INTO raspberries (name, ip_address, status, location) VALUES (?, ?, ?, ?)", 
            (name, ip_address, "Active", location)  # location を追加
        )
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_edit.html", raspi=None)


# Raspberry Pi の編集（データ更新）
@main.route('/edit_raspi/<int:id>', methods=["GET", "POST"])
def edit_raspi(id):
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")


    if request.method == "POST":
        # フォームから送信されたデータを取得
        name = request.form["name"]
        ip_address = request.form["ip_address"]
        location = request.form["location"]  # 位置情報があれば取得

        # データベースを更新
        cursor.execute("UPDATE raspberries SET name=?, ip_address=?, location=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (name, ip_address, location, id))
        conn.commit()
        conn.close()
        
        # 更新後はダッシュボードにリダイレクト
        return redirect(url_for('main.dashboard'))  # ダッシュボードページにリダイレクト

    # GETリクエスト時：編集対象のデータを表示
    cursor.execute("SELECT * FROM raspberries WHERE id=?", (id,))
    raspi = cursor.fetchone()
    conn.commit()
    conn.close()

    return render_template('edit_raspi.html', raspi=raspi)  # 編集フォームにデータを渡して表示

# Raspberry Pi の削除
@main.route("/delete/<int:id>", methods=["GET", "POST"])
def delete_raspi(id):
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")

    cursor.execute("DELETE FROM raspberries WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/init_db")
def initialize_database():
    try:
        init_db()
        return "Database initialized successfully!"
    except Exception as e:
        return f"Error initializing database: {e}", 500


# API: Raspberry Pi 一覧を取得
@app.route("/api/raspberries", methods=["GET"])
def get_raspberries():
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")

    cursor.execute("SELECT * FROM raspberries")
    raspberries = cursor.fetchall()
    conn.commit()
    conn.close()
    return jsonify([{"id": row[0], "name": row[1], "ip_address": row[2], "status": row[3]} for row in raspberries])

# API: Raspberry Pi を追加
@app.route("/api/raspberries", methods=["POST"])
def add_raspberry_api():
    data = request.json
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")

    cursor.execute("INSERT INTO raspberries (name, ip_address, status) VALUES (?, ?, ?)", (data["name"], data["ip_address"], "Active"))
    conn.commit()
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": new_id, **data, "status": "Active"})

# API: Raspberry Pi を編集または削除
@app.route("/api/raspberries/<int:id>", methods=["PUT", "DELETE"])
def modify_raspberry_api(id):
    if request.method == "PUT":
        data = request.json
        conn = sqlite3.connect('raspberries.db')
        cursor = conn.cursor()
        conn.execute("PRAGMA journal_mode=WAL;")

        cursor.execute("UPDATE raspberries SET name=?, ip_address=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", 
                       (data["name"], data["ip_address"], data["status"], id))
        conn.commit()
        conn.close()
        return jsonify(data)
    elif request.method == "DELETE":
        conn = sqlite3.connect('raspberries.db')
        cursor = conn.cursor()
        conn.execute("PRAGMA journal_mode=WAL;")

        cursor.execute("DELETE FROM raspberries WHERE id=?", (id,))
        conn.commit()
        conn.close()
        return '', 204

@app.route("/api/raspberries/<int:id>/temperature", methods=["POST"])
def update_temperature(id):
    data = request.json
    temperature = data["temperature"]
    
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")

    
    # 現在の温度を更新
    cursor.execute("UPDATE raspberries SET current_temperature=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (temperature, id))
    
    # 温度履歴を記録
    cursor.execute("INSERT INTO temperature_logs (raspberry_id, temperature) VALUES (?, ?)", (id, temperature))
    
    conn.commit()
    conn.close()
    return jsonify({"id": id, "temperature": temperature})

@main.route("/details/<int:id>")
def details(id):
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")

    cursor.execute('''
    SELECT logged_at, temperature
    FROM temperature_logs
    WHERE raspberry_id = ?
    ORDER BY logged_at DESC
    ''', (id,))
    temperature_logs = cursor.fetchall()
    conn.commit()
    conn.close()
    return render_template("details.html", logs=temperature_logs)

import re

import psutil

@main.route('/grid_dashboard')
def grid_dashboard():
    conn = sqlite3.connect('raspberries.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL;")


    cursor.execute('''
    SELECT r.id, r.name, r.ip_address,
           (SELECT cpu_temperature FROM cpu_temperature_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_temp,
           (SELECT cpu_usage FROM cpu_usage_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_cpu_usage,
           r.status, r.location
    FROM raspberries r
    ''')
    raspberries = cursor.fetchall()

    grid_data = []

    for raspi in raspberries:
        location = raspi['location']
        if location:
            match = re.search(r'x(\d+)y(\d+)', location)
            if match:
                location_x = int(match.group(1))
                location_y = int(match.group(2))
            else:
                location_x = 1
                location_y = 1
        else:
            location_x = 1
            location_y = 1

        # CPU使用率とDockerコンテナ情報をデータベースから取得
        cpu_usage = raspi['latest_cpu_usage'] if raspi['latest_cpu_usage'] is not None else "N/A"
        docker_containers = get_docker_containers(raspi['ip_address'], 'ubuntu', 'ubuntu')
        if not docker_containers:
            docker_containers = "No containers running"

        grid_data.append({
            "id": raspi['id'],
            "name": raspi['name'],
            "ip_address": raspi['ip_address'],
            "temperature": raspi['latest_temp'],
            "cpu_usage": cpu_usage,
            "docker_containers": docker_containers,
            "location_x": location_x,
            "location_y": location_y
        })

    conn.commit()
    conn.close()
    return render_template('grid_dashboard.html', grid_data=grid_data)


def get_temperature_and_cpu_usage():
    conn = sqlite3.connect('raspberries.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 温度データを取得
    cursor.execute('''
    SELECT r.id, r.name, r.ip_address,
           (SELECT cpu_temperature FROM cpu_temperature_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_temp,
           (SELECT timestamp FROM cpu_temperature_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS timestamp_temp
    FROM raspberries r
    ''')
    temperature_data = [dict(row) for row in cursor.fetchall()]

    # CPU 使用率データを取得
    cursor.execute('''
    SELECT r.id, r.name, r.ip_address,
           (SELECT cpu_usage FROM cpu_usage_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_cpu_usage,
           (SELECT timestamp FROM cpu_usage_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS timestamp_cpu
    FROM raspberries r
    ''')
    cpu_usage_data = [dict(row) for row in cursor.fetchall()]

    conn.close()

    # データをDataFrameに変換
    temperature_df = pd.DataFrame(temperature_data)
    cpu_usage_df = pd.DataFrame(cpu_usage_data)

    return temperature_df, cpu_usage_df

@main.route('/monitoring')
def index():
    temperature_df, _ = get_temperature_and_cpu_usage()

    # Plotlyでグラフを作成
    fig = px.bar(temperature_df, x="name", y="latest_temp", title="Raspberry Pi Temperature", labels={"name": "Raspberry Pi", "latest_temp": "Temperature (°C)"})
    graph_html = fig.to_html(full_html=False)  # グラフをHTML形式に変換

    return render_template('monitoring.html', graph_html=graph_html)



def get_temperature_logs():
    conn = sqlite3.connect('raspberries.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 温度ログを全て取得するSQLクエリ
    cursor.execute('''
    SELECT r.id AS raspberry, r.name, r.ip_address, t.cpu_temperature, t.timestamp 
    FROM raspberries r
    JOIN cpu_temperature_logs t ON r.id = t.raspberry_id
    ORDER BY t.timestamp
    ''')
    rows = cursor.fetchall()
    conn.close()

    # DataFrameに変換
    df = pd.DataFrame(rows, columns=["raspberry", "name", "ip_address", "cpu_temperature", "timestamp"])
    return df

@main.route('/monitoring_individual')
def monitoring_individual():
    df = get_temperature_logs()

    # timestamp を datetime 型に変換（念のため）
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    graphs = []  
    now = datetime.datetime.now()
    start_time = now - datetime.timedelta(minutes=15)  

    for raspberry_id in df["raspberry"].unique():
        raspberry_data = df[df["raspberry"] == raspberry_id]

        # 最新15分間のデータのみ取得
        raspberry_data = raspberry_data[raspberry_data["timestamp"] >= start_time]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=raspberry_data["timestamp"],
            y=raspberry_data["cpu_temperature"],
            mode='lines',
            name=f"Raspberry {raspberry_id}"
        ))
        fig.update_layout(
            title=f"Raspberry {raspberry_id} Temperature",
            xaxis_title="Timestamp",
            yaxis_title="Temperature (°C)",
            xaxis=dict(range=[start_time, now]),  
            height=600,
            width=900
        )

        graph_html = fig.to_html(full_html=False)
        graphs.append(graph_html)

    return render_template('monitoring_individual.html', graphs=graphs)


def get_latest_migration_history():
    conn = sqlite3.connect("migration_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM migration_history ORDER BY migration_time DESC LIMIT 20")
    data = cursor.fetchall()
    conn.close()
    return data

@main.route("/migration_history")
def migration_history():
    history = get_latest_migration_history()
    return render_template("migration_history.html", history=history)


if __name__ == "__main__":
    init_db()  # サーバー起動時にデータベースを初期化
    app.run(host="0.0.0.0", port=5000)
