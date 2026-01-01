document.addEventListener('DOMContentLoaded', function() {
    const chartCanvas = document.getElementById('clicksChart');
    if (!chartCanvas) return;
    
    // Get data from data attribute
    const chartDataElement = document.getElementById('chartData');
    if (!chartDataElement) return;
    
    let clicksData;
    try {
        clicksData = JSON.parse(chartDataElement.dataset.clicks);
    } catch (e) {
        console.error('Failed to parse chart data:', e);
        return;
    }
    
    const ctx = chartCanvas.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: clicksData.map(d => d.date),
            datasets: [{
                label: 'Clicks',
                data: clicksData.map(d => d.count),
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#6366f1',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#334155' },
                    ticks: { 
                        color: '#94a3b8',
                        maxTicksLimit: 7,
                        callback: function(value, index) {
                            const date = new Date(this.getLabelForValue(value));
                            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                        }
                    }
                },
                y: {
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' },
                    beginAtZero: true
                }
            }
        }
    });
});