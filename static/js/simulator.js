// ==========================================================================
// SIMULATOR, HEATMAP, DIGITAL TWIN & RECOVERY ENGINE
// ==========================================================================

let currentByDateMap = {};

// 1. HEATMAP RENDERER
window.renderHeatmap = function(byDateMap) {
  currentByDateMap = byDateMap || {};
  const grid = document.getElementById("heatmap-grid");
  if (!grid) return;

  grid.innerHTML = "";
  const dates = Object.keys(currentByDateMap).sort();

  dates.forEach(dtStr => {
    const info = currentByDateMap[dtStr];
    const d = new Date(dtStr);
    const dayNum = d.getDate();
    const monthStr = d.toLocaleDateString("en-US", { month: "short" });

    const card = document.createElement("div");
    card.className = "heatmap-day-card";

    let borderStyle = "";
    let countText = "";

    if (info.is_sunday) {
      countText = `<span style="color:var(--text-muted);">Sunday</span>`;
    } else if (info.is_holiday) {
      countText = `<span style="color:var(--warning-color);">Holiday</span>`;
    } else {
      const cnt = info.classes.length;
      countText = `<span class="day-classes-count">${cnt} ${cnt === 1 ? 'class' : 'classes'}</span>`;
    }

    card.innerHTML = `
      <div class="day-date">${monthStr} ${dayNum}</div>
      <div class="day-name">${info.day}</div>
      ${countText}
    `;

    card.addEventListener("click", () => {
      openDateModal(dtStr, info);
    });

    grid.appendChild(card);
  });
};

function openDateModal(dtStr, info) {
  const modal = document.getElementById("date-classes-modal");
  const title = document.getElementById("modal-date-title");
  const body = document.getElementById("modal-date-body");

  title.innerHTML = `<i class="fa-solid fa-calendar-day"></i> Timetable for ${dtStr} (${info.day})`;
  body.innerHTML = "";

  if (info.is_sunday) {
    body.innerHTML = "<p style='color:var(--text-muted);'>Sunday — No scheduled classes.</p>";
  } else if (info.is_holiday) {
    body.innerHTML = "<p style='color:var(--warning-color);'>College Holiday — No classes conducted.</p>";
  } else if (!info.classes || info.classes.length === 0) {
    body.innerHTML = "<p style='color:var(--text-muted);'>No classes scheduled on this date.</p>";
  } else {
    let listHtml = "<ul style='list-style:none; padding:0; display:flex; flex-direction:column; gap:0.5rem;'>";
    info.classes.forEach(c => {
      listHtml += `
        <li style="background:rgba(255,255,255,0.05); padding:0.6rem 0.8rem; border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong>${c.subject_code}</strong>
            <span style="font-size:0.8rem; color:var(--text-muted); display:block;">Period ${c.period}</span>
          </div>
          <span style="font-size:0.85rem; color:var(--accent); font-weight:600;">${c.time}</span>
        </li>
      `;
    });
    listHtml += "</ul>";
    body.innerHTML = listHtml;
  }

  modal.style.display = "flex";
}

function closeDateModal() {
  document.getElementById("date-classes-modal").style.display = "none";
}

// 2. SMART LEAVE PLANNER HANDLER
document.addEventListener("DOMContentLoaded", () => {
  const btnLeaveSim = document.getElementById("btn-run-leave-sim");
  if (btnLeaveSim) {
    btnLeaveSim.addEventListener("click", async () => {
      const sDate = document.getElementById("inp-leave-start").value;
      const eDate = document.getElementById("inp-leave-end").value;
      const lType = document.getElementById("inp-leave-type").value;
      const cfg = JSON.parse(localStorage.getItem("smart_attendance_config") || "{}");

      const payload = {
        section_id: cfg.section_id || "section_A",
        start_date: sDate,
        end_date: eDate,
        leave_type: lType,
        subjects: cfg.subjects || [],
        plan_end_date: cfg.target_date || "2026-11-29"
      };

      try {
        const res = await fetch("/api/simulate-leave", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderLeaveResults(data);
      } catch (err) {
        console.error("Error simulating leave:", err);
      }
    });
  }
});

function renderLeaveResults(data) {
  const container = document.getElementById("leave-sim-results");
  container.style.display = "block";

  let warningBox = "";
  if (data.has_warnings) {
    warningBox = `
      <div style="background:var(--danger-bg); border:1px solid var(--danger-color); padding:0.8rem 1rem; border-radius:8px; margin-bottom:1rem;">
        <strong style="color:var(--danger-color);">⚠️ Leave Warning!</strong>
        <p style="font-size:0.85rem; color:#fecdd3; margin-top:0.2rem;">This leave will drop one or more subjects into the Danger zone (< 75%).</p>
      </div>
    `;
  } else {
    warningBox = `
      <div style="background:var(--safe-bg); border:1px solid var(--safe-color); padding:0.8rem 1rem; border-radius:8px; margin-bottom:1rem;">
        <strong style="color:var(--safe-color);">✅ Leave Approved Safe</strong>
        <p style="font-size:0.85rem; color:#a7f3d0; margin-top:0.2rem;">All subjects remain above the 75% safety target after this leave.</p>
      </div>
    `;
  }

  let tableRows = "";
  data.simulated_subjects.forEach(s => {
    tableRows += `
      <tr>
        <td><strong>${s.name}</strong> (${s.short_name})</td>
        <td>${s.affected_classes_count} classes</td>
        <td><strong>${s.current_pct}%</strong></td>
        <td><span class="status-indicator-badge ${s.status_code}">${s.status_icon} ${s.status_label}</span></td>
      </tr>
    `;
  });

  container.innerHTML = `
    ${warningBox}
    <div class="sim-summary-bar">
      <div>
        <span>Leave Type: <strong>${data.leave_type}</strong></span> |
        <span>Dates: <strong>${data.start_date}</strong> to <strong>${data.end_date}</strong></span>
      </div>
      <div>
        <span>Affected Classes: <strong>${data.total_affected_classes}</strong></span> |
        <span>New Overall Attendance: <strong>${data.overall.overall_current_pct}%</strong> (${data.overall.pct_change > 0 ? '+' : ''}${data.overall.pct_change}%)</span>
      </div>
    </div>
    <table class="sim-subjects-table">
      <thead>
        <tr>
          <th>Subject</th>
          <th>Leave Misses</th>
          <th>New Projected %</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${tableRows}
      </tbody>
    </table>
  `;
}

// 3. WHAT-IF SIMULATOR HANDLER
async function runWhatIf(scenarioType, params = {}) {
  const cfg = JSON.parse(localStorage.getItem("smart_attendance_config") || "{}");
  const payload = {
    scenario_type: scenarioType,
    params: params,
    section_id: cfg.section_id || "section_A",
    subjects: cfg.subjects || [],
    plan_end_date: cfg.target_date || "2026-11-29"
  };

  try {
    const res = await fetch("/api/simulate-what-if", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    renderWhatIfResults(data);
  } catch (err) {
    console.error("Error in what-if simulation:", err);
  }
}

function openMissClassesModal() {
  const cfg = JSON.parse(localStorage.getItem("smart_attendance_config") || "{}");
  const subs = cfg.subjects || [];
  if (subs.length === 0) return;

  const subCode = prompt(`Enter subject code to miss classes (Available: ${subs.map(s => s.code).join(", ")}):`, subs[0].code);
  if (!subCode) return;
  const count = prompt("Enter number of classes you plan to miss:", "2");
  if (!count) return;

  runWhatIf("miss_n_classes", { subject_code: subCode, miss_count: parseInt(count) });
}

function renderWhatIfResults(data) {
  const container = document.getElementById("whatif-sim-results");
  container.style.display = "block";

  let tableRows = "";
  data.simulated_subjects.forEach(s => {
    tableRows += `
      <tr>
        <td><strong>${s.name}</strong> (${s.short_name})</td>
        <td><strong>${s.current_pct}%</strong></td>
        <td>${s.can_miss_75} classes</td>
        <td><span class="status-indicator-badge ${s.status_code}">${s.status_icon} ${s.status_label}</span></td>
      </tr>
    `;
  });

  container.innerHTML = `
    <div class="sim-summary-bar">
      <div>
        <span>Scenario: <strong>${data.scenario_type.toUpperCase().replace(/_/g, ' ')}</strong></span>
      </div>
      <div>
        <span>Resulting Overall Attendance: <strong>${data.overall.overall_current_pct}%</strong></span> |
        <span>At Risk Count: <strong>${data.overall.at_risk_count}</strong></span>
      </div>
    </div>
    <table class="sim-subjects-table">
      <thead>
        <tr>
          <th>Subject</th>
          <th>Projected %</th>
          <th>Safe Misses Left</th>
          <th>Resulting Status</th>
        </tr>
      </thead>
      <tbody>
        ${tableRows}
      </tbody>
    </table>
  `;
}

// 4. DIGITAL TWIN HANDLER
window.renderDigitalTwin = async function(cfg) {
  const grid = document.getElementById("digital-twin-grid");
  if (!grid) return;

  try {
    const res = await fetch("/api/digital-twin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        section_id: cfg.section_id || "section_A",
        subjects: cfg.subjects || [],
        today_str: cfg.start_date || "2026-09-28",
        plan_end_date: cfg.target_date || "2026-11-29"
      })
    });
    const data = await res.json();

    grid.innerHTML = "";
    Object.keys(data).forEach(key => {
      const item = data[key];
      grid.innerHTML += `
        <div class="twin-card">
          <h4>${item.title}</h4>
          <div class="twin-pct">${item.overall_pct}%</div>
          <div class="twin-sub">Max Possible: ${item.max_pct}%</div>
          <div class="twin-sub" style="margin-top:0.4rem;">Subjects at Risk: <strong style="color:${item.at_risk_count > 0 ? 'var(--danger-color)' : 'var(--safe-color)'}">${item.at_risk_count}</strong></div>
        </div>
      `;
    });
  } catch (err) {
    console.error("Error loading digital twin:", err);
  }
};

// 5. RECOVERY PATH RENDERER
window.renderRecoveryPath = function(subjects) {
  const grid = document.getElementById("recovery-path-grid");
  if (!grid) return;

  grid.innerHTML = "";

  subjects.forEach(sub => {
    const path = sub.recovery_path;
    const streak = sub.recovery_streak;

    let stepsHtml = "";
    path.milestones.forEach(m => {
      if (m.reached) {
        stepsHtml += `<div class="milestone-item reached"><span>Target ${m.target_pct}%</span> <span>✅ Achieved (${sub.current_pct}%)</span></div>`;
      } else if (m.achievable) {
        stepsHtml += `<div class="milestone-item"><span>Target ${m.target_pct}%</span> <span>Attend next <strong>${m.required_classes} classes</strong></span></div>`;
      } else {
        stepsHtml += `<div class="milestone-item impossible"><span>Target ${m.target_pct}%</span> <span>❌ Unachievable</span></div>`;
      }
    });

    const card = document.createElement("div");
    card.className = "recovery-card";
    card.innerHTML = `
      <h4>${sub.name} (${sub.short_name})</h4>
      <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.75rem;">
        Recovery Streak: <strong>${streak.attended} / ${streak.required}</strong> required classes
      </div>
      <div class="sub-progress-track" style="margin-bottom:1rem;">
        <div class="sub-progress-fill SAFE" style="width:${streak.progress_pct}%;"></div>
      </div>
      <div class="milestones-steps">
        ${stepsHtml}
      </div>
    `;
    grid.appendChild(card);
  });
};
