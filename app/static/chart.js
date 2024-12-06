// 初期化用データ（後で更新されます）
let labels = []; // 時間ラベル
let localData = []; // ローカル温度データ
let remoteData = []; // リモート温度データ

// グラフの初期設定
const ctx = document.getElementById('temperatureChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line', // 折れ線グラフ
    data: {
        labels: labels,
        datasets: [
            {
                label: 'Local Temperature',
                data: localData,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            },
            {
                label: 'Remote Temperature',
                data: remoteData,
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Time'
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Temperature (°C)'
                }
            }
        }
    }
});

// 温度データを取得して更新
function fetchTemperatureData() {
    fetch('/temperature')
        .then(response => response.json())
        .then(data => {
            const now = new Date().toLocaleTimeString(); // 現在時刻を取得
            labels.push(now);
            localData.push(data.local_temperature);
            remoteData.push(data.remote_temperature);

            // データが多すぎたら古いものを削除
            if (labels.length > 10) { // 10点を保持
                labels.shift();
                localData.shift();
                remoteData.shift();
            }

            chart.update(); // グラフを更新
        })
        .catch(error => console.error('Error fetching temperature data:', error));
}

// 10秒ごとにデータを取得
setInterval(fetchTemperatureData, 10000);
fetchTemperatureData(); // 初回呼び出