// ==========================================================================
// DASHBOARD CONTROLLER & STATE MANAGEMENT
// ==========================================================================

let globalStudentConfig = null;
let latestCalcResult = null;

document.addEventListener("DOMContentLoaded", async () => {
  // 1. Load config from localStorage or default
  loadStudentConfig();

  // 2. Setup date picker listeners
  const picker = document.getElementById("inp-future-date");
  picker.addEventListener("change", async (e) => {
    const val = e.target.value;
    globalStudentConfig.target_date = val;
    localStorage.setItem("smart_attendance_config", JSON.stringify(globalStudentConfig));
    await fetchAndRenderDashboard();
  });

  // 3. Tab Buttons setup
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      
      btn.classList.add("active");
      const targetTab = btn.dataset.tab;
      document.getElementById(targetTab).classList.add("active");
    });
  });

  // 4. Initial Fetch
  await fetchAndRenderDashboard();
});

function loadStudentConfig() {
  const saved = localStorage.getItem("smart_attendance_config");
  if (saved) {
    globalStudentConfig = JSON.parse(saved);
  } else {
    // Default sample data for instant demonstration
    globalStudentConfig = {
      student_name: "Alex Morgan",
      section_id: "section_A",
      start_date: "2026-09-28",
      target_date: "2026-11-29",
      subjects: [
        { code: "CS501", name: "Java Programming", conducted: 40, attended: 32 }, // 80%
        { code: "CS502", name: "Database Management Systems", conducted: 40, attended: 31 }, // 77.5%
        { code: "CS503", name: "Mathematics III", conducted: 38, attended: 31 }, // 81.5%
        { code: "CS504", name: "Computer Networks", conducted: 40, attended: 29 }, // 72.5%
        { code: "CS505", name: "Web Technology", conducted: 35, attended: 25 }, // 71.4%
        { code: "CS506", name: "Software Engineering", conducted: 40, attended: 36 }  // 90.0%
      ]
    };
    localStorage.setItem("smart_attendance_config", JSON.stringify(globalStudentConfig));
  }

  // Update header text
  document.getElementById("user-display-name").textContent = globalStudentConfig.student_name || "Student";
  if (globalStudentConfig.target_date) {
    document.getElementById("inp-future-date").value = globalStudentConfig.target_date;
  }
}

async function fetchAndRenderDashboard() {
  try {
    const response = await fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(globalStudentConfig)
    });

    const data = await response.json();
    latestCalcResult = data;

    // Render components
    renderHeaderInfo(data);
    renderKPIs(data.overall);
    renderDetentionBanner(data.subjects);
    renderSubjectCards(data.subjects);

    // Call external renderers
    if (window.renderDashboardCharts) {
      window.renderDashboardCharts(data);
    }
    if (window.renderHeatmap) {
      window.renderHeatmap(data.timetable_summary.by_date);
    }
    if (window.renderDigitalTwin) {
      window.renderDigitalTwin(globalStudentConfig);
    }
    if (window.renderRecoveryPath) {
      window.renderRecoveryPath(data.subjects);
    }

  } catch (err) {
    console.error("Error fetching dashboard calculations:", err);
  }
}

function renderHeaderInfo(data) {
  document.getElementById("user-sec-badge").textContent = `${data.section.name} (${data.section.department})`;
  document.getElementById("lbl-today-date").textContent = formatDateReadable(data.timetable_summary.start_date);

  // Semester timeline progress bar (29 Aug 2026 -> 29 Nov 2026 total 92 days)
  const start = new Date("2026-08-29");
  const end = new Date("2026-11-29");
  const today = new Date(data.timetable_summary.start_date);

  const totalDays = Math.round((end - start) / (1000 * 60 * 60 * 24));
  const passedDays = Math.max(0, Math.round((today - start) / (1000 * 60 * 60 * 24)));
  const pct = Math.min(100, Math.round((passedDays / totalDays) * 100));

  document.getElementById("lbl-sem-days-passed").textContent = `Day ${passedDays} of ${totalDays}`;
  document.getElementById("sem-progress-fill").style.width = `${pct}%`;
}

function renderKPIs(overall) {
  document.getElementById("kpi-overall-pct").textContent = `${overall.overall_current_pct}%`;
  
  const overallBadge = document.getElementById("kpi-overall-badge");
  overallBadge.textContent = overall.overall_current_pct >= 80 ? "Safe" : (overall.overall_current_pct >= 75 ? "Warning" : "Danger");
  overallBadge.className = `kpi-badge ${overall.overall_current_pct >= 80 ? 'safe' : (overall.overall_current_pct >= 75 ? 'warning' : 'danger')}`;

  document.getElementById("kpi-risk-count").textContent = overall.at_risk_count;
  document.getElementById("kpi-rem-classes").textContent = overall.total_remaining;
  document.getElementById("kpi-safe-misses").textContent = overall.total_safe_misses;
}

function renderDetentionBanner(subjects) {
  const detentionBanner = document.getElementById("detention-alert-banner");
  const grid = document.getElementById("detention-details-grid");
  grid.innerHTML = "";

  const detentions = subjects.filter(s => s.is_detention);

  if (detentions.length > 0) {
    detentions.forEach(s => {
      grid.innerHTML += `
        <div class="detention-item-card">
          <h4>${s.name} (${s.short_name})</h4>
          <p>Current: <strong>${s.current_pct}%</strong> | Max Possible: <strong>${s.max_possible_pct}%</strong></p>
          <p style="color:#fecdd3; margin-top:0.2rem;">Remaining: ${s.remaining_classes} classes | 75% Requirement Unachievable</p>
        </div>
      `;
    });
    detentionBanner.style.display = "flex";
  } else {
    detentionBanner.style.display = "none";
  }
}

function renderSubjectCards(subjects) {
  const grid = document.getElementById("subject-cards-grid");
  grid.innerHTML = "";

  subjects.forEach(sub => {
    const card = document.createElement("div");
    card.className = `subject-card state-${sub.status_code.toLowerCase()}`;

    let missText = "";
    if (sub.can_miss_75 > 0) {
      missText = `<span class="safe-miss-line"><i class="fa-solid fa-circle-check"></i> Safe to miss: <strong>${sub.can_miss_75} classes</strong></span>`;
    } else if (sub.is_detention) {
      missText = `<span class="danger-miss-line"><i class="fa-solid fa-triangle-exclamation"></i> 🚨 Irreversible Detention Warning</span>`;
    } else {
      missText = `<span class="danger-miss-line"><i class="fa-solid fa-triangle-exclamation"></i> Cannot miss any class! Attend next <strong>${sub.required_75} classes</strong>.</span>`;
    }

    let target90Text = "";
    if (sub.is_90_achievable) {
      target90Text = `Attend <strong>${sub.required_90} classes</strong> to reach 90%`;
    } else {
      target90Text = `<span style="color:var(--text-muted);">90% Target Not Achievable (Max ${sub.max_possible_pct}%)</span>`;
    }

    card.innerHTML = `
      <div class="sub-card-top">
        <div class="sub-name-block">
          <h3>${sub.name}</h3>
          <p>${sub.code} • ${sub.faculty || 'Faculty'}</p>
        </div>
        <div class="status-indicator-badge ${sub.status_code}">
          ${sub.status_icon} ${sub.status_label}
        </div>
      </div>

      <div class="sub-pct-display">
        <span class="pct-num">${sub.current_pct}%</span>
        <span class="sub-header-tag">Max: ${sub.max_possible_pct}%</span>
      </div>

      <div class="sub-progress-track">
        <div class="sub-progress-fill ${sub.status_code}" style="width: ${Math.min(100, sub.current_pct)}%;"></div>
      </div>

      <div class="sub-metrics-grid">
        <div class="metric-item">
          <span>Conducted</span>
          <strong>${sub.conducted}</strong>
        </div>
        <div class="metric-item">
          <span>Attended</span>
          <strong>${sub.attended}</strong>
        </div>
        <div class="metric-item">
          <span>Remaining</span>
          <strong>${sub.remaining_classes}</strong>
        </div>
      </div>

      <div class="sub-action-footer">
        ${missText}
        <div class="target-90-line"><i class="fa-solid fa-bullseye"></i> 90% Target: ${target90Text}</div>
      </div>
    `;

    grid.appendChild(card);
  });
}

function formatDateReadable(dateStr) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" });
  } catch (e) {
    return dateStr;
  }
}
