/**
 * dashboard.js  —  Real-time telemetry + YOLO AI detections
 *
 * New fields read from carState (sent by server via WebSocket):
 *   carState.traffic_light    "red" | "yellow" | "green" | "none"
 *   carState.detected_sign    "stop" | "speed_limit_50" | "yield" | "none" | …
 *   carState.yolo_confidence  0 – 100  (0 when nothing detected)
 */

let selectedCar  = localStorage.getItem('selectedCarId');
let speedChart   = null;
let batteryChart = null;


// ── Chart initialisation ─────────────────────────────────────────────────────
function initCharts() {
    const baseOpts = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { legend: { display: false } },
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                grid:  { color: 'rgba(255,255,255,0.05)' },
                ticks: { color: '#555a68', font: { family: "'JetBrains Mono', monospace", size: 10 } }
            },
            x: { display: false }
        }
    };

    speedChart = new Chart(
        document.getElementById('speedChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59,130,246,0.08)',
                borderWidth: 1.5,
                tension: 0.4,
                fill: true,
                pointRadius: 0
            }]
        },
        options: baseOpts
    });

    batteryChart = new Chart(
        document.getElementById('batteryChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor: '#22c55e',
                backgroundColor: 'rgba(34,197,94,0.08)',
                borderWidth: 1.5,
                tension: 0.4,
                fill: true,
                pointRadius: 0
            }]
        },
        options: baseOpts
    });
}

// ── Main telemetry update ────────────────────────────────────────────────────
function updateTelemetry(carState) {
    if (!carState) return;

    updateSpeed(carState.speed);
    updateBattery(carState.battery);
    updateTemperature(carState.temperature);
    updateStatus(carState.status, carState.mode);
    updateGPS(carState.gps);
    updateCharts(carState.history);

    // YOLO features
    updateTrafficLight(carState.traffic_light, carState.yolo_confidence);
    updateDetectedSign(carState.detected_sign, carState.yolo_confidence);
}

// ── Speed ────────────────────────────────────────────────────────────────────
function updateSpeed(speed) {
    const val = Math.round(speed || 0);
    document.getElementById('speedValue').textContent = val;
    document.getElementById('speedGauge').style.setProperty('--gauge-value', val);
}

// ── Battery ──────────────────────────────────────────────────────────────────
function updateBattery(battery) {
    const val = Math.round(battery || 0);
    const bar = document.getElementById('batteryBar');
    const pct = document.getElementById('batteryPercent');

    bar.style.width = `${val}%`;
    if (pct) pct.textContent = `${val}%`;

    // Color the bar based on level — uses CSS classes added in the redesign
    bar.className = 'progress-fill';
    if (val < 20)      bar.classList.add('danger');
    else if (val < 50) bar.classList.add('warning');
}

// ── Temperature ───────────────────────────────────────────────────────────────
function updateTemperature(temp) {
    const el = document.getElementById('tempValue');
    if (el) el.textContent = `${Math.round(temp || 0)}°C`;
}

// ── Status / Mode ────────────────────────────────────────────────────────────
function updateStatus(status, mode) {
    const badge = document.getElementById('statusBadge');
    const modeEl = document.getElementById('modeText');
    if (badge) {
        badge.textContent = (status || 'idle').toUpperCase();
        badge.className = `status-badge status-${status || 'idle'}`;
    }
    if (modeEl) modeEl.textContent = `Mode: ${mode || '—'}`;
}

// ── GPS ───────────────────────────────────────────────────────────────────────
function updateGPS(gps) {
    if (!gps) return;
    const lat = document.getElementById('latValue');
    const lon = document.getElementById('lonValue');
    if (lat) lat.textContent = gps.lat.toFixed(6);
    if (lon) lon.textContent = gps.lon.toFixed(6);
}

// ── Charts ────────────────────────────────────────────────────────────────────
function updateCharts(history) {
    if (!history || !speedChart || !batteryChart) return;
    const labels = history.speed.map((_, i) => i);
    speedChart.data.labels                  = labels;
    speedChart.data.datasets[0].data        = history.speed;
    batteryChart.data.labels                = labels;
    batteryChart.data.datasets[0].data      = history.battery;
    speedChart.update('none');
    batteryChart.update('none');
}

// ── TRAFFIC LIGHT ─────────────────────────────────────────────────────────────
/**
 * Lights up the correct bulb on the traffic-light housing.
 * Dims the other two.
 * Updates the label and confidence text.
 *
 * light: "red" | "yellow" | "green" | "none"
 */
function updateTrafficLight(light, confidence) {
    const lights = { red: 'tlRed', yellow: 'tlYellow', green: 'tlGreen' };
    const labels = {
        red:    'Red — car stopped',
        yellow: 'Yellow — slowing down',
        green:  'Green — proceeding',
        none:   'No signal detected'
    };

    // Dim all three bulbs first
    Object.values(lights).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('tl-active');
    });

    const labelEl = document.getElementById('tlLabel');
    const confEl  = document.getElementById('tlConf');

    if (!light || light === 'none') {
        if (labelEl) labelEl.textContent = 'No signal detected';
        if (confEl)  confEl.textContent  = '—';
        return;
    }

    // Light up the active bulb
    const activeId = lights[light];
    if (activeId) {
        const el = document.getElementById(activeId);
        if (el) el.classList.add('tl-active');
    }

    if (labelEl) labelEl.textContent = labels[light] || light;
    if (confEl)  confEl.textContent  = confidence ? `${confidence}% confidence` : '—';
}

// ── DETECTED SIGN ─────────────────────────────────────────────────────────────
/**
 * Shows a styled sign card for the detected traffic sign.
 * sign: "stop" | "speed_limit_50" | "speed_limit_30" | "yield" | "none" | …
 */
const SIGN_CONFIG = {
    stop: {
        label:  'Stop sign',
        shape:  'octagon',
        color:  '#ef4444',
        text:   'STOP'
    },
    yield: {
        label:  'Yield',
        shape:  'triangle',
        color:  '#f59e0b',
        text:   'YIELD'
    },
    speed_limit_50: {
        label:  'Speed limit sign (50)',
        shape:  'circle',
        color:  '#3b82f6',
        text:   '50'
    },
    speed_limit_30: {
        label:  'Speed limit sign (30)',
        shape:  'circle',
        color:  '#3b82f6',
        text:   '30'
    }
};

function buildSignSVG(shape, color, text) {
    const s = color;
    const w = 52, h = 52;

    if (shape === 'octagon') {
        // 8-sided stop sign
        return `<svg width="${w}" height="${h}" viewBox="0 0 52 52">
            <polygon points="16,4 36,4 48,16 48,36 36,48 16,48 4,36 4,16"
                fill="${s}" stroke="white" stroke-width="2.5"/>
            <text x="26" y="31" text-anchor="middle"
                font-family="'DM Sans',sans-serif" font-size="10"
                font-weight="700" fill="white">${text}</text>
        </svg>`;
    }
    if (shape === 'triangle') {
        return `<svg width="${w}" height="${h}" viewBox="0 0 52 52">
            <polygon points="26,4 50,48 2,48"
                fill="${s}" stroke="white" stroke-width="2.5"/>
            <text x="26" y="42" text-anchor="middle"
                font-family="'DM Sans',sans-serif" font-size="8"
                font-weight="700" fill="white">${text}</text>
        </svg>`;
    }
    // Default: circle (speed limits)
    return `<svg width="${w}" height="${h}" viewBox="0 0 52 52">
        <circle cx="26" cy="26" r="24" fill="white" stroke="${s}" stroke-width="4"/>
        <circle cx="26" cy="26" r="18" fill="white"/>
        <text x="26" y="32" text-anchor="middle"
            font-family="'JetBrains Mono',monospace" font-size="16"
            font-weight="700" fill="${s}">${text}</text>
    </svg>`;
}

function updateDetectedSign(sign, confidence) {
    const iconEl  = document.getElementById('signIcon');
    const labelEl = document.getElementById('signLabel');
    const confEl  = document.getElementById('signConf');

    if (!sign || sign === 'none') {
        if (iconEl)  iconEl.innerHTML  = buildEmptySignIcon();
        if (labelEl) labelEl.textContent = 'No sign detected';
        if (confEl)  confEl.textContent  = '—';
        return;
    }

    const cfg = SIGN_CONFIG[sign] || {
        label: sign.replace(/_/g, ' '),
        shape: 'circle',
        color: '#8b909e',
        text: '?'
    };

    if (iconEl)  iconEl.innerHTML  = buildSignSVG(cfg.shape, cfg.color, cfg.text);
    if (labelEl) labelEl.textContent = cfg.label;
    if (confEl)  confEl.textContent  = confidence ? `${confidence}% confidence` : '—';
}

function buildEmptySignIcon() {
    return `<svg width="52" height="52" viewBox="0 0 52 52" fill="none">
        <circle cx="26" cy="26" r="24" stroke="rgba(255,255,255,0.1)" stroke-width="1.5" stroke-dasharray="4 3"/>
        <line x1="16" y1="26" x2="36" y2="26" stroke="rgba(255,255,255,0.15)" stroke-width="1.5"/>
    </svg>`;
}


// ── Car selector ──────────────────────────────────────────────────────────────
async function loadCars() {
    try {
        const response = await fetch(`${SERVER_URL}/api/cars`);
        const cars = await response.json();
        const selector = document.getElementById('carSelector');
        selector.innerHTML = '<option value="">Select Car...</option>';

        Object.keys(cars).forEach(carId => {
            const opt = document.createElement('option');
            opt.value = carId;
            opt.textContent = carId;
            if (carId === selectedCar) opt.selected = true;
            selector.appendChild(opt);
        });

        if (selectedCar && cars[selectedCar]) {
            updateTelemetry(cars[selectedCar]);
        }
    } catch (err) {
        console.error('Error loading cars:', err);
    }
}

// ── Controls ──────────────────────────────────────────────────────────────────
document.getElementById('carSelector').addEventListener('change', e => {
    selectedCar = e.target.value;
    localStorage.setItem('selectedCarId', selectedCar);
    if (selectedCar) socketAPI.selectCar(selectedCar);
});

document.getElementById('emergencyStopBtn').addEventListener('click', () => {
    if (selectedCar) socketAPI.emergencyStop(selectedCar);
    else alert('Please select a car first');
});

document.getElementById('endTripBtn').addEventListener('click', () => {
    if (!selectedCar) { alert('Please select a car first'); return; }
    if (confirm('End current trip?')) { socketAPI.endTrip(selectedCar); alert('Trip ended'); }
});

document.getElementById('returnHomeBtn').addEventListener('click', () => {
    if (!selectedCar) { alert('Please select a car first'); return; }
    if (confirm(`Send ${selectedCar} back home?`)) {
        fetch(`${SERVER_URL}/api/return_home`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ car_id: selectedCar })
        }).then(() => alert(`${selectedCar} is returning home!`))
          .catch(() => alert('Failed to send home command'));
    }
});

document.getElementById('favoritePlacesBtn').addEventListener('click', () => {
    if (!selectedCar) { alert('Please select a car first'); return; }
    const places = [
        { name: 'Place 1', lat: 30.0444, lon: 31.2357 },
        { name: 'Place 2', lat: 30.0500, lon: 31.2400 },
        { name: 'Place 3', lat: 30.0600, lon: 31.2500 }
    ];
    const choice = prompt(
        `Select favourite place for ${selectedCar}:\n\n` +
        places.map((p,i) => `${i+1}. ${p.name}`).join('\n') +
        '\n\nEnter number (1–3):'
    );
    if (choice >= 1 && choice <= 3) {
        const p = places[choice - 1];
        socketAPI.setDestination(selectedCar, p.lat, p.lon);
        alert(`${selectedCar} heading to ${p.name}!`);
    }
});

// ── Socket events ─────────────────────────────────────────────────────────────
socket.on('telemetry_update', data => {
    if (selectedCar && data[selectedCar]) updateTelemetry(data[selectedCar]);
});

socket.on('critical_alert', data => {
    if (data.car_id === selectedCar && window.notifyUser) {
        window.notifyUser(data.alert.message, 'critical');
    }
});

socket.on('connect', () => {
    if (selectedCar) socketAPI.selectCar(selectedCar);
});

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    if (!selectedCar) {
        if (confirm('No car selected. Go to car selection page?')) {
            window.location.href = 'index.html';
        }
    }
    initCharts();
    loadCars();
});
