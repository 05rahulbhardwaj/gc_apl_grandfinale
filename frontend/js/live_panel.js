/**
 * CrowdPulse AI - Live Stats & Chart.js Integration
 */

let crowdChartInstance = null;

function updateLiveStats(state) {
    if (!state) return;

    // 1. Update text stats
    document.getElementById('stat-total-inside').textContent = state.total_crowd_inside.toLocaleString();
    document.getElementById('stat-outside').textContent = state.total_crowd_outside.toLocaleString();
    document.getElementById('stat-scans').textContent = state.ticket_scans_per_min.toFixed(0);
    
    // Average wait time (calc from gates)
    if (state.gates && state.gates.length > 0) {
        let maxWait = Math.max(...state.gates.map(g => g.avg_wait_time));
        document.getElementById('stat-wait').textContent = maxWait.toFixed(1) + ' m';
    }

    document.getElementById('stat-security').textContent = state.security_personnel;
    document.getElementById('stat-volunteers').textContent = state.volunteers_deployed;

    // 2. Update Safety Gauge
    updateSafetyGauge(state.action_plan?.safety_score || 0);

    // 3. Update Chart.js (simulate historical data if not provided)
    updateCrowdChart(state.total_crowd_inside);
}

function updateSafetyGauge(score) {
    const valueEl = document.getElementById('safety-score-value');
    const labelEl = document.getElementById('safety-score-label');
    const fillPath = document.getElementById('gauge-fill');
    
    valueEl.textContent = score;

    // Colors & Labels
    let color = 'var(--status-safe)';
    let text = 'EXCELLENT';
    
    if (score < 40) {
        color = 'var(--status-danger)'; text = 'CRITICAL';
    } else if (score < 70) {
        color = 'var(--status-warning)'; text = 'FAIR';
    } else if (score < 85) {
        color = '#4ade80'; text = 'GOOD';
    }

    labelEl.textContent = text;
    fillPath.style.stroke = color;

    // Circumference is ~188.5 for r=40
    const offset = 188.5 - (188.5 * (score / 100));
    fillPath.style.strokeDashoffset = offset;
}

// historical data array
const crowdHistory = [];
const timeLabels = [];

function initChart() {
    const ctx = document.getElementById('crowd-trend-chart').getContext('2d');
    
    // Gradient
    let gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(0, 212, 255, 0.4)');
    gradient.addColorStop(1, 'rgba(0, 212, 255, 0.0)');

    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";

    crowdChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: 'Total Crowd Inside',
                data: crowdHistory,
                borderColor: '#00d4ff',
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0,
                pointHitRadius: 10,
                fill: true,
                tension: 0.4 // Smooth bezier curves
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#00d4ff',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false
                }
            },
            scales: {
                x: { 
                    grid: { display: false, drawBorder: false },
                    ticks: { maxTicksLimit: 6 }
                },
                y: { 
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    beginAtZero: true
                }
            }
        }
    });
}

function updateCrowdChart(currentValue) {
    if (!crowdChartInstance) {
        initChart();
        // Seed initial mock data
        let v = Math.max(0, currentValue - 5000);
        for(let i=60; i>0; i--) {
            timeLabels.push(`-${i}m`);
            crowdHistory.push(v);
            v += Math.floor(Math.random() * 200) + 50;
        }
    }

    const now = new Date();
    const timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

    timeLabels.push(timeStr);
    crowdHistory.push(currentValue);

    if (timeLabels.length > 60) {
        timeLabels.shift();
        crowdHistory.shift();
    }

    crowdChartInstance.update('none'); // Update without animation to prevent flashing
}

window.updateLiveStats = updateLiveStats;
