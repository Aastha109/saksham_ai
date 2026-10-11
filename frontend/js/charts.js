/**
 * Saksham_AI Charts & BI Visualizations Module
 * Renders interactive business intelligence dashboards using Chart.js.
 */

let costTrendChartInstance = null;
let modelDistChartInstance = null;
let teamChartInstance = null;

function initCharts(trendData, modelData, teamData) {
  // Chart.js global dark theme defaults
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
  Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';

  renderCostTrendChart(trendData);
  renderModelDistributionChart(modelData);
  renderTeamChart(teamData);
}

function renderCostTrendChart(data) {
  const ctx = document.getElementById('trendChartCanvas');
  if (!ctx) return;

  if (costTrendChartInstance) {
    costTrendChartInstance.destroy();
  }

  const labels = data.map(d => d.log_date.slice(5)); // 'MM-DD'
  const spend = data.map(d => d.daily_spend);
  const savings = data.map(d => d.daily_savings);

  costTrendChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Realized / Estimated Spend ($)',
          data: spend,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99, 102, 241, 0.12)',
          borderWidth: 2,
          fill: true,
          tension: 0.35,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: 'Potential Savings Identified ($)',
          data: savings,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.08)',
          borderWidth: 2,
          borderDash: [5, 4],
          fill: true,
          tension: 0.35,
          pointRadius: 3,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            boxWidth: 12,
            font: { size: 12, weight: '600' }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleColor: '#fff',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(99, 102, 241, 0.4)',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: $${Number(context.raw).toFixed(4)}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: {
            callback: value => `$${value.toFixed(2)}`
          }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

function renderModelDistributionChart(data) {
  const ctx = document.getElementById('modelDistChartCanvas');
  if (!ctx) return;

  if (modelDistChartInstance) {
    modelDistChartInstance.destroy();
  }

  const labels = data.map(d => d.model_used);
  const costs = data.map(d => d.total_cost);

  const colors = [
    '#8b5cf6', // purple
    '#6366f1', // indigo
    '#06b6d4', // cyan
    '#10b981', // emerald
    '#f59e0b', // amber
    '#ec4899'  // pink
  ];

  modelDistChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [
        {
          data: costs,
          backgroundColor: colors.slice(0, labels.length),
          borderColor: '#0b0f19',
          borderWidth: 2,
          hoverOffset: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            boxWidth: 10,
            font: { size: 11, weight: '500' }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          callbacks: {
            label: function(context) {
              return ` ${context.label}: $${Number(context.raw).toFixed(3)}`;
            }
          }
        }
      },
      cutout: '68%'
    }
  });
}

function renderTeamChart(data) {
  const ctx = document.getElementById('teamChartCanvas');
  if (!ctx) return;

  if (teamChartInstance) {
    teamChartInstance.destroy();
  }

  const labels = data.map(d => d.team);
  const teamCosts = data.map(d => d.team_cost);
  const teamSavings = data.map(d => d.team_savings);

  teamChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Team Spend ($)',
          data: teamCosts,
          backgroundColor: 'rgba(99, 102, 241, 0.75)',
          borderRadius: 6
        },
        {
          label: 'Identified Savings ($)',
          data: teamSavings,
          backgroundColor: 'rgba(16, 185, 129, 0.75)',
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { boxWidth: 10, font: { size: 11 } }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { callback: v => `$${v.toFixed(2)}` }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

window.initCharts = initCharts;
