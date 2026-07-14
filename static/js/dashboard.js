/**
 * Krishi Mitra — Dashboard JavaScript
 * MSP chart + dashboard logic
 */

document.addEventListener("DOMContentLoaded", () => {
  restoreTheme();
  renderMspChart();
  loadSoilScore();
});

/* ── MSP Bar Chart ─────────────────────────────────────────────── */
function renderMspChart() {
  const container = document.getElementById("mspChart");
  if (!container) return;

  const data = [
    { crop: "🌿 Cotton (Long)", msp: 7521 },
    { crop: "🌿 Cotton (Medium)", msp: 7121 },
    { crop: "🫘 Moong", msp: 8682 },
    { crop: "🫘 Arhar", msp: 7550 },
    { crop: "🫘 Urad", msp: 7400 },
    { crop: "🥜 Groundnut", msp: 6783 },
    { crop: "🌻 Mustard", msp: 5950 },
    { crop: "🫘 Soybean", msp: 4892 },
    { crop: "🌾 Wheat", msp: 2275 },
    { crop: "🌾 Paddy", msp: 2300 },
    { crop: "🌾 Maize", msp: 2225 },
    { crop: "🌾 Bajra", msp: 2625 },
  ].sort((a, b) => b.msp - a.msp);

  const maxVal = Math.max(...data.map(d => d.msp));
  const colors = [
    "#16a34a", "#1d9e5e", "#22c55e", "#4ade80",
    "#86efac", "#0891b2", "#0ea5e9", "#38bdf8",
    "#7c3aed", "#a78bfa", "#d97706", "#f59e0b",
  ];

  container.innerHTML = data.map((d, i) => {
    const pct = Math.round((d.msp / maxVal) * 100);
    return `
      <div class="msp-bar-row">
        <div class="msp-crop-name">${d.crop}</div>
        <div class="msp-bar-bg">
          <div class="msp-bar-fill" style="width:0%;background:${colors[i % colors.length]}"
               data-width="${pct}">
            <span class="msp-value">₹${d.msp.toLocaleString("en-IN")}</span>
          </div>
        </div>
      </div>`;
  }).join("");

  // Animate bars after render
  setTimeout(() => {
    container.querySelectorAll(".msp-bar-fill").forEach(bar => {
      bar.style.width = bar.getAttribute("data-width") + "%";
    });
  }, 100);
}

/* ── Soil Score from localStorage ───────────────────────────────── */
function loadSoilScore() {
  const el = document.getElementById("dashSoilScore");
  if (!el) return;
  const profile = JSON.parse(localStorage.getItem("km_profile") || "{}");
  if (profile.name) {
    el.textContent = "Check →";
    el.parentElement.querySelector(".kpi-sub").textContent =
      `Hi ${profile.name.split(" ")[0]}! 👋`;
  }
}
