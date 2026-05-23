/**
 * CrowdPulse AI - Main Application Flow
 */

let isConnected = false;

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Map and Chart
    initStadiumMap();
    initChart();
    
    // 2. Connect WebSocket
    initWebSocket();
    
    // 3. Setup Fallback Polling
    setInterval(fetchStatus, 12000);
    fetchStatus();

    // 4. Time
    setInterval(updateClock, 1000);
    updateClock();

    // 5. Button Listeners
    document.getElementById('demo-scenario-btn').addEventListener('click', startDemoScenario);
    document.getElementById('execute-all-btn').addEventListener('click', () => {
        executeAction('execute_all');
        const btn = document.getElementById('execute-all-btn');
        btn.innerHTML = '<i class="fa-solid fa-check"></i> Executed';
        btn.style.background = 'var(--status-safe)';
        setTimeout(() => {
            btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Execute All Actions';
            btn.style.background = '';
        }, 3000);
    });

    const rtspModal = document.getElementById('rtsp-modal');
    document.getElementById('settings-btn').addEventListener('click', () => rtspModal.classList.remove('hidden'));
    document.getElementById('rtsp-close-btn').addEventListener('click', () => rtspModal.classList.add('hidden'));
    document.getElementById('rtsp-save-btn').addEventListener('click', async () => {
        const url = document.getElementById('rtsp-url-input').value;
        await fetch('/api/rtsp', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url})
        });
        rtspModal.classList.add('hidden');
        addTickerMessage(`Camera connected to ${url}`);
    });

    document.getElementById('get-analysis-btn')?.addEventListener('click', async () => {
        const btn = document.getElementById('get-analysis-btn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
        btn.disabled = true;
        
        try {
            const res = await fetch('/api/agents/analyze', { method: 'POST' });
            if (res.ok) {
                addTickerMessage('Agent Analysis Complete');
            } else {
                addTickerMessage('Error running analysis');
            }
        } catch (e) {
            addTickerMessage('Error connecting to backend');
        }
        
        btn.innerHTML = originalText;
        btn.disabled = false;
    });
});

function initWebSocket() {
    const socket = io({ path: '/ws/socket.io' });
    
    socket.on('connect', () => {
        document.querySelector('.status-dot').classList.add('green');
        document.querySelector('.status-dot').style.background = 'var(--status-safe)';
        addTickerMessage('Connected to Live Data Stream');
    });

    socket.on('disconnect', () => {
        document.querySelector('.status-dot').style.background = 'var(--status-danger)';
        addTickerMessage('Disconnected from Live Data Stream');
    });

    socket.on('state_update', (data) => {
        updateDashboard(data);
    });

    socket.on('agent_message', (data) => {
        addAgentMessage(data);
    });

    socket.on('alert', (data) => {
        addTickerMessage(`ALERT: ${data.title}`);
    });

    socket.on('gate_count_update', (data) => {
        const videoModal = document.getElementById('video-modal');
        if (videoModal && !videoModal.classList.contains('hidden')) {
            const titleText = document.getElementById('video-modal-title').innerText.toLowerCase();
            const formattedZoneId = data.zone_id.replace('_', ' ').toLowerCase();
            
            if (titleText.includes(formattedZoneId)) {
                const countEl = document.getElementById('video-total-count');
                if (countEl) countEl.innerText = data.count;
            }
        }
    });
}

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        if (res.ok) {
            const data = await res.json();
            updateDashboard(data);
        }
    } catch (e) {
        console.warn('Polling failed', e);
    }
}

function updateDashboard(state) {
    if (!state) return;
    
    // Map
    if (state.zones) updateZoneColors(state.zones);
    
    // Stats
    updateLiveStats(state);
    
    // Action Plan
    if (state.action_plan && state.action_plan.actions) {
        renderActionPlan(state.action_plan.actions, state.action_plan.overall_risk);
    }

    // Weather
    if (state.weather) {
        document.getElementById('weather-temp').textContent = state.weather.temperature + '°C';
        document.getElementById('weather-desc').textContent = state.weather.weather_description || 'Clear';
    }
}

// -- Action Panel Rendering --
function renderActionPlan(actions, riskLevel) {
    const container = document.getElementById('action-items-container');
    container.innerHTML = '';
    
    const badge = document.getElementById('risk-badge');
    badge.textContent = riskLevel.toUpperCase() + ' RISK';
    badge.className = `badge ${riskLevel.toLowerCase()}`;

    actions.forEach((action, i) => {
        const div = document.createElement('div');
        div.className = 'action-item';
        div.innerHTML = `
            <div class="action-desc">
                <span style="color: var(--text-secondary); margin-right: 8px;">${i+1}.</span>
                ${action.description}
            </div>
            <button class="action-btn" onclick="executeAction('${action.action_type}')">
                ${action.is_executed ? '<i class="fa-solid fa-check" style="color: var(--status-safe)"></i>' : 'Trigger'}
            </button>
        `;
        container.appendChild(div);
    });
}

async function executeAction(type) {
    await fetch(`/api/actions/${type}`, { method: 'POST' });
    addTickerMessage(`Action triggered: ${type.replace('_', ' ')}`);
}

// -- Agents Panel --
function addAgentMessage(msg) {
    const container = document.getElementById('agent-messages-container');
    
    let agentClass = 'agent-crowd';
    let icon = 'fa-robot';
    if (msg.agent_name.includes('Ticket')) { agentClass = 'agent-ticket'; icon = 'fa-qrcode'; }
    if (msg.agent_name.includes('Route')) { agentClass = 'agent-route'; icon = 'fa-route'; }
    if (msg.agent_name.includes('Weather')) { agentClass = 'agent-weather'; icon = 'fa-cloud-sun'; }
    if (msg.agent_name.includes('Emergency')) { agentClass = 'agent-emergency'; icon = 'fa-triangle-exclamation'; }

    const div = document.createElement('div');
    div.className = `agent-msg ${agentClass}`;
    div.innerHTML = `
        <div class="agent-msg-header">
            <span class="agent-name"><i class="fa-solid ${icon}"></i> ${msg.agent_name}</span>
            <span class="agent-time">${new Date(msg.timestamp).toLocaleTimeString()}</span>
        </div>
        <div class="agent-summary">${msg.summary}</div>
        <div class="agent-details">${msg.details}</div>
    `;
    
    div.addEventListener('click', () => div.classList.toggle('expanded'));
    container.prepend(div);

    if (container.children.length > 30) {
        container.lastChild.remove();
    }
}

// -- Utils --
async function startDemoScenario() {
    await fetch('/api/scenario/start', { method: 'POST' });
    addTickerMessage('Demo scenario initiated. Watch agents respond.');
}

function updateClock() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleTimeString('en-US', { hour12: false });
}

function addTickerMessage(text) {
    const container = document.getElementById('ticker-content');
    const span = document.createElement('span');
    span.textContent = `• ${new Date().toLocaleTimeString()} - ${text}`;
    container.appendChild(span);
}
