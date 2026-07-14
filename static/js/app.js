/**
 * Krishi Mitra — Smart Farming Advisor
 * Frontend Application JavaScript
 * IBM watsonx.ai + IBM Granite
 */

/* ── State ──────────────────────────────────────────────────────── */
let currentLanguage = localStorage.getItem("km_lang") || "en";
let farmerProfile = JSON.parse(localStorage.getItem("km_profile") || "{}");
let isVoiceRecording = false;
let recognition = null;
let synth = window.speechSynthesis;
let allMandiData = [];

/* ── Init ────────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  restoreTheme();
  restoreProfile();
  loadMandiPrices("kharif_2024_25");
  checkHealth();

  // Restore language select
  const langSel = document.getElementById("langSelect");
  if (langSel) langSel.value = currentLanguage;

  // Auto-scroll chat
  scrollChatToBottom();
});

/* ── Theme ───────────────────────────────────────────────────────── */
function toggleDarkMode() {
  const html = document.documentElement;
  const isDark = html.getAttribute("data-bs-theme") === "dark";
  html.setAttribute("data-bs-theme", isDark ? "light" : "dark");
  localStorage.setItem("km_theme", isDark ? "light" : "dark");

  const icon = document.getElementById("darkModeIcon");
  if (icon) icon.className = isDark ? "bi bi-moon-stars" : "bi bi-sun-fill";
}

function restoreTheme() {
  const saved = localStorage.getItem("km_theme");
  if (saved) {
    document.documentElement.setAttribute("data-bs-theme", saved);
    const icon = document.getElementById("darkModeIcon");
    if (icon) icon.className = saved === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars";
  }
}

/* ── Section Navigation ──────────────────────────────────────────── */
function showSection(name) {
  document.querySelectorAll(".content-section").forEach(s => s.classList.remove("active"));
  const target = document.getElementById(`section-${name}`);
  if (target) {
    target.classList.add("active");
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  if (name === "mandi") loadMandiPrices(
    (document.getElementById("mandiSeason") || {}).value || "kharif_2024_25"
  );
}

function scrollToChat() {
  showSection("chat");
  setTimeout(() => {
    const inp = document.getElementById("chatInput");
    if (inp) inp.focus();
  }, 200);
}

/* ── Language ─────────────────────────────────────────────────── */
function setLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem("km_lang", lang);
  const sel = document.getElementById("langSelect");
  const pLang = document.getElementById("pLanguage");
  if (sel) sel.value = lang;
  if (pLang) pLang.value = lang;
}

/* ── Chat ────────────────────────────────────────────────────────── */
function handleKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 120) + "px";
}

async function sendMessage() {
  const input = document.getElementById("chatInput");
  if (!input) return;

  const text = input.value.trim();
  if (!text) return;

  // Append user message
  appendMessage("user", text);
  input.value = "";
  input.style.height = "auto";

  // Show typing indicator
  const typingId = showTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        language: currentLanguage,
        farmer_profile: farmerProfile,
      }),
    });

    const data = await res.json();
    removeTyping(typingId);

    if (data.error) {
      appendMessage("bot", "⚠️ " + data.error);
    } else {
      appendMessage("bot", data.response);
      // Optional TTS
      if (localStorage.getItem("km_tts") === "on") {
        speakText(data.response.replace(/[#*_`]/g, "").substring(0, 300));
      }
    }
  } catch (err) {
    removeTyping(typingId);
    appendMessage("bot",
      "⚠️ Connection error. Please check your server is running and try again.");
  }
}

function quickChat(message) {
  showSection("chat");
  setTimeout(() => {
    const input = document.getElementById("chatInput");
    if (input) {
      input.value = message;
      sendMessage();
    }
  }, 100);
}

function appendMessage(role, content) {
  const container = document.getElementById("chatMessages");
  if (!container) return;

  const div = document.createElement("div");
  div.className = `msg-row msg-${role === "user" ? "user" : "bot"}`;

  const avatar = role === "user" ? "👨‍🌾" : "🌱";
  const timeStr = new Date().toLocaleTimeString("en-IN",
    { hour: "2-digit", minute: "2-digit" });

  const bubbleClass = role === "user" ? "msg-bubble-user" : "msg-bubble-bot";
  const headerRole = role === "user" ? "You" : "Krishi Mitra";

  // Convert markdown-ish to HTML for bot messages
  let html = role === "bot" ? markdownToHtml(content) : escapeHtml(content);

  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-bubble ${bubbleClass}">
      <div class="msg-header">${headerRole} <span class="msg-time">${timeStr}</span></div>
      <div class="msg-content">${html}</div>
    </div>`;

  container.appendChild(div);
  scrollChatToBottom();
}

function scrollChatToBottom() {
  const c = document.getElementById("chatMessages");
  if (c) {
    requestAnimationFrame(() => {
      c.scrollTop = c.scrollHeight;
    });
  }
}

function showTyping() {
  const container = document.getElementById("chatMessages");
  if (!container) return null;

  const id = "typing_" + Date.now();
  const div = document.createElement("div");
  div.id = id;
  div.className = "msg-row msg-bot";
  div.innerHTML = `
    <div class="msg-avatar">🌱</div>
    <div class="msg-bubble msg-bubble-bot">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`;

  container.appendChild(div);
  scrollChatToBottom();
  return id;
}

function removeTyping(id) {
  if (id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }
}

async function clearHistory() {
  if (!confirm("Clear all chat history?")) return;
  try {
    await fetch("/api/history/clear", { method: "POST" });
    const container = document.getElementById("chatMessages");
    if (container) {
      container.innerHTML = `
        <div class="chat-date-divider"><span>Today</span></div>
        <div class="msg-row msg-bot">
          <div class="msg-avatar">🌱</div>
          <div class="msg-bubble msg-bubble-bot">
            <div class="msg-header">Krishi Mitra</div>
            <p class="mb-0">Chat cleared. Ask me anything about farming! 🌾</p>
          </div>
        </div>`;
    }
  } catch (e) {
    showToast("Could not clear history", "danger");
  }
}

/* ── Markdown renderer ───────────────────────────────────────────── */
function markdownToHtml(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Headers
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");

  // Italic
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Unordered lists
  html = html.replace(/^\s*[-•]\s(.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

  // Numbered lists
  html = html.replace(/^\s*\d+\.\s(.+)$/gm, "<li>$1</li>");

  // Inline code
  html = html.replace(/`(.+?)`/g, "<code>$1</code>");

  // Line breaks
  html = html.replace(/\n\n/g, "</p><p>");
  html = html.replace(/\n/g, "<br>");

  return `<p>${html}</p>`;
}

function escapeHtml(text) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" };
  return text.replace(/[&<>"]/g, c => map[c]);
}

/* ── PDF Download ────────────────────────────────────────────────── */
async function downloadPDF() {
  showLoading("Generating PDF Report...");
  try {
    const histRes = await fetch("/api/history");
    const history = await histRes.json();

    const res = await fetch("/api/report/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "chat_history",
        farmer_profile: farmerProfile,
        chat_history: history,
      }),
    });

    if (!res.ok) throw new Error("PDF generation failed");

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `krishi_mitra_report_${Date.now()}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast("📄 PDF Report downloaded!", "success");
  } catch (e) {
    showToast("PDF generation failed: " + e.message, "danger");
  } finally {
    hideLoading();
  }
}

/* ── Crop Recommendations ────────────────────────────────────────── */
async function getCropRecommendations() {
  showLoading("Analysing crop suitability...");
  const soilType = document.getElementById("cropSoilType").value;
  const season = document.getElementById("cropSeason").value;
  const state = document.getElementById("cropState").value;
  const irrigation = document.getElementById("cropIrrigation").value;
  const rainfall = document.getElementById("cropRainfall").value;

  try {
    const res = await fetch("/api/crop-recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ soil_type: soilType, season, state, irrigation, rainfall }),
    });
    const data = await res.json();

    const resultEl = document.getElementById("cropResult");
    resultEl.classList.remove("d-none");
    resultEl.innerHTML = `<div class="result-content">${markdownToHtml(data.recommendations)}</div>`;
    resultEl.scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    showToast("Failed to get recommendations: " + e.message, "danger");
  } finally {
    hideLoading();
  }
}

/* ── Soil Health ─────────────────────────────────────────────────── */
async function analyzeSoil() {
  showLoading("Analysing soil data...");
  const ph = parseFloat(document.getElementById("soilPH").value);
  const nitrogen = document.getElementById("soilN").value;
  const phosphorus = document.getElementById("soilP").value;
  const potassium = document.getElementById("soilK").value;
  const organic_carbon = document.getElementById("soilOC").value;
  const soil_type = document.getElementById("soilType").value;

  try {
    const res = await fetch("/api/soil-health", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ph, nitrogen, phosphorus, potassium,
                             organic_carbon, soil_type }),
    });
    const data = await res.json();

    const resultEl = document.getElementById("soilResult");
    resultEl.classList.remove("d-none");

    const score = data.soil_health_score || 50;
    document.getElementById("soilScoreVal").textContent = score;
    const bar = document.getElementById("soilScoreBar");
    if (bar) {
      bar.style.width = score + "%";
      bar.style.background = score >= 70 ? "#16a34a" :
                              score >= 45 ? "#d97706" : "#dc2626";
    }
    const circle = document.getElementById("soilScoreCircle");
    if (circle) {
      circle.style.background = score >= 70 ? "#16a34a" :
                                 score >= 45 ? "#d97706" : "#dc2626";
    }

    const textEl = document.getElementById("soilAnalysisText");
    if (textEl) {
      textEl.classList.remove("d-none");
      textEl.innerHTML = markdownToHtml(data.analysis);
    }

    resultEl.scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    showToast("Soil analysis failed: " + e.message, "danger");
  } finally {
    hideLoading();
  }
}

/* ── Weather Advisory ────────────────────────────────────────────── */
async function getWeatherAdvisory() {
  const location = document.getElementById("weatherLocation").value.trim();
  const crop = document.getElementById("weatherCrop").value.trim();

  if (!location) {
    showToast("Please enter a location", "warning");
    return;
  }

  showLoading("Fetching weather advisory...");

  try {
    const res = await fetch("/api/weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ location, crop }),
    });
    const data = await res.json();

    // Weather widget
    const widget = document.getElementById("weatherWidget");
    if (widget) {
      widget.classList.remove("d-none");
      document.getElementById("weatherLocationDisplay").textContent =
        location + (data.weather.description ? ` — ${data.weather.description}` : "");

      if (data.weather && data.weather.temp !== undefined) {
        document.getElementById("wTemp").innerHTML =
          `<i class="bi bi-thermometer-half text-danger"></i> ${data.weather.temp}°C`;
        document.getElementById("wHumidity").innerHTML =
          `<i class="bi bi-droplet text-primary"></i> ${data.weather.humidity}%`;
        document.getElementById("wWind").innerHTML =
          `<i class="bi bi-wind text-info"></i> ${data.weather.wind_speed} m/s`;

        // Set weather icon
        const desc = (data.weather.description || "").toLowerCase();
        const iconEl = document.getElementById("weatherIcon");
        if (desc.includes("rain")) iconEl.textContent = "🌧️";
        else if (desc.includes("cloud")) iconEl.textContent = "⛅";
        else if (desc.includes("clear")) iconEl.textContent = "☀️";
        else if (desc.includes("storm")) iconEl.textContent = "⛈️";
        else iconEl.textContent = "🌤️";
      }
    }

    const resultEl = document.getElementById("weatherResult");
    resultEl.classList.remove("d-none");
    resultEl.innerHTML = markdownToHtml(data.advisory);
    resultEl.scrollIntoView({ behavior: "smooth" });
  } catch (e) {
    showToast("Weather advisory failed: " + e.message, "danger");
  } finally {
    hideLoading();
  }
}

/* ── Mandi Prices ────────────────────────────────────────────────── */
async function loadMandiPrices(season) {
  try {
    const res = await fetch("/api/mandi-prices");
    const data = await res.json();

    const rows = data[season] || [];
    allMandiData = rows;
    renderMandiTable(rows);
  } catch (e) {
    console.error("Mandi prices error:", e);
  }
}

function renderMandiTable(rows) {
  const tbody = document.getElementById("mandiTableBody");
  if (!tbody) return;

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="text-center py-3 text-muted">No data available</td></tr>`;
    return;
  }

  const maxMsp = Math.max(...rows.map(r => r.msp));

  tbody.innerHTML = rows.map((r, i) => {
    const pct = Math.round((r.msp / maxMsp) * 100);
    const trend = i % 3 === 0 ? "↑" : i % 3 === 1 ? "↓" : "→";
    const trendClass = i % 3 === 0 ? "trend-up" : i % 3 === 1 ? "trend-down" : "trend-flat";
    const perTonne = (r.msp * 10).toLocaleString("en-IN");

    return `<tr>
      <td>
        <div class="fw-semibold">${r.crop}</div>
        <div class="progress mt-1" style="height:4px;width:100px">
          <div class="progress-bar bg-success" style="width:${pct}%"></div>
        </div>
      </td>
      <td class="text-end fw-semibold text-success">₹${r.msp.toLocaleString("en-IN")}</td>
      <td class="text-end text-muted">₹${perTonne}</td>
      <td class="${trendClass}">${trend}</td>
    </tr>`;
  }).join("");
}

function filterMandi(query) {
  const q = query.toLowerCase();
  const filtered = allMandiData.filter(r => r.crop.toLowerCase().includes(q));
  renderMandiTable(filtered);
}

/* ── Farmer Profile ──────────────────────────────────────────────── */
function saveProfile() {
  const profile = {
    name: (document.getElementById("pName") || {}).value || "",
    phone: (document.getElementById("pPhone") || {}).value || "",
    state: (document.getElementById("pState") || {}).value || "",
    district: (document.getElementById("pDistrict") || {}).value || "",
    land_size: (document.getElementById("pLand") || {}).value || "",
    soil_type: (document.getElementById("pSoilType") || {}).value || "",
    water_source: (document.getElementById("pWaterSource") || {}).value || "",
    season: (document.getElementById("pSeason") || {}).value || "",
    crops: (document.getElementById("pCrops") || {}).value || "",
    language: (document.getElementById("pLanguage") || {}).value || "en",
  };

  farmerProfile = profile;
  localStorage.setItem("km_profile", JSON.stringify(profile));

  // Sync language
  if (profile.language) setLanguage(profile.language);

  // Save to server session
  fetch("/api/profile", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });

  // Update sidebar mini card
  updateProfileMiniCard(profile);

  showToast("✅ Profile saved! Chat personalised.", "success");
  showSection("chat");
}

function restoreProfile() {
  const saved = JSON.parse(localStorage.getItem("km_profile") || "{}");
  if (!saved || !Object.keys(saved).length) return;

  farmerProfile = saved;

  const fields = ["name", "phone", "state", "district",
                   "land_size", "soil_type", "water_source",
                   "season", "crops", "language"];

  const idMap = {
    name: "pName", phone: "pPhone", state: "pState",
    district: "pDistrict", land_size: "pLand",
    soil_type: "pSoilType", water_source: "pWaterSource",
    season: "pSeason", crops: "pCrops", language: "pLanguage",
  };

  fields.forEach(f => {
    const el = document.getElementById(idMap[f]);
    if (el && saved[f]) el.value = saved[f];
  });

  if (saved.language) setLanguage(saved.language);
  updateProfileMiniCard(saved);
}

function updateProfileMiniCard(profile) {
  const body = document.getElementById("profileMiniBody");
  if (!body) return;
  if (!profile.name) return;

  body.innerHTML = `
    <div class="mb-1"><strong>${profile.name}</strong></div>
    ${profile.state ? `<div class="small text-muted">${profile.state}</div>` : ""}
    ${profile.soil_type ? `<div class="small text-muted">Soil: ${profile.soil_type}</div>` : ""}
    ${profile.land_size ? `<div class="small text-muted">Land: ${profile.land_size} acres</div>` : ""}
    <button class="btn btn-sm btn-outline-success w-100 mt-2" onclick="showSection('profile')">
      <i class="bi bi-pencil me-1"></i>Edit Profile
    </button>`;
}

/* ── Voice Input ─────────────────────────────────────────────────── */
function toggleVoiceInput() {
  if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
    showToast("Voice input not supported in this browser. Try Chrome.", "warning");
    return;
  }

  if (isVoiceRecording) {
    stopVoiceInput();
  } else {
    startVoiceInput();
  }
}

function startVoiceInput() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRec();

  // Map language code to BCP47
  const langMap = {
    en: "en-IN", hi: "hi-IN", pa: "pa-IN", te: "te-IN",
    ta: "ta-IN", mr: "mr-IN", kn: "kn-IN", gu: "gu-IN", bn: "bn-IN",
  };
  recognition.lang = langMap[currentLanguage] || "en-IN";
  recognition.continuous = false;
  recognition.interimResults = true;

  recognition.onstart = () => {
    isVoiceRecording = true;
    const btn = document.getElementById("voiceBtn");
    if (btn) btn.classList.add("recording");
    showToast("🎤 Listening... Speak your question", "success");
  };

  recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }
    const input = document.getElementById("chatInput");
    if (input) {
      input.value = transcript;
      autoResize(input);
    }
  };

  recognition.onend = () => {
    isVoiceRecording = false;
    const btn = document.getElementById("voiceBtn");
    if (btn) btn.classList.remove("recording");

    const input = document.getElementById("chatInput");
    if (input && input.value.trim()) {
      setTimeout(() => sendMessage(), 300);
    }
  };

  recognition.onerror = (e) => {
    isVoiceRecording = false;
    const btn = document.getElementById("voiceBtn");
    if (btn) btn.classList.remove("recording");
    if (e.error !== "no-speech") {
      showToast("Voice error: " + e.error, "warning");
    }
  };

  recognition.start();
}

function stopVoiceInput() {
  if (recognition) recognition.stop();
  isVoiceRecording = false;
  const btn = document.getElementById("voiceBtn");
  if (btn) btn.classList.remove("recording");
}

/* ── TTS ─────────────────────────────────────────────────────────── */
function speakText(text) {
  if (!synth) return;
  synth.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  const langMap = { en: "en-IN", hi: "hi-IN", pa: "pa-IN", te: "te-IN", ta: "ta-IN" };
  utt.lang = langMap[currentLanguage] || "en-IN";
  utt.rate = 0.9;
  synth.speak(utt);
}

/* ── UI Helpers ──────────────────────────────────────────────────── */
function showLoading(text = "Please wait...") {
  const overlay = document.getElementById("loadingOverlay");
  const txt = document.getElementById("loadingText");
  if (overlay) overlay.classList.remove("d-none");
  if (txt) txt.textContent = text;
}

function hideLoading() {
  const overlay = document.getElementById("loadingOverlay");
  if (overlay) overlay.classList.add("d-none");
}

function showToast(msg, type = "success") {
  const toast = document.getElementById("kmToast");
  const msgEl = document.getElementById("kmToastMsg");
  if (!toast || !msgEl) return;

  msgEl.textContent = msg;
  toast.className = `toast align-items-center border-0 show text-bg-${type}`;

  const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
  bsToast.show();
}

/* ── Health Check ────────────────────────────────────────────────── */
async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    const statusEl = document.getElementById("agentStatus");
    if (statusEl) {
      if (data.watsonx_status === "connected") {
        statusEl.innerHTML = `<span class="status-dot bg-success"></span>
          IBM Granite AI Connected`;
      } else {
        statusEl.innerHTML = `<span class="status-dot bg-warning"></span>
          Fallback Mode (Set API Key)`;
      }
    }
  } catch (e) {
    const statusEl = document.getElementById("agentStatus");
    if (statusEl) {
      statusEl.innerHTML = `<span class="status-dot bg-danger"></span>
        Server Offline`;
    }
  }
}
