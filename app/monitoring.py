import sqlite3
import matplotlib.pyplot as plt
import pandas as pd

def get_temperature_and_cpu_usage():
    conn = sqlite3.connect('raspberries.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 温度データを取得
    cursor.execute('''
    SELECT r.id, r.name, r.ip_address,
           (SELECT cpu_temperature FROM cpu_temperature_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_temp,
           (SELECT timestamp FROM cpu_temperature_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_temp
    FROM raspberries r
    ''')
    temperature_data = cursor.fetchall()

    # CPU 使用率データを取得
    cursor.execute('''
    SELECT r.id, r.name, r.ip_address,
           (SELECT cpu_usage FROM cpu_usage_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_cpu_usage,
           (SELECT timestamp FROM cpu_usage_logs WHERE raspberry_id = r.id ORDER BY timestamp DESC LIMIT 1) AS latest_cpu_usage
    FROM raspberries r
    ''')
    cpu_usage_data = cursor.fetchall()

    conn.close()

    # データをDataFrameに変換
    temperature_df = pd.DataFrame(temperature_data, columns=["raspberry", "temperature", "ip_address", "latest_temp", "timestamp_temp"])
    cpu_usage_df = pd.DataFrame(cpu_usage_data, columns=["raspberry", "cpu_usage", "ip_address", "latest_cpu_usage", "timestamp_cpu"])

    return temperature_df, cpu_usage_df

# グラフの表示
def plot_graphs():
    # データを取得
    temperature_df, cpu_usage_df = get_temperature_and_cpu_usage()
    print("Temperature Data:\n", temperature_df)
    print("CPU Usage Data:\n", cpu_usage_df)

    # 温度グラフの作成
    plt.figure(figsize=(10, 5))
    plt.bar(temperature_df['raspberry'], temperature_df['temperature'], color='blue')
    plt.xlabel('Raspberry Pi')
    plt.ylabel('Temperature (°C)')
    plt.title('Raspberry Pi Temperature')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # CPU使用率グラフの作成
    plt.figure(figsize=(10, 5))
    plt.bar(cpu_usage_df['raspberry'], cpu_usage_df['cpu_usage'], color='green')
    plt.xlabel('Raspberry Pi')
    plt.ylabel('CPU Usage (%)')
    plt.title('Raspberry Pi CPU Usage')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_graphs()


