from flask import Flask, jsonify, request, render_template, redirect
import sqlite3
from flask import Blueprint
from flask import render_template, request, redirect, url_for

main = Blueprint("main", __name__)

app = Flask(__name__)

# データベースの初期化
def init_db():
    conn = sqlite3.connect("raspberries.db")
    cursor = conn.cursor()
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

# app/routes.py
# ルートの設定
@main.route("/")
def dashboard():
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT r.id, r.name, r.ip_address, r.status,
           (SELECT temperature FROM temperature_logs WHERE raspberry_id = r.id ORDER BY logged_at DESC LIMIT 1) AS latest_temp
    FROM raspberries r
    ''')
    raspberries = cursor.fetchall()
    conn.close()
    return render_template("dashboard.html", raspberries=raspberries)



@main.route("/add_raspi", methods=["GET", "POST"])
def add_raspi():
    if request.method == "POST":
        name = request.form.get("name")
        ip_address = request.form.get("ip_address")

        # ip_addressがNoneでないことを確認
        if not name or not ip_address:
            return "Name and IP address are required!", 400

        conn = sqlite3.connect('raspberries.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO raspberries (name, ip_address, status) VALUES (?, ?, ?)", (name, ip_address, "Active"))
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_edit.html", raspi=None)

# edit_raspi ルートの定義
@main.route("/edit_raspi/<int:id>", methods=["GET", "POST"])
def edit_raspi(id):
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()

    if request.method == "POST":
        # POSTリクエストで編集した内容を保存
        name = request.form["name"]
        ip_address = request.form["ip_address"]
        cursor.execute("UPDATE raspberries SET name = ?, ip_address = ? WHERE id = ?", (name, ip_address, id))
        conn.commit()
        conn.close()
        return redirect("/")

    # GETリクエストでデータを表示
    cursor.execute("SELECT * FROM raspberries WHERE id = ?", (id,))
    raspi = cursor.fetchone()
    conn.close()

    # 編集フォームに表示するデータを渡す
    if raspi:
        return render_template("add_edit.html", raspi=raspi)
    else:
        # データが見つからなかった場合の処理
        return "Raspberry Pi not found", 404

# Raspberry Pi の編集（データ更新）
@app.route('/update_raspi/<int:raspi_id>', methods=["POST"])
def update_raspi(raspi_id):
    name = request.form["name"]
    ip_address = request.form["ip_address"]
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE raspberries SET name=?, ip_address=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (name, ip_address, raspi_id))
    conn.commit()
    conn.close()
    return redirect("/")

# Raspberry Pi の削除
@main.route("/delete/<int:raspi_id>", methods=["GET", "POST"])
def delete_raspi(raspi_id):
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM raspberries WHERE id = ?", (raspi_id,))
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
    cursor.execute("SELECT * FROM raspberries")
    raspberries = cursor.fetchall()
    conn.close()
    return jsonify([{"id": row[0], "name": row[1], "ip_address": row[2], "status": row[3]} for row in raspberries])

# API: Raspberry Pi を追加
@app.route("/api/raspberries", methods=["POST"])
def add_raspberry_api():
    data = request.json
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO raspberries (name, ip_address, status) VALUES (?, ?, ?)", (data["name"], data["ip_address"], "Active"))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return jsonify({"id": new_id, **data, "status": "Active"})

# API: Raspberry Pi を編集または削除
@app.route("/api/raspberries/<int:raspi_id>", methods=["PUT", "DELETE"])
def modify_raspberry_api(raspi_id):
    if request.method == "PUT":
        data = request.json
        conn = sqlite3.connect('raspberries.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE raspberries SET name=?, ip_address=?, status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", 
                       (data["name"], data["ip_address"], data["status"], raspi_id))
        conn.commit()
        conn.close()
        return jsonify(data)
    elif request.method == "DELETE":
        conn = sqlite3.connect('raspberries.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM raspberries WHERE id=?", (raspi_id,))
        conn.commit()
        conn.close()
        return '', 204

@app.route("/api/raspberries/<int:raspi_id>/temperature", methods=["POST"])
def update_temperature(raspi_id):
    data = request.json
    temperature = data["temperature"]
    
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    
    # 現在の温度を更新
    cursor.execute("UPDATE raspberries SET current_temperature=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (temperature, raspi_id))
    
    # 温度履歴を記録
    cursor.execute("INSERT INTO temperature_logs (raspberry_id, temperature) VALUES (?, ?)", (raspi_id, temperature))
    
    conn.commit()
    conn.close()
    return jsonify({"raspi_id": raspi_id, "temperature": temperature})

@main.route("/details/<int:id>")
def details(id):
    conn = sqlite3.connect('raspberries.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT logged_at, temperature
    FROM temperature_logs
    WHERE raspberry_id = ?
    ORDER BY logged_at DESC
    ''', (id,))
    temperature_logs = cursor.fetchall()
    conn.close()
    return render_template("details.html", logs=temperature_logs)






if __name__ == "__main__":
    init_db()  # サーバー起動時にデータベースを初期化
    app.run(host="0.0.0.0", port=5000)
