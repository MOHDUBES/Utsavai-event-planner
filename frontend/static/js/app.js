/**
 * UtsavAI – Main Application JavaScript
 *
 * Architecture:
 * - Pure vanilla JS, no dependencies
 * - Modular functions organized by feature
 * - localStorage for plan persistence
 * - Accessible: ARIA live regions, keyboard nav, focus management
 * - i18n: English + Hindi toggle
 * - XSS protection: all user data escaped before DOM insertion
 */

'use strict';

/* ══════════════════════════════════════════════════════════
   0. Utilities & Constants
   ══════════════════════════════════════════════════════════ */

const API_BASE = '/api/v1';
const STORAGE_KEY = 'utsavai_saved_plans';

/** Escape HTML to prevent XSS. All user data must pass through this. */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

/** Format number as Indian currency (₹ with lakh/crore notation) */
function formatINR(amount) {
  const num = Math.abs(Number(amount));
  if (num >= 10_000_000) return `₹${(num / 10_000_000).toFixed(1)}Cr`;
  if (num >= 100_000) return `₹${(num / 100_000).toFixed(1)}L`;
  if (num >= 1_000) return `₹${(num / 1_000).toFixed(1)}K`;
  return `₹${num.toLocaleString('en-IN')}`;
}

/** Format exact INR with commas */
function formatINRFull(amount) {
  return `₹${Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

/** Announce to screen readers via live region */
function announce(message, priority = 'polite') {
  const el = priority === 'assertive'
    ? document.getElementById('aria-assertive')
    : document.getElementById('aria-live');
  if (!el) return;
  el.textContent = '';
  requestAnimationFrame(() => { el.textContent = message; });
}

/** Simple element query helpers */
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

/* ══════════════════════════════════════════════════════════
   1. i18n (English / Hindi toggle)
   ══════════════════════════════════════════════════════════ */

let currentLang = 'en';

const translations = {
  en: {
    hero_subtitle: "AI-powered planning for weddings, birthdays, Diwali melas & more. Instant budget breakdown, vendor checklists, and personalized ideas — in INR.",
    form_title: "📋 Tell Us About Your Event",
    form_subtitle: "Fill in the details and we'll generate a complete plan in seconds.",
    label_event_type: "Event Type",
    label_date: "Event Date",
    label_city: "City",
    label_city_tier: "City Tier",
    label_guests: "Number of Guests",
    label_budget: "Total Budget (₹ INR)",
    label_theme: "Theme / Style (optional)",
    label_dietary: "Dietary Preference",
    label_venue_type: "Venue Type",
    label_religion: "Religion / Culture (optional)",
    label_customs: "Cultural Customs / Rituals (optional)",
    label_requirements: "Special Requirements (optional)",
    label_priorities: "What matters most to you?",
    btn_generate: "Generate My Plan",
  },
  hi: {
    hero_subtitle: "शादी, जन्मदिन, दिवाली मेले और अन्य उत्सवों के लिए AI-संचालित योजना। तुरंत बजट, वेंडर सूची और व्यक्तिगत विचार — भारतीय रुपये में।",
    form_title: "📋 अपने उत्सव के बारे में बताएं",
    form_subtitle: "विवरण भरें और हम कुछ ही सेकंड में पूरी योजना तैयार करेंगे।",
    label_event_type: "कार्यक्रम का प्रकार",
    label_date: "कार्यक्रम की तारीख",
    label_city: "शहर",
    label_city_tier: "शहर का स्तर",
    label_guests: "मेहमानों की संख्या",
    label_budget: "कुल बजट (₹ INR)",
    label_theme: "थीम / शैली (वैकल्पिक)",
    label_dietary: "आहार प्राथमिकता",
    label_venue_type: "स्थान का प्रकार",
    label_religion: "धर्म / संस्कृति (वैकल्पिक)",
    label_customs: "सांस्कृतिक रीति-रिवाज (वैकल्पिक)",
    label_requirements: "विशेष आवश्यकताएं (वैकल्पिक)",
    label_priorities: "आपकी प्राथमिकताएं क्या हैं?",
    btn_generate: "मेरी योजना बनाएं",
  },
};

function applyTranslations() {
  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (translations[currentLang][key]) {
      el.textContent = translations[currentLang][key];
    }
  });
}

/* ══════════════════════════════════════════════════════════
   2. Theme Toggle (Dark / Light)
   ══════════════════════════════════════════════════════════ */

function initTheme() {
  const savedTheme = localStorage.getItem('utsavai_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);
}

function updateThemeIcon(theme) {
  const icon = $('#theme-icon');
  const btn = $('#theme-toggle');
  if (!icon || !btn) return;
  icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
  btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
}

$('#theme-toggle')?.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('utsavai_theme', next);
  updateThemeIcon(next);
  announce(`Switched to ${next} mode`);
});

$('#lang-toggle')?.addEventListener('click', () => {
  currentLang = currentLang === 'en' ? 'hi' : 'en';
  const btn = $('#lang-toggle');
  btn.setAttribute('aria-pressed', currentLang === 'hi' ? 'true' : 'false');
  applyTranslations();
  announce(currentLang === 'hi' ? 'हिंदी में बदल दिया गया' : 'Switched to English');
});

/* ══════════════════════════════════════════════════════════
   3. Budget Display Formatting
   ══════════════════════════════════════════════════════════ */

const budgetInput = $('#total_budget_inr');
const budgetDisplay = $('#budget-display');

budgetInput?.addEventListener('input', () => {
  const val = parseFloat(budgetInput.value);
  if (!isNaN(val) && val > 0) {
    budgetDisplay.textContent = `= ${formatINR(val)} total`;
  } else {
    budgetDisplay.textContent = 'Enter your total budget';
  }
});

/* ══════════════════════════════════════════════════════════
   4. Multi-step Form
   ══════════════════════════════════════════════════════════ */

let currentStep = 1;

function goToStep(stepNum) {
  const prev = $(`#step-${currentStep}`);
  const next = $(`#step-${stepNum}`);
  if (!next) return;

  // Validate current step before advancing
  if (stepNum > currentStep && !validateStep(currentStep)) return;

  prev?.classList.remove('active');
  next.classList.add('active');
  currentStep = stepNum;

  // Update step indicators
  $$('.step').forEach(el => {
    const n = parseInt(el.dataset.step);
    el.classList.toggle('active', n === stepNum);
    el.classList.toggle('done', n < stepNum);
  });

  // Focus first input in new step
  const firstInput = next.querySelector('input, select, textarea, button');
  firstInput?.focus();

  announce(`Step ${stepNum} of 3: ${['', 'Basic Information', 'Event Details', 'Budget Priorities'][stepNum]}`);
}

function validateStep(stepNum) {
  const step = $(`#step-${stepNum}`);
  if (!step) return true;
  let valid = true;

  $$('[required]', step).forEach(input => {
    const errorEl = input.closest('.form-group')?.querySelector('.form-error');
    if (!input.value.trim()) {
      input.classList.add('error');
      if (errorEl) {
        errorEl.textContent = 'This field is required.';
        errorEl.classList.add('visible');
      }
      valid = false;
    } else {
      input.classList.remove('error');
      if (errorEl) {
        errorEl.textContent = '';
        errorEl.classList.remove('visible');
      }
    }
  });

  // Guest count validation
  if (stepNum === 1) {
    const guests = $('#guest_count');
    const budget = $('#total_budget_inr');
    if (guests && (parseInt(guests.value) < 1 || parseInt(guests.value) > 10000)) {
      markError(guests, 'Guest count must be between 1 and 10,000.');
      valid = false;
    }
    if (budget && (parseFloat(budget.value) < 1000)) {
      markError(budget, 'Minimum budget is ₹1,000.');
      valid = false;
    }
  }

  if (!valid) {
    announce('Please fix the errors before continuing.', 'assertive');
    // Focus first error
    step.querySelector('.form-input.error, .form-select.error')?.focus();
  }

  return valid;
}

function markError(input, message) {
  input.classList.add('error');
  const errorEl = input.closest('.form-group')?.querySelector('.form-error');
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.classList.add('visible');
  }
}

// Step navigation
$$('.next-step').forEach(btn => {
  btn.addEventListener('click', () => goToStep(parseInt(btn.dataset.next)));
});

$$('.prev-step').forEach(btn => {
  btn.addEventListener('click', () => goToStep(parseInt(btn.dataset.prev)));
});

/* ══════════════════════════════════════════════════════════
   5. Priority Chips
   ══════════════════════════════════════════════════════════ */

$$('.priority-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const pressed = chip.getAttribute('aria-pressed') === 'true';
    const currentlySelected = $$('.priority-chip[aria-pressed="true"]').length;

    if (pressed) {
      chip.setAttribute('aria-pressed', 'false');
    } else if (currentlySelected < 6) {
      chip.setAttribute('aria-pressed', 'true');
    } else {
      announce('You can select up to 6 priorities.', 'assertive');
    }
  });
});

function getSelectedPriorities() {
  return $$('.priority-chip[aria-pressed="true"]').map(c => c.dataset.value);
}

/* ══════════════════════════════════════════════════════════
   6. Loading Overlay
   ══════════════════════════════════════════════════════════ */

const loadingSteps = [
  'Calculating budget allocation…',
  'Planning vendor checklist…',
  'Building your timeline…',
  'Running sanity checks…',
  'Getting AI personalization…',
  'Finalizing your plan…',
];

let loadingInterval = null;

function showLoading() {
  const overlay = $('#loading-overlay');
  const bar = $('#loading-bar');
  const stepEl = $('#loading-step');
  if (!overlay) return;

  overlay.classList.remove('hidden');
  overlay.setAttribute('aria-busy', 'true');
  announce('Generating your event plan. Please wait…');

  let stepIdx = 0;
  let progress = 0;

  loadingInterval = setInterval(() => {
    stepIdx = (stepIdx + 1) % loadingSteps.length;
    if (stepEl) stepEl.textContent = loadingSteps[stepIdx];

    progress = Math.min(progress + 15, 90);
    if (bar) {
      bar.style.width = `${progress}%`;
      bar.parentElement.setAttribute('aria-valuenow', progress);
    }
  }, 700);
}

function hideLoading() {
  clearInterval(loadingInterval);
  const overlay = $('#loading-overlay');
  const bar = $('#loading-bar');
  if (!overlay) return;

  if (bar) {
    bar.style.width = '100%';
    bar.parentElement.setAttribute('aria-valuenow', 100);
  }

  setTimeout(() => {
    overlay.classList.add('hidden');
    overlay.removeAttribute('aria-busy');
  }, 400);
}

/* ══════════════════════════════════════════════════════════
   7. Demo Scenarios
   ══════════════════════════════════════════════════════════ */

$('#load-demo-btn')?.addEventListener('click', async () => {
  const panel = $('#demo-panel');
  const btn = $('#load-demo-btn');
  const isExpanded = btn.getAttribute('aria-expanded') === 'true';

  panel.classList.toggle('hidden', isExpanded);
  btn.setAttribute('aria-expanded', String(!isExpanded));

  if (!isExpanded && $('#demo-cards .loading-spinner')) {
    await loadDemoCards();
  }
});

async function loadDemoCards() {
  try {
    const res = await fetch(`${API_BASE}/demos`);
    if (!res.ok) throw new Error('Failed to load demos');
    const demos = await res.json();
    renderDemoCards(demos);
  } catch (e) {
    $('#demo-cards').innerHTML = `<p class="form-hint">Could not load demos. Please fill the form manually.</p>`;
  }
}

function renderDemoCards(demos) {
  const icons = ['💍', '🎂', '🪔'];
  $('#demo-cards').innerHTML = demos.map((demo, i) => `
    <div class="demo-card" role="listitem" tabindex="0"
      data-demo-id="${escapeHtml(demo.id)}"
      aria-label="Load demo: ${escapeHtml(demo.title)}"
    >
      <span class="demo-card-icon" aria-hidden="true">${icons[i] || '🎊'}</span>
      <div class="demo-card-title">${escapeHtml(demo.title)}</div>
      <div class="demo-card-desc">${escapeHtml(demo.description)}</div>
    </div>
  `).join('');

  $$('.demo-card').forEach((card, i) => {
    const handler = () => loadDemoPayload(demos[i].payload);
    card.addEventListener('click', handler);
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handler(); }
    });
  });
}

function loadDemoPayload(payload) {
  // Fill form fields
  const fieldMap = {
    event_type: '#event_type',
    event_date: '#event_date',
    city: '#city',
    city_tier: '#city_tier',
    guest_count: '#guest_count',
    total_budget_inr: '#total_budget_inr',
    theme: '#theme',
    dietary: '#dietary',
    venue_type: '#venue_type',
    religion_culture: '#religion_culture',
    cultural_customs: '#cultural_customs',
    special_requirements: '#special_requirements',
  };

  Object.entries(fieldMap).forEach(([key, sel]) => {
    const el = $(sel);
    if (el && payload[key] !== undefined) {
      el.value = payload[key];
      el.dispatchEvent(new Event('input'));
    }
  });

  // Set priorities
  const priorities = payload.priorities || [];
  $$('.priority-chip').forEach(chip => {
    const selected = priorities.includes(chip.dataset.value);
    chip.setAttribute('aria-pressed', String(selected));
  });

  // Hide demo panel
  $('#demo-panel').classList.add('hidden');
  $('#load-demo-btn').setAttribute('aria-expanded', 'false');

  // Scroll to form
  $('#planning-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
  announce(`Demo loaded: ${payload.event_type} event. Review and submit the form.`);
}

/* ══════════════════════════════════════════════════════════
   8. Form Submission & API Call
   ══════════════════════════════════════════════════════════ */

$('#start-planning-btn')?.addEventListener('click', () => {
  $('#planning-section').scrollIntoView({ behavior: 'smooth' });
  $('#event_type')?.focus();
});

let currentPlan = null;
let currentSessionId = null;

$('#event-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!validateStep(currentStep)) return;

  const formData = collectFormData();
  if (!formData) return;

  showLoading();

  try {
    const res = await fetch(`${API_BASE}/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(formData),
    });

    const data = await res.json();

    if (!res.ok) {
      const msg = data.detail || 'Failed to generate plan.';
      announce(msg, 'assertive');
      alert(`Error: ${msg}`);
      return;
    }

    currentPlan = data;
    currentSessionId = data.session_id;
    renderPlan(data);

  } catch (err) {
    console.error('Plan generation failed:', err);
    announce('Network error. Please check your connection and try again.', 'assertive');
    alert('Network error. Please try again.');
  } finally {
    hideLoading();
  }
});

function collectFormData() {
  const priorities = getSelectedPriorities();
  if (priorities.length === 0) {
    announce('Please select at least one priority area.', 'assertive');
    return null;
  }

  return {
    event_type: $('#event_type')?.value,
    event_date: $('#event_date')?.value,
    city: $('#city')?.value,
    city_tier: $('#city_tier')?.value || 'metro',
    guest_count: parseInt($('#guest_count')?.value || '0'),
    total_budget_inr: parseFloat($('#total_budget_inr')?.value || '0'),
    theme: $('#theme')?.value || '',
    dietary: $('#dietary')?.value || 'mixed',
    venue_type: $('#venue_type')?.value || 'indoor',
    religion_culture: $('#religion_culture')?.value || '',
    cultural_customs: $('#cultural_customs')?.value || '',
    special_requirements: $('#special_requirements')?.value || '',
    priorities: priorities,
  };
}

/* ══════════════════════════════════════════════════════════
   9. Plan Rendering
   ══════════════════════════════════════════════════════════ */

function renderPlan(plan) {
  const section = $('#results-section');
  section.classList.remove('hidden');
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // Plan header
  const req = plan.event_request;
  $('#plan-title').textContent = `${getEventEmoji(req.event_type)} ${titleCase(req.event_type.replace(/_/g, ' '))} Plan`;
  $('#plan-meta').innerHTML = `
    ${escapeHtml(req.city)} · ${escapeHtml(req.event_date)} · 
    ${escapeHtml(String(req.guest_count))} guests · 
    ${formatINR(req.total_budget_inr)} budget
  `;

  // Render each section
  renderSanityChecks(plan.sanity_checks);
  renderBudget(plan.budget);
  renderTimeline(plan.timeline);
  renderVendors(plan.vendor_checklist);
  renderAI(plan.ai_personalization);

  // Switch to budget tab
  switchTab('budget');

  announce('Your event plan is ready! Review the Budget, Timeline, Vendors, and AI Ideas tabs.');
}

function getEventEmoji(type) {
  const map = {
    wedding: '💍', birthday: '🎂', diwali_mela: '🪔',
    eid_celebration: '🌙', navratri: '💃', college_fest: '🎓',
    corporate: '🏢', anniversary: '💕', baby_shower: '👶',
    rwa_event: '🏘️', other: '🎉',
  };
  return map[type] || '🎊';
}

function titleCase(str) {
  return str.replace(/\b\w/g, c => c.toUpperCase());
}

function getCategorySvgIcon(category) {
  const cat = String(category || '').toLowerCase();
  let iconId = 'icon-venue';
  if (cat.includes('food') || cat.includes('cater') || cat.includes('biryani') || cat.includes('cake') || cat.includes('sweet') || cat.includes('fasting')) {
    iconId = 'icon-food';
  } else if (cat.includes('decor') || cat.includes('floral') || cat.includes('light') || cat.includes('balloon') || cat.includes('branding')) {
    iconId = 'icon-decor';
  } else if (cat.includes('photo') || cat.includes('video')) {
    iconId = 'icon-photography';
  } else if (cat.includes('music') || cat.includes('dj') || cat.includes('entertainment') || cat.includes('artist') || cat.includes('performer') || cat.includes('av') || cat.includes('equipment') || cat.includes('sound')) {
    iconId = 'icon-music';
  } else if (cat.includes('invitation') || cat.includes('stationery') || cat.includes('card') || cat.includes('promotion') || cat.includes('gift') || cat.includes('return')) {
    iconId = 'icon-invitation';
  } else if (cat.includes('transport') || cat.includes('vehicle') || cat.includes('logistic')) {
    iconId = 'icon-transport';
  } else if (cat.includes('pandit') || cat.includes('officiant') || cat.includes('puja') || cat.includes('religious') || cat.includes('ceremonial')) {
    iconId = 'icon-priest';
  } else if (cat.includes('makeup') || cat.includes('groom') || cat.includes('attire') || cat.includes('bridal')) {
    iconId = 'icon-makeup';
  } else if (cat.includes('permission') || cat.includes('noc') || cat.includes('security') || cat.includes('cleanup')) {
    iconId = 'icon-permissions';
  } else if (cat.includes('venue') || cat.includes('hall') || cat.includes('pandal') || cat.includes('ground') || cat.includes('lawn') || cat.includes('stage')) {
    iconId = 'icon-venue';
  }
  return `<svg class="category-svg-icon" width="20" height="20" aria-hidden="true" focusable="false"><use href="/assets/icons/sprite.svg#${iconId}" /></svg>`;
}

/* ── 9a. Sanity Checks ── */
function renderSanityChecks(checks) {
  const container = $('#sanity-alerts');
  const errors = checks.filter(c => c.status === 'error');
  const warnings = checks.filter(c => c.status === 'warning');
  const oks = checks.filter(c => c.status === 'ok');

  // Show errors and warnings only (not all oks to reduce noise)
  const toShow = [...errors, ...warnings, ...(oks.length > 0 ? [oks[0]] : [])];

  container.innerHTML = toShow.map(check => `
    <div class="sanity-alert ${escapeHtml(check.status)}" role="status">
      <span aria-hidden="true">${check.status === 'ok' ? '✅' : check.status === 'warning' ? '⚠️' : '❌'}</span>
      <div>
        <strong>${escapeHtml(check.check_name)}:</strong> ${escapeHtml(check.message)}
        ${check.suggestion ? `<br><em>💡 ${escapeHtml(check.suggestion)}</em>` : ''}
      </div>
    </div>
  `).join('');
}

/* ── 9b. Budget ── */
function renderBudget(budget) {
  const container = $('#budget-content');
  const maxAmount = Math.max(...budget.allocations.map(a => a.amount_inr));

  container.innerHTML = `
    <div class="budget-summary">
      <div class="stat-card">
        <span class="stat-icon" aria-hidden="true">💰</span>
        <span class="stat-value">${formatINR(budget.total_inr)}</span>
        <span class="stat-label">Total Budget</span>
      </div>
      <div class="stat-card">
        <span class="stat-icon" aria-hidden="true">👤</span>
        <span class="stat-value">${formatINR(budget.per_head_inr)}</span>
        <span class="stat-label">Per Head</span>
      </div>
      <div class="stat-card">
        <span class="stat-icon" aria-hidden="true">🛡️</span>
        <span class="stat-value">${formatINR(budget.contingency_inr)}</span>
        <span class="stat-label">Contingency (10%)</span>
      </div>
      <div class="stat-card">
        <span class="stat-icon" aria-hidden="true">🗓️</span>
        <span class="stat-value">${escapeHtml(budget.season)}</span>
        <span class="stat-label">Season</span>
      </div>
    </div>

    <div class="budget-chart">
      <h3 class="chart-title">Budget Allocation</h3>
      <div role="list" aria-label="Budget breakdown by category">
        ${budget.allocations.map(alloc => `
          <div class="budget-bar-item" role="listitem">
            <div class="bar-header">
              <span class="bar-category">${getCategorySvgIcon(alloc.category)}<span>${escapeHtml(alloc.category)}</span></span>
              <span class="bar-amount">${escapeHtml(alloc.percentage.toFixed(1))}% · ${formatINRFull(alloc.amount_inr)}</span>
            </div>
            <div class="bar-track" role="progressbar"
              aria-valuenow="${alloc.percentage.toFixed(0)}"
              aria-valuemin="0" aria-valuemax="100"
              aria-label="${escapeHtml(alloc.category)}: ${alloc.percentage.toFixed(1)}%">
              <div class="bar-fill" style="width: 0%" data-target="${(alloc.amount_inr / maxAmount * 100).toFixed(1)}%"></div>
            </div>
            ${alloc.notes ? `<div class="bar-notes">${escapeHtml(alloc.notes)}</div>` : ''}
          </div>
        `).join('')}
      </div>
    </div>

    ${budget.warnings.length > 0 || budget.suggestions.length > 0 ? `
      <div class="alert-list" role="list" aria-label="Budget warnings and suggestions">
        ${budget.warnings.map(w => `
          <div class="alert-item warning" role="listitem">${escapeHtml(w)}</div>
        `).join('')}
        ${budget.suggestions.map(s => `
          <div class="alert-item suggestion" role="listitem">${escapeHtml(s)}</div>
        `).join('')}
      </div>
    ` : ''}
  `;

  // Animate bars after DOM paint
  requestAnimationFrame(() => {
    setTimeout(() => {
      $$('.bar-fill').forEach(bar => {
        bar.style.width = bar.dataset.target;
      });
    }, 100);
  });
}

/* ── 9c. Timeline ── */
function renderTimeline(timeline) {
  const container = $('#timeline-content');
  const priorityColors = {
    critical: '#ef4444', high: '#f59e0b', medium: '#3b82f6', low: '#22c55e'
  };
  const priorityLabels = { critical: '🔴', high: '🟡', medium: '🔵', low: '🟢' };

  container.innerHTML = `
    <div class="timeline-meta" aria-label="Timeline summary">
      <span>📅 Event: <strong>${escapeHtml(String(timeline.event_date))}</strong></span>
      <span>⏳ Days remaining: <strong>${escapeHtml(String(timeline.days_until_event))}</strong></span>
      ${timeline.is_compressed ? '<span class="urgent-badge" role="alert">⚡ COMPRESSED TIMELINE</span>' : ''}
    </div>

    ${timeline.warnings.length > 0 ? `
      <div class="alert-list" role="list" aria-label="Timeline warnings">
        ${timeline.warnings.map(w => `
          <div class="alert-item warning" role="listitem">${escapeHtml(w)}</div>
        `).join('')}
      </div>
    ` : ''}

    <div class="timeline-list" role="list" aria-label="Event planning timeline">
      ${timeline.tasks.map((task, idx) => `
        <div class="timeline-item priority-${escapeHtml(task.priority)}" role="listitem">
          <div class="timeline-dot" aria-hidden="true" title="${escapeHtml(task.priority)} priority">
            ${escapeHtml(priorityLabels[task.priority] || '⚪')}
          </div>
          <div class="timeline-body">
            <div class="timeline-header">
              <span class="timeline-label">${escapeHtml(task.label)}</span>
              ${task.is_urgent ? '<span class="urgent-badge">⚡ URGENT</span>' : ''}
            </div>
            <div class="timeline-task">
              <input type="checkbox" id="task-${idx}" aria-label="${escapeHtml(task.task)}"
                ${task.status === 'done' ? 'checked' : ''}
                onchange="updateTaskStatus(this, ${idx})"
              />
              <label for="task-${idx}">${escapeHtml(task.task)}</label>
            </div>
            <div>
              <span class="timeline-category">${escapeHtml(task.category)}</span>
            </div>
            ${task.notes ? `<div class="timeline-notes">${escapeHtml(task.notes)}</div>` : ''}
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

window.updateTaskStatus = function(checkbox, idx) {
  if (currentPlan && currentPlan.timeline.tasks[idx]) {
    currentPlan.timeline.tasks[idx].status = checkbox.checked ? 'done' : 'pending';
    announce(`Task ${checkbox.checked ? 'completed' : 'marked pending'}: ${currentPlan.timeline.tasks[idx].task}`);
  }
};

/* ── 9d. Vendors ── */
function renderVendors(checklist) {
  const container = $('#vendors-content');

  container.innerHTML = `
    <div class="section-badge" aria-hidden="true">
      📋 ${escapeHtml(String(checklist.total_categories))} vendor categories
    </div>
    <div class="vendor-grid" role="list" aria-label="Vendor checklist">
      ${checklist.items.map((vendor, idx) => `
        <article class="vendor-card" role="listitem">
          <div class="vendor-card-header"
            tabindex="0"
            aria-expanded="true"
            aria-controls="vendor-body-${idx}"
            onclick="toggleVendorCard(this, ${idx})"
            onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();toggleVendorCard(this,${idx})}"
          >
            <div>
              <div class="vendor-title">
                ${getCategorySvgIcon(vendor.category)}
                <span>${escapeHtml(vendor.category)}</span>
                ${vendor.is_mandatory ? '<span class="vendor-mandatory" aria-label="Mandatory vendor">Required</span>' : ''}
              </div>
              <div class="vendor-cost">
                ${formatINR(vendor.estimated_cost_min_inr)} – ${formatINR(vendor.estimated_cost_max_inr)}
              </div>
            </div>
            <span aria-hidden="true" id="vendor-arrow-${idx}">▲</span>
          </div>
          <div class="vendor-body" id="vendor-body-${idx}">
            <div class="vendor-lead">📅 Book at least <strong>${escapeHtml(String(vendor.booking_lead_time_days))} days</strong> in advance</div>
            <p class="questions-title">Questions to ask</p>
            <ul class="questions-list" aria-label="Questions to ask this vendor">
              ${vendor.questions_to_ask.map(q => `<li>${escapeHtml(q)}</li>`).join('')}
            </ul>
            ${vendor.notes ? `<div class="vendor-notes">💡 ${escapeHtml(vendor.notes)}</div>` : ''}
          </div>
        </article>
      `).join('')}
    </div>
  `;
}

window.toggleVendorCard = function(header, idx) {
  const body = $(`#vendor-body-${idx}`);
  const arrow = $(`#vendor-arrow-${idx}`);
  const isExpanded = header.getAttribute('aria-expanded') === 'true';
  body.style.display = isExpanded ? 'none' : '';
  header.setAttribute('aria-expanded', String(!isExpanded));
  if (arrow) arrow.textContent = isExpanded ? '▼' : '▲';
};

/* ── 9e. AI Personalization ── */
function renderAI(ai) {
  const container = $('#ai-content');
  const badge = ai.is_ai_generated
    ? `✨ AI Generated (${escapeHtml(ai.provider_used)})`
    : '📝 Template-based (No API Key)';

  container.innerHTML = `
    <div class="ai-provider-badge" aria-label="Content source">
      <span aria-hidden="true">${ai.is_ai_generated ? '🤖' : '📝'}</span>
      ${badge}
      ${!ai.is_ai_generated ? '— <a href="/api/docs#/events/get_demos_api_v1_demos_get" style="color:var(--color-primary)">Add API key for AI suggestions</a>' : ''}
    </div>

    <div class="ai-grid">
      <div class="ai-card">
        <div class="ai-card-header">
          <span class="ai-card-icon" aria-hidden="true">🎨</span>
          <span class="ai-card-title">Theme Ideas</span>
        </div>
        <ul class="ai-list" aria-label="Theme ideas">
          ${ai.theme_ideas.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
        </ul>
      </div>

      <div class="ai-card">
        <div class="ai-card-header">
          <span class="ai-card-icon" aria-hidden="true">🍽️</span>
          <span class="ai-card-title">Menu Suggestions</span>
        </div>
        <ul class="ai-list" aria-label="Menu suggestions">
          ${ai.menu_suggestions.map(m => `<li>${escapeHtml(m)}</li>`).join('')}
        </ul>
      </div>

      <div class="ai-card">
        <div class="ai-card-header">
          <span class="ai-card-icon" aria-hidden="true">💐</span>
          <span class="ai-card-title">Decor Ideas</span>
        </div>
        <ul class="ai-list" aria-label="Decor ideas">
          ${ai.decor_ideas.map(d => `<li>${escapeHtml(d)}</li>`).join('')}
        </ul>
      </div>

      <div class="ai-card">
        <div class="ai-card-header">
          <span class="ai-card-icon" aria-hidden="true">🎮</span>
          <span class="ai-card-title">Games & Activities</span>
        </div>
        <ul class="ai-list" aria-label="Games and activities">
          ${ai.games_activities.map(g => `<li>${escapeHtml(g)}</li>`).join('')}
        </ul>
      </div>

      <div class="ai-card ai-card-full">
        <div class="ai-card-header">
          <span class="ai-card-icon" aria-hidden="true">💌</span>
          <span class="ai-card-title">Invitation Wording</span>
        </div>
        <div class="ai-prose" aria-label="Invitation text">${escapeHtml(ai.invitation_wording)}</div>
      </div>

      <div class="ai-card ai-card-full">
        <div class="ai-card-header">
          <span class="ai-card-icon" aria-hidden="true">🥂</span>
          <span class="ai-card-title">Speech / Toast</span>
        </div>
        <div class="ai-prose" aria-label="Speech or toast">${escapeHtml(ai.speech_toast)}</div>
      </div>
    </div>
  `;
}

/* ══════════════════════════════════════════════════════════
   10. Tab Navigation
   ══════════════════════════════════════════════════════════ */

$$('.tab').forEach(tab => {
  tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  tab.addEventListener('keydown', e => {
    const tabs = $$('.tab');
    const idx = tabs.indexOf(tab);
    if (e.key === 'ArrowRight') { e.preventDefault(); tabs[(idx + 1) % tabs.length]?.click(); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); tabs[(idx - 1 + tabs.length) % tabs.length]?.click(); }
  });
});

function switchTab(tabId) {
  $$('.tab').forEach(t => {
    const active = t.dataset.tab === tabId;
    t.classList.toggle('active', active);
    t.setAttribute('aria-selected', String(active));
    t.setAttribute('tabindex', active ? '0' : '-1');
  });

  $$('.tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });

  announce(`${titleCase(tabId)} tab selected`);
}

/* ══════════════════════════════════════════════════════════
   11. Chat Assistant
   ══════════════════════════════════════════════════════════ */

$('#chat-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const input = $('#chat-input');
  const message = input.value.trim();
  if (!message || !currentSessionId) {
    if (!currentSessionId) announce('Please generate a plan first before chatting.', 'assertive');
    return;
  }

  input.value = '';
  addChatMessage(message, 'user');
  showTypingIndicator();

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: message,
      }),
    });

    const data = await res.json();
    hideTypingIndicator();

    if (!res.ok) {
      addChatMessage('Sorry, I had trouble processing that. Please try again.', 'assistant');
      return;
    }

    // Format message with basic markdown-like formatting
    const reply = data.reply || 'I could not generate a response.';
    addChatMessage(reply, 'assistant');

    // If plan was updated, re-render
    if (data.is_plan_updated && data.updated_plan) {
      currentPlan = data.updated_plan;
      renderPlan(data.updated_plan);
      addChatMessage('✅ Your plan has been updated! Check the tabs above.', 'assistant');
    }

  } catch (err) {
    hideTypingIndicator();
    addChatMessage('Network error. Please check your connection.', 'assistant');
  }
});

function addChatMessage(text, role) {
  const container = $('#chat-messages');
  const avatar = role === 'assistant' ? '🤖' : '👤';

  // Simple markdown-like formatting
  const formatted = escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/- (.*?)(<br>|$)/g, '<li>$1</li>')
    .replace(/((?:<li>.*?<\/li>)+)/g, '<ul>$1</ul>');

  const msgEl = document.createElement('div');
  msgEl.className = `chat-message ${role}-message`;
  msgEl.innerHTML = `
    <div class="message-avatar" aria-hidden="true">${avatar}</div>
    <div class="message-content" aria-label="${role === 'assistant' ? 'Assistant' : 'You'}: ${escapeHtml(text.substring(0, 50))}">
      ${formatted}
    </div>
  `;

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
  announce(`${role === 'assistant' ? 'Assistant replied' : 'Message sent'}`);
}

let typingEl = null;
function showTypingIndicator() {
  typingEl = document.createElement('div');
  typingEl.className = 'chat-message assistant-message';
  typingEl.innerHTML = `
    <div class="message-avatar" aria-hidden="true">🤖</div>
    <div class="typing-indicator" aria-label="Assistant is typing">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  $('#chat-messages').appendChild(typingEl);
  $('#chat-messages').scrollTop = $('#chat-messages').scrollHeight;
}

function hideTypingIndicator() {
  typingEl?.remove();
  typingEl = null;
}

/* ══════════════════════════════════════════════════════════
   12. Export & Save
   ══════════════════════════════════════════════════════════ */

$('#export-md-btn')?.addEventListener('click', () => {
  if (!currentPlan) return;
  const md = generateMarkdown(currentPlan);
  downloadFile(md, 'utsavai-plan.md', 'text/markdown');
  announce('Plan exported as Markdown');
});

$('#export-json-btn')?.addEventListener('click', () => {
  if (!currentPlan) return;
  const json = JSON.stringify(currentPlan, null, 2);
  downloadFile(json, 'utsavai-plan.json', 'application/json');
  announce('Plan exported as JSON');
});

$('#print-btn')?.addEventListener('click', () => {
  window.print();
  announce('Opening print dialog');
});

$('#save-btn')?.addEventListener('click', () => {
  if (!currentPlan) return;
  try {
    const saves = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    const entry = { id: currentSessionId, savedAt: new Date().toISOString(), plan: currentPlan };
    saves.unshift(entry);
    if (saves.length > 5) saves.length = 5; // Keep last 5 plans
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saves));
    $('#save-btn').textContent = '✅ Saved!';
    setTimeout(() => { $('#save-btn').innerHTML = '<span aria-hidden="true">💾</span> Save'; }, 2000);
    announce('Plan saved to browser storage');
  } catch (e) {
    alert('Could not save plan. Browser storage may be full.');
  }
});

$('#new-plan-btn')?.addEventListener('click', () => {
  $('#results-section').classList.add('hidden');
  $('#planning-section').scrollIntoView({ behavior: 'smooth' });
  goToStep(1);
  currentPlan = null;
  currentSessionId = null;
  document.getElementById('event-form')?.reset();
  $$('.priority-chip').forEach(c => c.setAttribute('aria-pressed', ['food','venue','decor'].includes(c.dataset.value) ? 'true' : 'false'));
  announce('New plan form ready');
});

function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function generateMarkdown(plan) {
  const req = plan.event_request;
  const b = plan.budget;
  const t = plan.timeline;

  return `# ${titleCase(req.event_type.replace(/_/g, ' '))} Plan by UtsavAI
Generated: ${plan.generated_at}

## Event Details
- **Event:** ${req.event_type}
- **Date:** ${req.event_date}
- **City:** ${req.city} (${req.city_tier})
- **Guests:** ${req.guest_count}
- **Budget:** ₹${req.total_budget_inr.toLocaleString('en-IN')}
- **Theme:** ${req.theme || 'Not specified'}
- **Dietary:** ${req.dietary}

## Budget Breakdown
| Category | % | Amount (₹) |
|---|---|---|
${b.allocations.map(a => `| ${a.category} | ${a.percentage.toFixed(1)}% | ₹${a.amount_inr.toLocaleString('en-IN')} |`).join('\n')}
| **Contingency (10%)** | 10% | ₹${b.contingency_inr.toLocaleString('en-IN')} |
| **TOTAL** | 100% | ₹${b.total_inr.toLocaleString('en-IN')} |

**Per head cost:** ₹${b.per_head_inr.toLocaleString('en-IN')}

${b.warnings.length > 0 ? `### ⚠️ Warnings\n${b.warnings.map(w => `- ${w}`).join('\n')}` : ''}

## Timeline
${t.tasks.map(task => `- [ ] **[${task.label}]** ${task.task} *(${task.category})*${task.notes ? `\n  > ${task.notes}` : ''}`).join('\n')}

## Vendor Checklist
${plan.vendor_checklist.items.map(v => `### ${v.category}
- **Estimated cost:** ₹${v.estimated_cost_min_inr.toLocaleString('en-IN')} – ₹${v.estimated_cost_max_inr.toLocaleString('en-IN')}
- **Book:** ${v.booking_lead_time_days} days in advance
**Key questions:**
${v.questions_to_ask.map(q => `- ${q}`).join('\n')}`).join('\n\n')}

## AI Personalization
### Theme Ideas
${plan.ai_personalization.theme_ideas.map(t => `- ${t}`).join('\n')}

### Menu Suggestions
${plan.ai_personalization.menu_suggestions.map(m => `- ${m}`).join('\n')}

### Speech / Toast
${plan.ai_personalization.speech_toast}

---
*Generated by UtsavAI – India's Smart Event Planner*
`;
}

/* ══════════════════════════════════════════════════════════
   13. Initialization
   ══════════════════════════════════════════════════════════ */

function init() {
  initTheme();
  applyTranslations();

  // Set minimum date to today
  const dateInput = $('#event_date');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
    // Default to 3 months from now
    const defaultDate = new Date();
    defaultDate.setMonth(defaultDate.getMonth() + 3);
    dateInput.value = defaultDate.toISOString().split('T')[0];
  }

  // Load saved plan if available
  try {
    const saves = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    if (saves.length > 0) {
      // Could show "Resume last plan" button here
    }
  } catch (e) { /* ignore */ }

  console.log('UtsavAI initialized ✨');
}

init();
