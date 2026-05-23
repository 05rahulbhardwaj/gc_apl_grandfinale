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
    // document.getElementById('demo-scenario-btn').addEventListener('click', startDemoScenario);

    const rtspModal = document.getElementById('rtsp-modal');
    const settingsModal = document.getElementById('settings-modal');

    // Settings Modal (Dynamic Contacts)
    const contactsContainer = document.getElementById('contacts-container');
    
    function createContactRow(name = '', mobile = '', seat = '') {
        const row = document.createElement('div');
        row.className = 'contact-row';
        row.style.display = 'flex';
        row.style.gap = '10px';
        row.style.alignItems = 'center';
        
        row.innerHTML = `
            <input type="text" class="glass-input contact-name" placeholder="Name" value="${name}" style="flex: 1;">
            <input type="text" class="glass-input contact-mobile" placeholder="Mobile" value="${mobile}" style="flex: 1;">
            <input type="text" class="glass-input contact-seat" placeholder="Seat No." value="${seat}" style="flex: 1; max-width: 100px;">
            <button class="icon-btn remove-contact-btn" style="color: #ef4444;" title="Remove"><i class="fa-solid fa-trash"></i></button>
        `;
        
        row.querySelector('.remove-contact-btn').addEventListener('click', () => {
            row.remove();
        });
        
        contactsContainer.appendChild(row);
    }

    document.getElementById('add-contact-btn').addEventListener('click', () => createContactRow());

    document.getElementById('settings-btn').addEventListener('click', () => {
        contactsContainer.innerHTML = '';
        const savedContacts = JSON.parse(localStorage.getItem('broadcastContacts') || '[]');
        if (savedContacts.length === 0) {
            createContactRow(); // Show at least one empty row
        } else {
            savedContacts.forEach(c => createContactRow(c.name, c.mobile, c.seat));
        }
        settingsModal.classList.remove('hidden');
    });

    document.getElementById('settings-close-btn').addEventListener('click', () => settingsModal.classList.add('hidden'));
    
    document.getElementById('settings-save-btn').addEventListener('click', () => {
        const rows = contactsContainer.querySelectorAll('.contact-row');
        const contacts = [];
        rows.forEach(row => {
            const name = row.querySelector('.contact-name').value.trim();
            const mobile = row.querySelector('.contact-mobile').value.trim();
            const seat = row.querySelector('.contact-seat').value.trim();
            if (name || mobile) { // Only save if at least name or mobile is provided
                contacts.push({ name, mobile, seat });
            }
        });
        localStorage.setItem('broadcastContacts', JSON.stringify(contacts));
        settingsModal.classList.add('hidden');
        addTickerMessage(`Saved ${contacts.length} contacts locally.`);
    });

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

    // ── Easter Egg: Face Match ──────────────────────────────
    const fmModal = document.getElementById('face-match-modal');
    const fmVideo = document.getElementById('fm-video');
    const fmCanvas = document.getElementById('fm-canvas');
    const fmWebcam = document.getElementById('fm-webcam-area');
    const fmLoading = document.getElementById('fm-loading');
    const fmResults = document.getElementById('fm-results');
    let fmStream = null;

    function fmShow(el) { el.style.display = 'flex'; }
    function fmHide(el) { el.style.display = 'none'; }

    document.getElementById('easter-egg-btn').addEventListener('click', async () => {
        fmModal.classList.remove('hidden');
        fmShow(fmWebcam);
        fmHide(fmLoading);
        fmHide(fmResults);
        
        try {
            fmStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
            fmVideo.srcObject = fmStream;
        } catch (e) {
            alert('Camera access denied. Please allow camera access.');
        }
    });

    function stopFmCamera() {
        if (fmStream) {
            fmStream.getTracks().forEach(t => t.stop());
            fmStream = null;
        }
    }

    document.getElementById('close-face-match-btn').addEventListener('click', () => {
        stopFmCamera();
        fmModal.classList.add('hidden');
    });

    document.getElementById('fm-capture-btn').addEventListener('click', async () => {
        // Capture frame from video
        fmCanvas.width = fmVideo.videoWidth;
        fmCanvas.height = fmVideo.videoHeight;
        const ctx = fmCanvas.getContext('2d');
        ctx.drawImage(fmVideo, 0, 0);
        
        // Show loading
        fmHide(fmWebcam);
        fmShow(fmLoading);
        stopFmCamera();

        // Convert to blob and send
        fmCanvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('file', blob, 'selfie.jpg');
            
            try {
                const res = await fetch('/api/face-match', { method: 'POST', body: formData });
                if (!res.ok) throw new Error('Face match failed');
                
                const data = await res.json();
                
                // Hide loading, show results
                fmHide(fmLoading);
                fmShow(fmResults);
                
                // Best match
                if (data.best_match) {
                    document.getElementById('fm-best-name').textContent = `You look like ${data.best_match.name}!`;
                    document.getElementById('fm-best-score').textContent = `${data.best_match.similarity}% Match`;
                    document.getElementById('fm-celeb-img').src = data.best_match.thumbnail;
                    document.getElementById('fm-celeb-label').textContent = data.best_match.name;
                }
                document.getElementById('fm-user-img').src = data.user_image;
                
                // All matches
                const allContainer = document.getElementById('fm-all-matches');
                allContainer.innerHTML = '';
                data.matches.forEach(m => {
                    const bar = document.createElement('div');
                    bar.style.cssText = 'display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 8px; background: rgba(255,255,255,0.05);';
                    bar.innerHTML = `
                        <img src="${m.thumbnail}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;">
                        <span style="flex: 0 0 120px; color: var(--text-primary); font-weight: 500;">${m.name}</span>
                        <div style="flex: 1; background: rgba(255,255,255,0.1); border-radius: 4px; height: 20px; overflow: hidden;">
                            <div style="width: ${m.similarity}%; height: 100%; background: linear-gradient(90deg, #4285F4, #34A853); border-radius: 4px; transition: width 1s ease;"></div>
                        </div>
                        <span style="flex: 0 0 45px; text-align: right; color: var(--accent-cyan); font-weight: bold;">${m.similarity}%</span>
                    `;
                    allContainer.appendChild(bar);
                });
                
            } catch (err) {
                fmHide(fmLoading);
                fmShow(fmWebcam);
                alert('Face match failed. Please try again.');
            }
        }, 'image/jpeg', 0.9);
    });

    document.getElementById('fm-retake-btn').addEventListener('click', async () => {
        fmHide(fmResults);
        fmShow(fmWebcam);
        try {
            fmStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
            fmVideo.srcObject = fmStream;
        } catch (e) {
            alert('Camera access denied.');
        }
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
    badge.textContent = riskLevel ? riskLevel.toUpperCase() + ' RISK' : 'MEDIUM RISK';
    badge.className = `badge ${riskLevel ? riskLevel.toLowerCase() : 'medium'}`;

    // Only render the Broadcast action
    const broadcastActions = [
      { type: 'broadcast_ticket', description: 'Broadcast Entry, Exit & Seat Info to all added contacts' }
    ];

    broadcastActions.forEach((action, i) => {
        const div = document.createElement('div');
        div.className = 'action-item';
        div.innerHTML = `
            <div class="action-desc">
                <span style="color: var(--text-secondary); margin-right: 8px;">${i+1}.</span>
                ${action.description}
            </div>
            <button class="action-btn-cyan action-btn" onclick="executeAction(this, '${action.type}')" style="min-width: 120px;">
                <i class="fa-solid fa-satellite-dish"></i> Broadcast
            </button>
        `;
        container.appendChild(div);
    });
}

async function executeAction(btn, actionType) {
    if (btn.classList.contains('executed')) return;

    const savedContacts = JSON.parse(localStorage.getItem('broadcastContacts') || '[]');
    if (savedContacts.length === 0) {
        alert("Please add at least one contact in Settings first.");
        return;
    }

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending...';
    btn.disabled = true;

    try {
        let successCount = 0;

        for (const contact of savedContacts) {
            if (!contact.mobile) continue;

            let message = "";
            if (actionType === 'broadcast_ticket') {
                const namePart = contact.name ? `Hi ${contact.name}, ` : '';
                const seatPart = contact.seat ? ` Seat: ${contact.seat}.` : '';
                message = `${namePart}Your match entry is via Gate 1, exit via Gate 3.${seatPart}`;
            } else if (actionType === 'broadcast_weather') {
                const namePart = contact.name ? `Hi ${contact.name}, ` : '';
                message = `${namePart}Weather Update: Clear skies expected throughout the match. No rain predicted.`;
            }

            const response = await fetch(`/api/send-sms`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ number: contact.mobile, message: message })
            });

            if (response.ok) {
                successCount++;
            }
        }

        if (successCount > 0) {
            btn.innerHTML = `<i class="fa-solid fa-check"></i> Sent to ${successCount}`;
            btn.classList.add('executed');
            btn.style.background = 'var(--status-safe)';
        } else {
            btn.innerHTML = '<i class="fa-solid fa-xmark"></i> Failed';
            setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2000);
        }
    } catch (err) {
        console.error('[Actions] Execute error:', err);
        btn.innerHTML = '<i class="fa-solid fa-xmark"></i> Error';
        setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2000);
    }
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
