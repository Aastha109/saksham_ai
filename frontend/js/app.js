/**
 * Saksham_AI Main Client Application Logic
 * Debounced typing, real-time coaching HUD, diff rendering, and BI data layer.
 */

// Global Application State
const state = {
  currentModel: 'gpt-4o',
  debounceTimer: null,
  lastAnalysis: null,
  activeTab: 'studio',
  modelsCatalog: {}
};

// DOM Elements
const elements = {
  promptInput: document.getElementById('promptInput'),
  modelSelect: document.getElementById('modelSelect'),
  sampleSelect: document.getElementById('sampleSelect'),
  wordCountBadge: document.getElementById('wordCountBadge'),
  charCountBadge: document.getElementById('charCountBadge'),
  tokenCountPill: document.getElementById('tokenCountPill'),
  tokenizerPill: document.getElementById('tokenizerPill'),
  latencyBadge: document.getElementById('latencyBadge'),
  
  // HUD Elements
  gaugeCircle: document.getElementById('gaugeCircle'),
  gaugeScoreText: document.getElementById('gaugeScoreText'),
  efficiencyBadge: document.getElementById('efficiencyBadge'),
  followUpRiskText: document.getElementById('followUpRiskText'),
  issuesContainer: document.getElementById('issuesContainer'),
  positivesContainer: document.getElementById('positivesContainer'),
  
  // Cost Box
  singleCostVal: document.getElementById('singleCostVal'),
  scale10kCostVal: document.getElementById('scale10kCostVal'),
  costRangeSub: document.getElementById('costRangeSub'),
  
  // Eco Box
  ecoEnergyVal: document.getElementById('ecoEnergyVal'),
  ecoCarbonVal: document.getElementById('ecoCarbonVal'),
  ecoEquivVal: document.getElementById('ecoEquivVal'),
  
  // Model Rec Card
  recComplexityBadge: document.getElementById('recComplexityBadge'),
  recModelTitle: document.getElementById('recModelTitle'),
  recSavingsHighlight: document.getElementById('recSavingsHighlight'),
  recGuidanceText: document.getElementById('recGuidanceText'),
  applyModelBtn: document.getElementById('applyModelBtn'),
  
  // Rewrite Card
  rewriteCard: document.getElementById('rewriteCard'),
  rewriteSavingsTag: document.getElementById('rewriteSavingsTag'),
  rewriteDiffContainer: document.getElementById('rewriteDiffContainer'),
  rewriteRationaleText: document.getElementById('rewriteRationaleText'),
  applyRewriteBtn: document.getElementById('applyRewriteBtn'),
  
  // Buttons
  logPromptBtn: document.getElementById('logPromptBtn'),
  clearPromptBtn: document.getElementById('clearPromptBtn'),
  toastContainer: document.getElementById('toastContainer')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupEventListeners();
  loadModelsCatalog();
  loadSamplePrompts();
  
  // Load default sample to immediately showcase value
  loadPromptSample('customer_support_bloated');
});

// Setup Tab Navigation
function setupTabs() {
  const tabButtons = document.querySelectorAll('.nav-tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  
  document.querySelectorAll('.nav-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });

  document.querySelectorAll('.tab-content-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === `tab-${tabId}`);
  });

  if (tabId === 'analytics') {
    loadAnalyticsDashboard();
  } else if (tabId === 'pricing') {
    renderPricingMatrix();
  }
}

// Setup Event Listeners
function setupEventListeners() {
  // Debounced typing handler (~350ms)
  elements.promptInput.addEventListener('input', () => {
    updateWordAndCharCount();
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(() => {
      triggerAnalysis();
    }, 320);
  });

  elements.modelSelect.addEventListener('change', (e) => {
    state.currentModel = e.target.value;
    triggerAnalysis();
  });

  elements.sampleSelect.addEventListener('change', (e) => {
    const key = e.target.value;
    if (key) {
      loadPromptSample(key);
    }
  });

  elements.clearPromptBtn.addEventListener('click', () => {
    elements.promptInput.value = '';
    updateWordAndCharCount();
    triggerAnalysis();
    showToast('Prompt cleared');
  });

  elements.applyRewriteBtn.addEventListener('click', () => {
    if (state.lastAnalysis && state.lastAnalysis.rewrite && state.lastAnalysis.rewrite.rewritten_prompt) {
      elements.promptInput.value = state.lastAnalysis.rewrite.rewritten_prompt;
      updateWordAndCharCount();
      triggerAnalysis();
      showToast('✨ Tightened rewrite applied successfully!');
    }
  });

  elements.applyModelBtn.addEventListener('click', () => {
    if (state.lastAnalysis && state.lastAnalysis.recommendation) {
      const rec = state.lastAnalysis.recommendation.recommended_model;
      elements.modelSelect.value = rec;
      state.currentModel = rec;
      triggerAnalysis();
      showToast(`⚡ Model switched to ${rec}`);
    }
  });

  elements.logPromptBtn.addEventListener('click', () => {
    logPromptToDatabase();
  });

  // Table filter search
  const tableSearch = document.getElementById('tableSearchInput');
  if (tableSearch) {
    tableSearch.addEventListener('input', (e) => {
      filterAuditLogsTable(e.target.value);
    });
  }

  // Team filter dropdown
  const teamFilterSelect = document.getElementById('teamFilterSelect');
  if (teamFilterSelect) {
    teamFilterSelect.addEventListener('change', (e) => {
      fetchAuditLogs(e.target.value);
    });
  }

  // CSV export button
  const exportCsvBtn = document.getElementById('exportCsvBtn');
  if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', () => {
      window.location.href = '/api/analytics/export';
      showToast('📥 Exporting prompt usage logs to CSV for Power BI...');
    });
  }
}

// Load Models from API
async function loadModelsCatalog() {
  try {
    const res = await fetch('/api/models');
    const data = await res.json();
    state.modelsCatalog = data.models || {};
    populateModelDropdown();
  } catch (err) {
    console.error('Failed to load models catalog:', err);
  }
}

function populateModelDropdown() {
  const select = elements.modelSelect;
  select.innerHTML = '';
  Object.keys(state.modelsCatalog).forEach(key => {
    const m = state.modelsCatalog[key];
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = `${m.name} (${m.provider}) - $${m.input_per_m}/M in`;
    if (key === state.currentModel) opt.selected = true;
    select.appendChild(opt);
  });
}

function loadSamplePrompts() {
  const select = elements.sampleSelect;
  if (!window.PROMPT_SAMPLES) return;
  Object.keys(window.PROMPT_SAMPLES).forEach(key => {
    const item = window.PROMPT_SAMPLES[key];
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = item.title;
    select.appendChild(opt);
  });
}

function loadPromptSample(key) {
  const item = window.PROMPT_SAMPLES[key];
  if (!item) return;
  elements.promptInput.value = item.prompt;
  if (item.model) {
    elements.modelSelect.value = item.model;
    state.currentModel = item.model;
  }
  updateWordAndCharCount();
  triggerAnalysis();
}

function updateWordAndCharCount() {
  const text = elements.promptInput.value || '';
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  elements.wordCountBadge.textContent = `${words} words`;
  elements.charCountBadge.textContent = `${text.length} chars`;
}

// Main Coaching Analysis Trigger
async function triggerAnalysis() {
  const promptText = elements.promptInput.value || '';
  const startTime = performance.now();

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: promptText,
        model: state.currentModel,
        team: 'Core Engineering',
        user_id: 'current_developer'
      })
    });

    const elapsed = Math.round(performance.now() - startTime);
    if (elements.latencyBadge) {
      elements.latencyBadge.textContent = `⚡ ${elapsed}ms`;
    }

    if (!res.ok) throw new Error('Analysis API error');
    const data = await res.json();
    state.lastAnalysis = data;
    renderAnalysisData(data);
  } catch (err) {
    console.error('Analysis failed:', err);
  }
}

// Render Analysis HUD
function renderAnalysisData(data) {
  const { tokens, cost, efficiency, recommendation, environmental_impact, rewrite } = data;

  // 1. Token HUD
  elements.tokenCountPill.textContent = `${tokens.token_count} tokens`;
  elements.tokenizerPill.textContent = tokens.tokenizer_used;

  // 2. Efficiency Radial Gauge
  const score = efficiency.score;
  const strokeOffset = 283 - (283 * score / 100);
  elements.gaugeCircle.style.strokeDashoffset = strokeOffset;
  elements.gaugeScoreText.textContent = score;

  // Color mapping
  let strokeColor = '#10b981'; // emerald
  let badgeClass = 'badge-emerald';
  if (score < 50) {
    strokeColor = '#f43f5e';
    badgeClass = 'badge-rose';
  } else if (score < 70) {
    strokeColor = '#f59e0b';
    badgeClass = 'badge-amber';
  } else if (score < 85) {
    strokeColor = '#06b6d4';
    badgeClass = 'badge-cyan';
  }
  elements.gaugeCircle.style.stroke = strokeColor;
  elements.efficiencyBadge.className = `efficiency-rating-badge ${badgeClass}`;
  elements.efficiencyBadge.textContent = efficiency.rating;
  elements.followUpRiskText.textContent = `Follow-up Risk: ${efficiency.follow_up_risk}`;

  // Diagnostics & Positives
  renderIssuesList(efficiency.issues, efficiency.positives);

  // 3. Cost Meter
  elements.singleCostVal.textContent = `$${cost.total_cost_estimate_usd.toFixed(5)}`;
  elements.scale10kCostVal.textContent = `$${cost.scale_projections.cost_10k_requests_usd.toFixed(2)}`;
  elements.costRangeSub.textContent = `Range: $${cost.cost_range.min_usd.toFixed(5)} - $${cost.cost_range.max_usd.toFixed(5)}`;

  // 4. Environmental Impact
  elements.ecoEnergyVal.textContent = `${environmental_impact.energy_consumption_wh.estimate} Wh`;
  elements.ecoCarbonVal.textContent = `${environmental_impact.carbon_footprint_g.estimate} g`;
  elements.ecoEquivVal.textContent = `${environmental_impact.equivalents.led_bulb_seconds}s LED`;

  // 5. Model Recommendation
  renderModelRecommendation(recommendation);

  // 6. Rewrite & Diff View
  renderRewriteView(rewrite);
}

function renderIssuesList(issues, positives) {
  elements.issuesContainer.innerHTML = '';
  elements.positivesContainer.innerHTML = '';

  if (issues.length === 0) {
    elements.issuesContainer.innerHTML = `
      <div class="positive-pill-item">
        <span>✨</span>
        <span>No major token waste or vagueness flags detected.</span>
      </div>
    `;
  } else {
    issues.forEach(iss => {
      const item = document.createElement('div');
      item.className = `issue-pill-item ${iss.severity === 'medium' ? 'issue-med' : ''}`;
      item.innerHTML = `
        <span>⚠️</span>
        <div>
          <strong>${iss.title}</strong>: ${iss.description}
          <div style="font-size:0.75rem; color:#fca5a5; margin-top:2px;">Fix: ${iss.suggestion}</div>
        </div>
      `;
      elements.issuesContainer.appendChild(item);
    });
  }

  if (positives && positives.length > 0) {
    positives.forEach(pos => {
      const item = document.createElement('div');
      item.className = 'positive-pill-item';
      item.innerHTML = `
        <span>✅</span>
        <div><strong>${pos.title}</strong>: ${pos.description}</div>
      `;
      elements.positivesContainer.appendChild(item);
    });
  }
}

function renderModelRecommendation(rec) {
  elements.recComplexityBadge.textContent = `${rec.task_complexity} Task`;
  
  if (rec.is_downgrade_recommended) {
    elements.recModelTitle.innerHTML = `Switch to <span style="color:#38bdf8">${rec.recommended_model_name}</span>`;
    elements.recSavingsHighlight.textContent = `Save ${rec.pct_cost_saved}% ($${rec.savings_10k_requests_usd}/10k calls)`;
    elements.applyModelBtn.style.display = 'inline-flex';
    elements.applyModelBtn.textContent = `Switch to ${rec.recommended_model}`;
  } else {
    elements.recModelTitle.innerHTML = `Current model <span style="color:#a78bfa">${rec.current_model_name}</span> is well suited`;
    elements.recSavingsHighlight.textContent = `Optimal Tier`;
    elements.applyModelBtn.style.display = 'none';
  }

  elements.recGuidanceText.textContent = rec.guidance;
}

function renderRewriteView(rewrite) {
  if (!rewrite || !rewrite.diff_stream || rewrite.diff_stream.length === 0 || rewrite.tokens_saved === 0) {
    elements.rewriteCard.style.display = 'none';
    return;
  }

  elements.rewriteCard.style.display = 'block';
  elements.rewriteSavingsTag.textContent = `-${rewrite.tokens_saved} tokens (-${rewrite.pct_token_reduction}%) • Saves $${rewrite.savings_10k_requests_usd}/10k`;

  // Render Diff Chips
  elements.rewriteDiffContainer.innerHTML = '';
  rewrite.diff_stream.forEach(chunk => {
    const span = document.createElement('span');
    if (chunk.type === 'removed') {
      span.className = 'diff-tag-removed';
      span.textContent = chunk.text;
    } else if (chunk.type === 'added') {
      span.className = 'diff-tag-added';
      span.textContent = chunk.text;
    } else {
      span.className = 'diff-tag-equal';
      span.textContent = chunk.text;
    }
    elements.rewriteDiffContainer.appendChild(span);
  });

  elements.rewriteRationaleText.textContent = rewrite.breakeven_explanation;
}

// Log Prompt Simulation
async function logPromptToDatabase() {
  if (!state.lastAnalysis) {
    showToast('⚠️ Type or select a prompt first.');
    return;
  }

  const { tokens, cost, efficiency, recommendation, environmental_impact, rewrite } = state.lastAnalysis;
  const promptText = elements.promptInput.value;

  try {
    const res = await fetch('/api/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: promptText,
        rewritten_prompt: rewrite ? rewrite.rewritten_prompt : '',
        model_used: state.currentModel,
        recommended_model: recommendation.recommended_model,
        task_category: recommendation.task_complexity,
        input_tokens: tokens.token_count,
        output_tokens: cost.expected_output_tokens,
        cost_usd: cost.total_cost_estimate_usd,
        savings_usd: recommendation.cost_difference_usd || 0.0,
        efficiency_score: efficiency.score,
        carbon_g: environmental_impact.carbon_footprint_g.estimate,
        team: 'Core Engineering',
        user_id: 'dev_analyst'
      })
    });

    const result = await res.json();
    if (result.status === 'success') {
      showToast(`✅ Prompt logged to SQLite DB (Audit ID: #${result.log_id}). Real-time analytics updated!`);
    }
  } catch (err) {
    console.error('Failed to log prompt:', err);
    showToast('❌ Error logging prompt to SQL database.');
  }
}

// Load BI Dashboard Metrics & Charts
async function loadAnalyticsDashboard() {
  try {
    // 1. Fetch KPIs
    const kpiRes = await fetch('/api/analytics/kpis');
    const kpis = await kpiRes.json();
    renderKpiCards(kpis);

    // 2. Fetch Charts Data
    const chartsRes = await fetch('/api/analytics/charts');
    const chartsData = await chartsRes.json();
    if (window.initCharts) {
      window.initCharts(chartsData.trends, chartsData.models, chartsData.teams);
    }

    // 3. Fetch Audit Logs Table
    fetchAuditLogs();
  } catch (err) {
    console.error('Failed to load analytics dashboard:', err);
  }
}

function renderKpiCards(kpis) {
  document.getElementById('kpiTotalPrompts').textContent = kpis.total_prompts.toLocaleString();
  document.getElementById('kpiTotalSpend').textContent = `$${kpis.total_cost_usd.toFixed(3)}`;
  document.getElementById('kpiTotalSavings').textContent = `$${kpis.total_savings_usd.toFixed(3)}`;
  document.getElementById('kpiAvgEfficiency').textContent = `${kpis.avg_efficiency_score}/100`;
  document.getElementById('kpiCarbonAvoided').textContent = `${kpis.co2e_avoided_kg} kg`;
}

async function fetchAuditLogs(teamFilter = 'all') {
  try {
    const url = teamFilter && teamFilter !== 'all' 
      ? `/api/analytics/logs?team=${encodeURIComponent(teamFilter)}&limit=60`
      : '/api/analytics/logs?limit=60';
    const res = await fetch(url);
    const data = await res.json();
    renderAuditLogsTable(data.logs || []);
  } catch (err) {
    console.error('Failed to fetch audit logs:', err);
  }
}

function renderAuditLogsTable(logs) {
  const tbody = document.getElementById('auditLogsTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:2rem; color:#64748b;">No logs recorded yet.</td></tr>`;
    return;
  }

  logs.forEach(row => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="prompt-hash-code">#${row.prompt_hash}</span></td>
      <td style="max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${row.prompt_preview}">
        ${row.prompt_preview}
      </td>
      <td><strong>${row.model_used}</strong></td>
      <td><span style="font-size:0.78rem; text-transform:uppercase; color:#94a3b8;">${row.task_category}</span></td>
      <td>${row.total_tokens}</td>
      <td style="color:#cbd5e1;">$${Number(row.cost_usd).toFixed(4)}</td>
      <td style="color:#34d399; font-weight:700;">+$${Number(row.savings_usd).toFixed(4)}</td>
      <td>
        <span class="efficiency-rating-badge ${row.efficiency_score >= 80 ? 'badge-emerald' : (row.efficiency_score >= 60 ? 'badge-amber' : 'badge-rose')}" style="font-size:0.74rem;">
          ${row.efficiency_score}
        </span>
      </td>
      <td style="font-size:0.75rem; color:#94a3b8;">${row.created_at.slice(0, 16)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function filterAuditLogsTable(query) {
  const filter = query.toLowerCase().trim();
  const rows = document.querySelectorAll('#auditLogsTableBody tr');
  rows.forEach(r => {
    const text = r.textContent.toLowerCase();
    r.style.display = text.includes(filter) ? '' : 'none';
  });
}

// Render Pricing Matrix Tab
function renderPricingMatrix() {
  const container = document.getElementById('pricingCardsGrid');
  if (!container || !state.modelsCatalog) return;

  const testTokens = parseInt(document.getElementById('pricingCalcInput').value) || 1000;
  container.innerHTML = '';

  Object.keys(state.modelsCatalog).forEach(key => {
    const m = state.modelsCatalog[key];
    const singleCost = (testTokens * m.input_per_m + 300 * m.output_per_m) / 1000000;
    const cost10k = singleCost * 10000;
    const cost1M = singleCost * 1000000;

    const card = document.createElement('div');
    card.className = `pricing-card-item ${key === state.currentModel ? 'featured' : ''}`;
    card.innerHTML = `
      <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
          <span class="tier-badge tier-${m.tier}">${m.tier}</span>
          <span style="font-size:0.75rem; color:#94a3b8;">${m.provider}</span>
        </div>
        <h4 style="font-size:1.15rem; font-weight:700; color:#fff; margin-bottom:0.35rem;">${m.name}</h4>
        <p style="font-size:0.78rem; color:#94a3b8; margin-bottom:1rem;">${m.description}</p>
        
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-bottom:1rem; font-size:0.8rem; background:rgba(0,0,0,0.3); padding:0.6rem; border-radius:6px;">
          <div><span style="color:#64748b;">Input / 1M:</span> <strong style="color:#fff;">$${m.input_per_m}</strong></div>
          <div><span style="color:#64748b;">Output / 1M:</span> <strong style="color:#fff;">$${m.output_per_m}</strong></div>
        </div>
      </div>
      
      <div style="border-top:1px solid rgba(255,255,255,0.06); padding-top:0.85rem;">
        <div style="font-size:0.72rem; color:#64748b; text-transform:uppercase;">Cost @ ${testTokens} input tokens:</div>
        <div style="font-size:1.35rem; font-weight:800; color:#fff; margin-bottom:0.25rem;">$${singleCost.toFixed(5)} <span style="font-size:0.75rem; font-weight:500; color:#94a3b8;">/ call</span></div>
        <div style="font-size:0.78rem; color:#34d399; font-weight:600;">$${cost10k.toFixed(2)} per 10,000 calls</div>
      </div>
    `;
    container.appendChild(card);
  });
}

// Global Toast System
function showToast(msg) {
  if (!elements.toastContainer) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>💬</span> <span>${msg}</span>`;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}
