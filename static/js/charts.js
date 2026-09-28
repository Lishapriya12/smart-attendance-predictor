// ==========================================================================
// CHART VISUALIZATIONS (CHART.JS ENGINE)
// ==========================================================================

let subjectBarChart = null;
let forecastLineChart = null;
let riskDonutChart = null;

window.renderDashboardCharts = function(data) {
  renderSubjectBarChart(data.subjects);
  renderForecastLineChart(data.forecast);
  renderRiskDonutChart(data.subjects);
};

function renderSubjectBarChart(subjects) {
  const ctx = document.getElementById("chart-subject-bar");
  if (!ctx) return;

  const labels = subjects.map(s => s.short_name);
  const currentData = subjects.map(s => s.current_pct);
  const maxData = subjects.map(s => s.max_possible_pct);

  const colors = subjects.map(s => {
    if (s.status_code === "SAFE") return "#10b981";
    if (s.status_code === "WARNING") return "#f59e0b";
    if (s.status_code === "DANGER") return "#ef4444";
    return "#f43f5e";
  });

  if (subjectBarChart) {
    subjectBarChart.destroy();
  }

  subjectBarChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Current Attendance %",
          data: currentData,
          backgroundColor: colors,
          borderRadius: 6,
          barPercentage: 0.6
        },
        {
          label: "Max Possible %",
          data: maxData,
          backgroundColor: "rgba(255, 255, 255, 0.15)",
          borderRadius: 6,
          barPercentage: 0.6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 40,
          max: 100,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", callback: (val) => val + "%" }
        },
        x: {
          grid: { display: false },
          ticks: { color: "#f8fafc" }
        }
      },
      plugins: {
        legend: { labels: { color: "#94a3b8" } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.raw}%`
          }
        }
      }
    }
  });
}

function renderForecastLineChart(forecastData) {
  const ctx = document.getElementById("chart-forecast-line");
  if (!ctx || !forecastData) return;

  const labels = forecastData.map(f => f.label);
  const perfectData = forecastData.map(f => f.perfect_pct);
  const avgData = forecastData.map(f => f.avg_pct);

  if (forecastLineChart) {
    forecastLineChart.destroy();
  }

  forecastLineChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "100% Attendance Path",
          data: perfectData,
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56, 189, 248, 0.1)",
          fill: true,
          tension: 0.3,
          pointRadius: 5
        },
        {
          label: "Current Trend Path",
          data: avgData,
          borderColor: "#6366f1",
          borderDash: [5, 5],
          tension: 0.3,
          pointRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 50,
          max: 100,
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", callback: (val) => val + "%" }
        },
        x: {
          grid: { display: false },
          ticks: { color: "#f8fafc" }
        }
      },
      plugins: {
        legend: { labels: { color: "#94a3b8" } }
      }
    }
  });
}

function renderRiskDonutChart(subjects) {
  const ctx = document.getElementById("chart-risk-donut");
  if (!ctx) return;

  let safe = 0, warning = 0, danger = 0, irrecoverable = 0;
  subjects.forEach(s => {
    if (s.status_code === "SAFE") safe++;
    else if (s.status_code === "WARNING") warning++;
    else if (s.status_code === "DANGER") danger++;
    else if (s.status_code === "IRRECOVERABLE") irrecoverable++;
  });

  if (riskDonutChart) {
    riskDonutChart.destroy();
  }

  riskDonutChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Safe", "Warning", "Danger", "Irrecoverable"],
      datasets: [{
        data: [safe, warning, danger, irrecoverable],
        backgroundColor: ["#10b981", "#f59e0b", "#ef4444", "#f43f5e"],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#94a3b8", boxWidth: 12 }
        }
      },
      cutout: "70%"
    }
  });
}
