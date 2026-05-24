// ─── UI Elements ───
const chatBox = document.getElementById('chat-box');
const terminalBox = document.getElementById('terminal-box');
const liveTranscriptEl = document.getElementById('live-transcript');
const statusTag = document.getElementById('status-tag');
const energyFlux = document.getElementById('energy-flux');
const neuralLink = document.getElementById('neural-link');
const headerTime = document.getElementById('header-time');
const headerDate = document.getElementById('header-date');
const footerUptime = document.getElementById('footer-uptime');
const netLabel = document.getElementById('net-label');
const tempVal = document.getElementById('temp-val');

const cpuVal = document.getElementById('cpu-val');
const ramVal = document.getElementById('ram-val');
const netVal = document.getElementById('net-val');
const cpuRing = document.getElementById('cpu-ring');
const ramRing = document.getElementById('ram-ring');
const netRing = document.getElementById('net-ring');

const GAUGE_CIRC = 213.6;

// Speech
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechRecognition ? new SpeechRecognition() : null;
const synth = window.speechSynthesis;

if (recognition) {
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';
}

const HINGLISH_WORDS = new Set([
    "main", "hoon", "he", "hu", "aap", "bataiye", "batao", "kaise", "hain", "hai", "ho",
    "bahut", "kuch", "kya", "karun", "theek", "nahi", "haan", "mera", "aapka", "bhai"
]);

function isHinglish(text) {
    if (/[\u0900-\u097F]/.test(text)) return true;
    const words = text.toLowerCase().match(/\b[a-z]+\b/g);
    if (!words) return false;
    let n = 0;
    for (const w of words) if (HINGLISH_WORDS.has(w)) n++;
    return n >= 2 || n / words.length >= 0.2;
}

let isActiveSession = false;
let isSpeaking = false;
let currentUtterance = null;
const sparkHistory = [];

// ─── Gauge & HUD helpers ───
function setGauge(ringEl, percent) {
    if (!ringEl) return;
    const p = Math.min(100, Math.max(0, percent));
    ringEl.style.strokeDashoffset = String(GAUGE_CIRC - (GAUGE_CIRC * p) / 100);
}

function setCoreStatus(status, link) {
    if (statusTag) statusTag.textContent = status;
    if (neuralLink) neuralLink.textContent = link || status;
}

function pulseCore(on) {
    const glow = document.getElementById('core-glow');
    if (glow) glow.classList.toggle('active-pulse', on);
}

function drawSparkline() {
    const canvas = document.getElementById('sparkline');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    if (sparkHistory.length < 2) return;
    ctx.strokeStyle = '#ff4400';
    ctx.lineWidth = 2;
    ctx.shadowColor = '#ff3300';
    ctx.shadowBlur = 8;
    ctx.beginPath();
    const step = w / (sparkHistory.length - 1);
    sparkHistory.forEach((v, i) => {
        const y = h - (v / 100) * (h - 8) - 4;
        if (i === 0) ctx.moveTo(0, y);
        else ctx.lineTo(i * step, y);
    });
    ctx.stroke();
}

// ─── Mobile panel navigation ───
function showPanel(name) {
    document.querySelectorAll('.col').forEach((col) => {
        col.classList.toggle('active-panel', col.dataset.panel === name);
    });
    document.querySelectorAll('.nav-btn[data-nav]').forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.nav === name);
    });
}

document.querySelectorAll('.nav-btn[data-nav]').forEach((btn) => {
    btn.addEventListener('click', () => showPanel(btn.dataset.nav));
});

document.getElementById('nav-command')?.addEventListener('click', () => {
    showPanel('core');
    document.querySelector('.command-section')?.scrollIntoView({ behavior: 'smooth' });
});

document.getElementById('nav-settings')?.addEventListener('click', () => {
    addChatMessage('Settings: use Chrome, allow mic, run python server.py on PC.', 'jarvis-msg');
    showPanel('comms');
});

document.querySelectorAll('.hub-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.hub-tab').forEach((t) => t.classList.remove('active'));
        tab.classList.add('active');
        const isChat = tab.dataset.tab === 'chat';
        if (chatBox) chatBox.style.display = isChat ? 'block' : 'none';
        if (terminalBox) terminalBox.style.display = isChat ? 'none' : 'block';
    });
});

// ─── Terminal log ───
function logToTerminal(message, type = 'INFO') {
    const time = new Date().toLocaleTimeString().split(' ')[0];
    const line = document.createElement('div');
    line.className = 'terminal-line';
    line.innerText = `[${time}] [${type}] ${message}`;
    terminalBox.appendChild(line);
    terminalBox.scrollTop = terminalBox.scrollHeight;
    if (terminalBox.childNodes.length > 50) terminalBox.removeChild(terminalBox.firstChild);
}

// ─── Speech recognition ───
function initSpeech() {
    if (!recognition) {
        logToTerminal('Speech API not supported in this browser.', 'ERROR');
        return;
    }
    try {
        recognition.start();
        setCoreStatus('LISTENING', 'ESTABLISHED');
        logToTerminal('Neural Bridge online', 'SYSTEM');
    } catch (e) {
        logToTerminal('Mic init: ' + e.message, 'ERROR');
    }
}

if (recognition) {
    recognition.onresult = (event) => {
        let interim = '';
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) final += event.results[i][0].transcript;
            else interim += event.results[i][0].transcript;
        }
        if (interim) {
            liveTranscriptEl.innerText = interim;
        }
        if (final) {
            const text = final.toLowerCase().trim();
            logToTerminal(text, 'USER');
            liveTranscriptEl.innerText = 'Listening...';

            if (isSpeaking) {
                synth.cancel();
                isSpeaking = false;
                setCoreStatus(isActiveSession ? 'ACTIVE' : 'STANDBY', isActiveSession ? 'ESTABLISHED' : 'STANDBY');
                pulseCore(isActiveSession);
                const stops = ['stop', 'stop jarvis', 'quiet', 'bas', 'ruko'];
                if (stops.some((p) => text.includes(p))) return;
            }

            if (!isActiveSession) {
                if (text.includes('jarvis') || text.includes('hey jarvis')) wakeUpJarvis();
            } else {
                handleCommand(text);
            }
        }
    };

    recognition.onerror = (event) => {
        logToTerminal('Mic: ' + event.error, 'ERROR');
        if (event.error === 'not-allowed') {
            addChatMessage('Allow microphone in browser settings.', 'jarvis-msg');
        }
    };

    recognition.onend = () => {
        setTimeout(() => {
            try { recognition.start(); } catch (_) {}
        }, 400);
    };
}

document.getElementById('manual-mic')?.addEventListener('click', () => {
    if (!isActiveSession) wakeUpJarvis();
    else addChatMessage('Already active, Mr Aryan.', 'jarvis-msg');
});

function wakeUpJarvis() {
    isActiveSession = true;
    setCoreStatus('ACTIVE', 'ESTABLISHED');
    if (energyFlux) energyFlux.textContent = '94%';
    pulseCore(true);
    addChatMessage('System online. How can I help, Mr Aryan?', 'jarvis-msg');
    speak('Yes Mr Aryan. I am listening.');
    logToTerminal('Session active', 'AUTH');
    updateTasks(2, 1);
}

async function handleCommand(text) {
    if (['stop jarvis', 'go to sleep', 'shut down'].includes(text)) {
        isActiveSession = false;
        setCoreStatus('STANDBY', 'STANDBY');
        if (energyFlux) energyFlux.textContent = '72%';
        pulseCore(false);
        addChatMessage('Standby mode.', 'jarvis-msg');
        speak('Understood sir. Standby.');
        updateTasks(1, 0);
        return;
    }

    addChatMessage(text, 'user-msg');
    setCoreStatus('THINKING', 'PROCESSING');
    logToTerminal('Processing...', 'THINK');

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const data = await res.json();
        addChatMessage(data.response, 'jarvis-msg');
        setCoreStatus('ACTIVE', 'ESTABLISHED');
        speak(data.response);
        logToTerminal('Response ready', 'AI');
    } catch (_) {
        setCoreStatus('OFFLINE', 'FAILED');
        if (netLabel) netLabel.textContent = 'LINK: OFFLINE';
        logToTerminal('Backend offline — run server.py', 'CRITICAL');
        addChatMessage('Server offline. Run python server.py on your PC.', 'jarvis-msg');
    }
}

function speak(text) {
    if (!synth) return;
    if (synth.speaking) synth.cancel();

    const voices = synth.getVoices();
    const hindi = isHinglish(text);
    let voice;
    if (hindi) {
        voice = voices.find((v) => v.lang.includes('hi')) || voices.find((v) => v.lang.includes('en'));
    } else {
        voice = voices.find((v) => v.lang.includes('en-IN')) ||
            voices.find((v) => v.name.includes('Male') && v.lang.includes('en')) ||
            voices.find((v) => v.lang.includes('en'));
    }

    currentUtterance = new SpeechSynthesisUtterance(text);
    currentUtterance.voice = voice || voices[0];
    currentUtterance.rate = hindi ? 1.35 : 1.0;
    currentUtterance.pitch = 0.9;

    currentUtterance.onstart = () => {
        isSpeaking = true;
        setCoreStatus('SPEAKING', 'ESTABLISHED');
        pulseCore(true);
    };
    currentUtterance.onend = () => {
        isSpeaking = false;
        setCoreStatus(isActiveSession ? 'ACTIVE' : 'STANDBY', isActiveSession ? 'ESTABLISHED' : 'STANDBY');
        pulseCore(isActiveSession);
    };

    if (synth.paused) synth.resume();
    synth.speak(currentUtterance);
}

document.getElementById('unlock-voice')?.addEventListener('click', () => {
    const u = new SpeechSynthesisUtterance('Jarvis protocol online.');
    u.voice = synth.getVoices().find((v) => v.lang.includes('en')) || synth.getVoices()[0];
    synth.speak(u);
    logToTerminal('Voice unlocked', 'SYSTEM');
});

function addChatMessage(text, className) {
    const div = document.createElement('div');
    div.className = `chat-message ${className}`;
    div.innerText = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function updateTasks(active, pending) {
    const a = document.getElementById('tasks-active');
    const p = document.getElementById('tasks-pending');
    if (a) a.textContent = String(active);
    if (p) p.textContent = String(pending);
}

async function updateStats() {
    try {
        const res = await fetch('/stats');
        const d = await res.json();
        const cpu = Math.round(d.cpu);
        const ram = Math.round(d.ram);

        cpuVal.textContent = cpu + '%';
        ramVal.textContent = ram + '%';
        setGauge(cpuRing, cpu);
        setGauge(ramRing, ram);

        const netOk = d.network > 0;
        netVal.textContent = netOk ? 'OK' : '--';
        setGauge(netRing, netOk ? 85 : 20);
        if (netLabel) netLabel.textContent = 'LINK: ACTIVE';
        if (footerUptime) footerUptime.textContent = 'UPTIME ' + d.uptime + 's';
        if (energyFlux && !isSpeaking) energyFlux.textContent = Math.min(99, 60 + Math.round((100 - cpu) / 3)) + '%';

        sparkHistory.push(cpu);
        if (sparkHistory.length > 24) sparkHistory.shift();
        drawSparkline();
    } catch (_) {
        if (netLabel) netLabel.textContent = 'LINK: LOCAL';
    }
}

function updateClock() {
    const now = new Date();
    if (headerTime) headerTime.textContent = now.toTimeString().slice(0, 5);
    if (headerDate) {
        const months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
        headerDate.textContent =
            String(now.getDate()).padStart(2, '0') + ' ' + months[now.getMonth()] + ' ' + now.getFullYear();
    }
    if (tempVal) tempVal.textContent = Math.round(22 + Math.sin(now.getHours() / 4) * 4) + '°';
}

// Init
window.onload = () => {
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(updateStats, 2000);
    setGauge(cpuRing, 0);
    setGauge(ramRing, 0);
    setGauge(netRing, 50);

    logToTerminal('Welcome Mr Aryan.', 'SYSTEM');
    logToTerminal('Tap screen to enable mic.', 'SYSTEM');

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    const startMic = () => {
        if (recognition) initSpeech();
    };
    document.body.addEventListener('touchstart', startMic, { once: true });
    document.body.addEventListener('click', startMic, { once: true });

    if (window.innerWidth < 900) showPanel('core');
    if (chatBox) chatBox.style.display = 'none';
};

// Load voices (Android Chrome)
if (synth) {
    synth.onvoiceschanged = () => synth.getVoices();
}
