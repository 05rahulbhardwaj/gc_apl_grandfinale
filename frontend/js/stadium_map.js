/**
 * CrowdPulse AI - Premium Canvas Particle Stadium Map
 */

const MAP_CONTAINER_ID = 'stadium-map-container';

let canvas, ctx;
let particles = [];
let zoneDensities = {};
let zoneCounts = {};

const COLORS = {
    'very_low': '#3b82f6', // Blue
    'low': '#22c55e',      // Green
    'medium': '#eab308',   // Yellow
    'high': '#ef4444',     // Red
    'very_high': '#991b1b',// Dark Red
    'default': '#334155'   // Slate
};

function _internalInitStadiumMap() {
    const container = document.getElementById(MAP_CONTAINER_ID);
    if (!container) return;
    container.innerHTML = '';

    canvas = document.createElement('canvas');
    container.appendChild(canvas);

    // High DPI Canvas setup
    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    
    // Hardcoded internal resolution for layout, scaled to fit container
    const width = 800;
    const height = 600;
    
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    
    ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    
    // To scale the internal 800x600 coordinates to the actual canvas CSS size:
    const scaleX = container.clientWidth / 800;
    const scaleY = container.clientHeight / 600;
    const scale = Math.min(scaleX, scaleY);
    
    // We will draw everything centered in 800x600
    generateParticles();
    
    // Initial draw
    requestAnimationFrame(drawMap);
}

function generateParticles() {
    particles = [];
    
    const cx = 400;
    const cy = 300;
    
    // 1. Generate Stands (Concentric arcs of seats)
    // Angles in Canvas: 0 is Right(East), 90 is Down(South), 180 is Left(West), 270 is Up(North)
    for (let r = 140; r <= 280; r += 12) {
        const circumference = 2 * Math.PI * r;
        const numDots = Math.floor(circumference / 10); // spacing between dots
        
        for (let i = 0; i < numDots; i++) {
            const angle = (i / numDots) * Math.PI * 2;
            let deg = (angle * 180 / Math.PI) % 360;
            if (deg < 0) deg += 360;
            
            let zoneId = null;
            
            // Define stands with gaps for aisles
            if ((deg > 325 || deg < 35)) zoneId = 'east_stand';
            else if (deg > 55 && deg < 125) zoneId = 'south_stand';
            else if (deg > 145 && deg < 215) zoneId = 'west_stand';
            else if (deg > 235 && deg < 305) zoneId = 'north_stand';
            
            if (zoneId) {
                // Add some slight randomness for natural look
                const offsetR = r + (Math.random() * 4 - 2);
                const offsetAngle = angle + (Math.random() * 0.02 - 0.01);
                particles.push({
                    x: cx + Math.cos(offsetAngle) * offsetR,
                    y: cy + Math.sin(offsetAngle) * offsetR,
                    zoneId: zoneId,
                    size: 2.5
                });
            }
        }
    }
    
    // 2. Generate Gates & Areas (Random clusters)
    const areas = [
        { id: 'gate_3', cx: 400, cy: 60, r: 30, count: 60 },      // North
        { id: 'gate_4', cx: 650, cy: 120, r: 30, count: 50 },     // NE
        { id: 'gate_5', cx: 650, cy: 480, r: 30, count: 50 },     // SE
        { id: 'gate_1', cx: 150, cy: 480, r: 30, count: 50 },     // SW
        { id: 'gate_2', cx: 150, cy: 120, r: 30, count: 50 },     // NW
        { id: 'food_court', cx: 250, cy: 420, r: 40, count: 80 },
        { id: 'main_entrance', cx: 400, cy: 530, r: 40, count: 120 },
        { id: 'parking', cx: 400, cy: 580, r: 40, count: 80 }
    ];
    
    areas.forEach(area => {
        for (let i = 0; i < area.count; i++) {
            // Random point in circle
            const r = area.r * Math.sqrt(Math.random());
            const theta = Math.random() * 2 * Math.PI;
            particles.push({
                x: area.cx + r * Math.cos(theta),
                y: area.cy + r * Math.sin(theta),
                zoneId: area.id,
                size: 2
            });
        }
    });
}

function updateZoneColors(zones) {
    if (!zones) return;
    zones.forEach(z => {
        zoneDensities[z.zone_id] = z.density_level;
        zoneCounts[z.zone_id] = z.person_count || 0;
    });
    // Trigger redraw
    requestAnimationFrame(drawMap);
}

function drawMap() {
    if (!ctx) return;
    
    // Clear
    ctx.clearRect(0, 0, 800, 600);
    
    const cx = 400;
    const cy = 300;
    
    // Draw Grass Base
    ctx.beginPath();
    ctx.ellipse(cx, cy, 320, 320, 0, 0, 2 * Math.PI);
    const grad = ctx.createRadialGradient(cx, cy, 100, cx, cy, 320);
    grad.addColorStop(0, 'rgba(34, 197, 94, 0.05)');
    grad.addColorStop(1, 'rgba(34, 197, 94, 0)');
    ctx.fillStyle = grad;
    ctx.fill();
    
    // Draw Pitch
    ctx.fillStyle = 'rgba(202, 138, 4, 0.8)';
    ctx.fillRect(cx - 15, cy - 40, 30, 80);
    
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.lineWidth = 1;
    // Creases
    ctx.beginPath();
    ctx.moveTo(cx - 15, cy - 30); ctx.lineTo(cx + 15, cy - 30);
    ctx.moveTo(cx - 15, cy + 30); ctx.lineTo(cx + 15, cy + 30);
    ctx.stroke();

    // Draw Particles
    particles.forEach(p => {
        const density = zoneDensities[p.zoneId] || 'default';
        const color = COLORS[density];
        
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = color;
        
        // Add glow for high density
        if (density === 'high' || density === 'very_high') {
            ctx.shadowBlur = 8;
            ctx.shadowColor = color;
        } else {
            ctx.shadowBlur = 0;
        }
        
        ctx.fill();
    });
    ctx.shadowBlur = 0; // reset

    // Draw Labels
    ctx.font = 'bold 11px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    const labels = [
        { text: 'NORTH STAND', x: cx, y: cy - 200, zone: 'north_stand' },
        { text: 'SOUTH STAND', x: cx, y: cy + 200, zone: 'south_stand' },
        { text: 'EAST STAND', x: cx + 220, y: cy, zone: 'east_stand' },
        { text: 'WEST STAND', x: cx - 220, y: cy, zone: 'west_stand' },
        { text: 'GATE 3', x: cx, y: 40, zone: 'gate_3' },
        { text: 'GATE 4', x: 650, y: 100, zone: 'gate_4' },
        { text: 'GATE 5', x: 650, y: 500, zone: 'gate_5' },
        { text: 'GATE 1', x: 150, y: 500, zone: 'gate_1' },
        { text: 'GATE 2', x: 150, y: 100, zone: 'gate_2' },
        { text: 'FOOD COURT', x: 250, y: 450, zone: 'food_court' },
        { text: 'MAIN ENTRANCE', x: cx, y: 560, zone: 'main_entrance' }
    ];

    // Store label regions for click detection
    window._mapLabels = [];

    labels.forEach(l => {
        const density = zoneDensities[l.zone] || 'default';
        const color = COLORS[density];
        const count = zoneCounts[l.zone];
        
        let displayText = l.text;
        if (count !== undefined && count > 0) {
            displayText += ` (${count})`;
        }
        
        // Label background
        const metrics = ctx.measureText(displayText);
        const padX = 6; const padY = 4;
        
        const rectW = metrics.width + padX*2;
        const rectH = 12 + padY*2;
        const rectX = l.x - metrics.width/2 - padX;
        const rectY = l.y - 6 - padY;

        window._mapLabels.push({
            zone: l.zone,
            text: l.text,
            x: rectX,
            y: rectY,
            w: rectW,
            h: rectH
        });

        // Hover effect check
        const isHovered = window._hoveredZone === l.zone;
        
        ctx.fillStyle = isHovered ? 'rgba(30, 41, 59, 0.9)' : 'rgba(15, 23, 42, 0.7)';
        ctx.strokeStyle = color;
        ctx.lineWidth = isHovered ? 2 : 1;
        ctx.beginPath();
        ctx.roundRect(rectX, rectY, rectW, rectH, 4);
        
        if (isHovered) {
            ctx.shadowBlur = 10;
            ctx.shadowColor = color;
        }

        ctx.fill();
        ctx.stroke();
        ctx.shadowBlur = 0;

        ctx.fillStyle = '#f8fafc';
        ctx.fillText(displayText, l.x, l.y);
    });
}

function setupInteractivity() {
    if (window._interactivitySetup) return;
    window._interactivitySetup = true;

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        // Scale mouse coords to internal 800x600 resolution
        const scaleX = 800 / rect.width;
        const scaleY = 600 / rect.height;
        const mx = (e.clientX - rect.left) * scaleX;
        const my = (e.clientY - rect.top) * scaleY;

        let hovered = null;
        if (window._mapLabels) {
            for (let l of window._mapLabels) {
                if (mx >= l.x && mx <= l.x + l.w && my >= l.y && my <= l.y + l.h) {
                    hovered = l.zone;
                    break;
                }
            }
        }

        if (window._hoveredZone !== hovered) {
            window._hoveredZone = hovered;
            canvas.style.cursor = hovered ? 'pointer' : 'default';
            requestAnimationFrame(drawMap);
        }
    });

    canvas.addEventListener('click', async (e) => {
        if (window._hoveredZone) {
            const zoneId = window._hoveredZone;
            const label = window._mapLabels.find(l => l.zone === zoneId);
            
            if (zoneId.includes('gate') || zoneId === 'food_court') {
                openVideoModal(zoneId, label.text);
            } else {
                openCameraModal(zoneId, label.text);
            }
        }
    });
}

// Video Modal Logic
let videoCountInterval = null;

function openVideoModal(zoneId, zoneName) {
    document.getElementById('video-modal-title').innerText = `Live Feed: ${zoneName}`;
    document.getElementById('video-modal').classList.remove('hidden');
    
    // Show spinner, hide stream and overlay until first frame loads
    const spinner = document.getElementById('video-loading-spinner');
    const streamImg = document.getElementById('live-stream-img');
    const overlay = document.getElementById('video-count-overlay');
    
    if (spinner) spinner.style.display = 'flex';
    streamImg.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
    
    // When first frame arrives, swap spinner for video
    streamImg.onload = function() {
        if (spinner) spinner.style.display = 'none';
        streamImg.style.display = 'block';
        if (overlay) overlay.style.display = 'flex';
        // Only need this for the first frame
        streamImg.onload = null;
    };
    
    // Set the source of the image to the MJPEG stream endpoint
    streamImg.src = `/api/stream-gate/${zoneId}?t=${new Date().getTime()}`;

    // Reset and start polling count
    const countEl = document.getElementById('video-total-count');
    if (countEl) countEl.innerText = "0";
    if (videoCountInterval) clearInterval(videoCountInterval);
    videoCountInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/gate-count/${zoneId}`);
            if (res.ok) {
                const data = await res.json();
                if (countEl) countEl.innerText = data.count;
            }
        } catch (e) {
            // ignore
        }
    }, 1000);
}

function closeVideoModal() {
    document.getElementById('video-modal').classList.add('hidden');
    // Stop the stream by removing the src
    document.getElementById('live-stream-img').src = "";
    if (videoCountInterval) clearInterval(videoCountInterval);
}

document.getElementById('close-video-btn')?.addEventListener('click', closeVideoModal);

// Camera Modal Logic
let currentStream = null;
let currentZoneId = null;

async function openCameraModal(zoneId, zoneName) {
    currentZoneId = zoneId;
    document.getElementById('camera-modal-title').innerText = `Scanning: ${zoneName}`;
    document.getElementById('camera-modal').classList.remove('hidden');
    
    // Reset UI
    document.getElementById('webcam-video').style.display = 'block';
    document.getElementById('webcam-result').style.display = 'none';
    document.getElementById('scan-result-text').innerText = '';
    document.getElementById('capture-btn').style.display = 'block';
    document.getElementById('capture-btn').innerText = '📸 Capture & Analyze';
    document.getElementById('retake-btn').style.display = 'none';

    try {
        currentStream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.getElementById('webcam-video');
        video.srcObject = currentStream;
    } catch (err) {
        console.error("Camera error:", err);
        document.getElementById('scan-result-text').innerText = '❌ Camera access denied or not available.';
        document.getElementById('scan-result-text').style.color = '#ef4444';
        document.getElementById('capture-btn').style.display = 'none';
    }
}

function closeCameraModal() {
    document.getElementById('camera-modal').classList.add('hidden');
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        currentStream = null;
    }
}

document.getElementById('close-camera-btn')?.addEventListener('click', closeCameraModal);

document.getElementById('capture-btn')?.addEventListener('click', async () => {
    const video = document.getElementById('webcam-video');
    const canvas = document.getElementById('webcam-canvas');
    const captureBtn = document.getElementById('capture-btn');
    const resultText = document.getElementById('scan-result-text');
    
    // Draw current frame to hidden canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    
    captureBtn.innerText = '⏳ Analyzing...';
    captureBtn.disabled = true;
    
    // Convert to Blob
    canvas.toBlob(async (blob) => {
        const formData = new FormData();
        formData.append('file', blob, 'capture.jpg');
        
        try {
            const response = await fetch(`/api/zone-scan/${currentZoneId}`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Show result image
                video.style.display = 'none';
                const resultImg = document.getElementById('webcam-result');
                resultImg.src = data.annotated_image;
                resultImg.style.display = 'block';
                
                resultText.innerText = `✅ Found ${data.person_count_in_frame} people. Density: ${data.new_density.toUpperCase()}`;
                resultText.style.color = '#22c55e';
                
                captureBtn.style.display = 'none';
                document.getElementById('retake-btn').style.display = 'block';
                
                if (window.addTickerMessage) {
                    window.addTickerMessage(`Scan complete: ${data.person_count_in_frame} people detected in ${currentZoneId}.`);
                }
            } else {
                resultText.innerText = '❌ Analysis failed on server.';
                resultText.style.color = '#ef4444';
            }
        } catch (err) {
            resultText.innerText = '❌ Connection error.';
            resultText.style.color = '#ef4444';
        }
        captureBtn.disabled = false;
        captureBtn.innerText = '📸 Capture & Analyze';
    }, 'image/jpeg', 0.9);
});

document.getElementById('retake-btn')?.addEventListener('click', () => {
    document.getElementById('webcam-video').style.display = 'block';
    document.getElementById('webcam-result').style.display = 'none';
    document.getElementById('scan-result-text').innerText = '';
    document.getElementById('capture-btn').style.display = 'block';
    document.getElementById('retake-btn').style.display = 'none';
});

// Global Exports
window.initStadiumMap = () => {
    _internalInitStadiumMap();
    setupInteractivity();
};

window.updateZoneColors = updateZoneColors;
