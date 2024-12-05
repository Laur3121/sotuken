// 温度データを取得してグラフに描画
fetch('/temperature')
    .then(response => response.json())
    .then(data => {
        const localTemp = data.local_temperature;
        const remoteTemp = data.remote_temperature;

        // グラフ用のデータ
        const chartData = {
            labels: ['Local', 'Remote'],
            datasets: [{
                label: 'Temperature',
                data: [localTemp, remoteTemp],
                borderColor: 'rgb(75, 192, 192)',
                fill: false
            }]
        };

        // Chart.jsでグラフを描画
        const ctx = document.getElementById('temperatureChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'bar', // 棒グラフ
            data: chartData,
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }  // この閉じカッコを追加
        });  // ここを修正

        // 定期的に温度データを更新
        setInterval(function() {
            fetch('/temperature')
                .then(response => response.json())
                .then(data => {
                    const localTemp = data.local_temperature;
                    const remoteTemp = data.remote_temperature;

                    chart.data.datasets[0].data = [localTemp, remoteTemp];
                    chart.update();  // グラフを更新
                })
                .catch(error => console.error('Error fetching temperature data:', error));
        }, 10000);  // 10秒ごとに更新
    })
    .catch(error => console.error('Error fetching temperature data:', error));
