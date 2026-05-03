// ═══════════════════════════════════════════════════
//  ECHO MIND — app.js  (desktop, no voice)
// ═══════════════════════════════════════════════════

// ─── SCREEN / PANEL SWITCHING ───────────────────────
function goToScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.add('hidden'));
    document.getElementById(id).classList.remove('hidden');
}

function showPanel(id) {
    document.querySelectorAll('.panel').forEach(p => p.classList.add('hidden'));
    document.getElementById(id).classList.remove('hidden');

    // sync sidebar active state
    document.querySelectorAll('.sidebar-btn').forEach(btn => btn.classList.remove('active'));
    const map = { 'panel-home': 0, 'panel-chat': 1 };
    const idx = map[id];
    if (idx !== undefined) {
        document.querySelectorAll('.sidebar-btn')[idx]?.classList.add('active');
    }
}

// ─── LOGIN ───────────────────────────────────────────
async function handleLogin() {
    const nameEl  = document.getElementById('login-name');
    const emailEl = document.getElementById('login-email');
    const passEl  = document.getElementById('login-password');
    const errEl   = document.getElementById('login-error');

    const name  = nameEl.value.trim();
    const email = emailEl.value.trim();
    const pass  = passEl.value.trim();

    if (!name || !email || !pass) {
        errEl.textContent = 'Please fill in all fields.';
        errEl.classList.remove('hidden');
        return;
    }
    errEl.classList.add('hidden');

    // Save user data to server (stored in users.json)
    try {
        await fetch('/save-user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email })
        });
    } catch (e) {
        console.warn('Could not save user to server:', e);
    }

    // Also keep name in sessionStorage for this tab
    sessionStorage.setItem('echoMindUser', name);

    applyUsername(name);
    goToScreen('screen-welcome');
}

function handleLogout() {
    sessionStorage.removeItem('echoMindUser');
    goToScreen('screen-login');
}

function applyUsername(name) {
    const greeting = name + '! 👋';
    const el1 = document.getElementById('home-username');
    const el2 = document.getElementById('sidebar-username');
    if (el1) el1.textContent = greeting;
    if (el2) el2.textContent = name;
}

// ─── CHAT SEND ───────────────────────────────────────
async function sendMessage() {
    const input = document.getElementById("chat-input");
    const msg = input.value.trim();
    if (!msg) return;

    addUserMessage(msg);
    input.value = "";
    showTyping(true);

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg, session_id: "default" })
        });
        const data = await res.json();
        showTyping(false);
        addBotMessage(data.reply);
    } catch (err) {
        showTyping(false);
        addBotMessage("⚠️ Error connecting to server");
    }
}

function addUserMessage(text) {
    const chat = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "msg user-msg";
    div.innerHTML = `<div class="user-bubble">${text}</div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function addBotMessage(text) {
    const chat = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "msg bot-msg";
    div.innerHTML = `
        <div class="bot-bubble">
            <div class="bot-avatar-sm">🤖</div>
            <div class="bubble">${text}</div>
        </div>`;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

function showTyping(show) {
    const t = document.getElementById("typing-indicator");
    if (show) t.classList.remove("hidden");
    else t.classList.add("hidden");
}

function clearChat() {
    const chat = document.getElementById("chat-messages");
    chat.innerHTML = `
      <div class="msg bot-msg">
        <div class="bot-bubble">
          <div class="bot-avatar-sm">🤖</div>
          <div class="bubble">
            <p>👋 Hi! I'm <strong>Echo Mind</strong>. Ask me anything!</p>
            <span class="msg-time">Now</span>
          </div>
        </div>
      </div>`;
}

function selectTopic(id, label) {
    // highlight chip
    document.querySelectorAll('.topic-chip').forEach(c => c.classList.remove('active'));
    document.querySelector(`.topic-chip[data-topic="${id}"]`)?.classList.add('active');
    // switch to chat and pre-fill
    showPanel('panel-chat');
    const input = document.getElementById('chat-input');
    if (input) { input.value = `Tell me about ${label}`; input.focus(); }
}

function askFromHistory(question) {
    showPanel('panel-chat');
    const input = document.getElementById('chat-input');
    if (input) { input.value = question; input.focus(); }
}

// ─── INIT ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    // Enter key in chat
    const input = document.getElementById("chat-input");
    if (input) {
        input.addEventListener("keypress", e => {
            if (e.key === "Enter") sendMessage();
        });
    }

    // Enter key in login
    ['login-name','login-email','login-password'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('keypress', e => { if (e.key === 'Enter') handleLogin(); });
    });

    // Auto-login if name already in session
    const saved = sessionStorage.getItem('echoMindUser');
    if (saved) {
        applyUsername(saved);
        goToScreen('screen-home');
    }
});
