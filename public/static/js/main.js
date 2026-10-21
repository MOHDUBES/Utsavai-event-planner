/**
 * @fileoverview Main orchestrator and entry point for UtsavAI ES modules.
 */

import { $, $$, escapeHtml, formatINR, announce, titleCase, getEventEmoji, extractErrorMessage } from './dom.js';
import { BUDGET_LIMITS, GUEST_LIMITS, MAX_PRIORITIES, LOADING_STEPS, STEP_NAMES } from './constants.js';
import { getCurrentPlan, setCurrentPlan, getCurrentStep, setCurrentStep } from './state.js';
import { initTheme, toggleTheme } from './theme.js';
import { applyTranslations, toggleLanguage } from './i18n.js';
import { fetchDemos, generatePlan } from './api.js';
import { renderBudget } from './render/budget.js';
import { renderTimeline } from './render/timeline.js';
import { renderVendors, renderSanityChecks } from './render/vendors.js';
import { renderAI } from './render/ideas.js';
import { initChat } from './chat.js';
import { initExport } from './export.js';

let loadingInterval = null;

/**
 * Switch form step wizard to specific step number (1-3).
 * @param {number} stepNum
 */
export function goToStep(stepNum) {
  const current = getCurrentStep();
  const prev = $(`#step-${current}`);
  const next = $(`#step-${stepNum}`);
  if (!next) return;

  if (stepNum > current && !validateStep(current)) return;

  prev?.classList.remove('active');
  next.classList.add('active');
  setCurrentStep(stepNum);

  $$('.step').forEach(el => {
    const n = parseInt(el.dataset.step, 10);
    el.classList.toggle('active', n === stepNum);
    el.classList.toggle('done', n < stepNum);
  });

  const firstInput = next.querySelector('input, select, textarea, button');
  firstInput?.focus();
  announce(`Step ${stepNum} of 3: ${STEP_NAMES[stepNum]}`);
}

/**
 * Validate inputs in the active wizard step.
 * @param {number} stepNum
 * @returns {boolean}
 */
export function validateStep(stepNum) {
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

  if (stepNum === 1) {
    valid = validateStepOneLimits() && valid;
  }

  if (!valid) {
    announce('Please fix the errors before continuing.', 'assertive');
    step.querySelector('.form-input.error, .form-select.error')?.focus();
  }
  return valid;
}

/**
 * Validate guest count and budget boundaries for Step 1.
 * @returns {boolean}
 */
function validateStepOneLimits() {
  const guests = $('#guest_count');
  const budget = $('#total_budget_inr');
  let ok = true;

  if (guests) {
    const gVal = parseInt(guests.value, 10);
    if (isNaN(gVal) || gVal < GUEST_LIMITS.MIN || gVal > GUEST_LIMITS.MAX) {
      markFieldError(guests, `Guest count must be between ${GUEST_LIMITS.MIN} and ${GUEST_LIMITS.MAX.toLocaleString('en-IN')}.`);
      ok = false;
    }
  }

  if (budget) {
    const bVal = parseFloat(budget.value);
    if (isNaN(bVal) || bVal < BUDGET_LIMITS.MIN) {
      markFieldError(budget, `Minimum budget is ₹${BUDGET_LIMITS.MIN.toLocaleString('en-IN')}.`);
      ok = false;
    } else if (bVal > BUDGET_LIMITS.MAX) {
      markFieldError(budget, `Maximum budget is ₹10 Crore (₹${BUDGET_LIMITS.MAX.toLocaleString('en-IN')}).`);
      ok = false;
    }
  }
  return ok;
}

/**
 * Mark input with error class and message text.
 * @param {HTMLElement} input
 * @param {string} message
 */
function markFieldError(input, message) {
  input.classList.add('error');
  const errorEl = input.closest('.form-group')?.querySelector('.form-error');
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.classList.add('visible');
  }
}

/**
 * Collect and serialize values from the intake form.
 * @returns {object|null}
 */
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
    guest_count: parseInt($('#guest_count')?.value || '0', 10),
    total_budget_inr: parseFloat($('#total_budget_inr')?.value || '0'),
    theme: $('#theme')?.value || '',
    dietary: $('#dietary')?.value || 'mixed',
    venue_type: $('#venue_type')?.value || 'indoor',
    religion_culture: $('#religion_culture')?.value || '',
    cultural_customs: $('#cultural_customs')?.value || '',
    special_requirements: $('#special_requirements')?.value || '',
    priorities,
  };
}

/**
 * Retrieve user selected priority chip values.
 * @returns {string[]}
 */
export function getSelectedPriorities() {
  return $$('.priority-chip[aria-pressed="true"]').map(c => c.dataset.value);
}

/**
 * Render the complete generated event plan across all tabs.
 * @param {object} plan
 */
export function renderPlan(plan) {
  setCurrentPlan(plan);
  const section = $('#results-section');
  if (!section) return;

  section.classList.remove('hidden');
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const req = plan.event_request;
  const titleEl = $('#plan-title');
  const metaEl = $('#plan-meta');
  if (titleEl) {
    titleEl.textContent = `${getEventEmoji(req.event_type)} ${titleCase(req.event_type.replace(/_/g, ' '))} Plan`;
  }
  if (metaEl) {
    metaEl.innerHTML = `${escapeHtml(req.city)} · ${escapeHtml(req.event_date)} · ${escapeHtml(String(req.guest_count))} guests · ${formatINR(req.total_budget_inr)} budget`;
  }

  renderSanityChecks(plan.sanity_checks);
  renderBudget(plan.budget);
  renderTimeline(plan.timeline);
  renderVendors(plan.vendor_checklist);
  renderAI(plan.ai_personalization);

  switchTab('budget');
  announce('Your event plan is ready! Review the Budget, Timeline, Vendors, and AI Ideas tabs.');
}

/**
 * Switch active results tab by ID.
 * @param {string} tabId
 */
export function switchTab(tabId) {
  $$('.tab').forEach(t => {
    const active = t.dataset.tab === tabId;
    t.classList.toggle('active', active);
    t.setAttribute('aria-selected', String(active));
    t.setAttribute('tabindex', active ? '0' : '-1');
    if (active) t.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  });

  $$('.tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });

  announce(`${titleCase(tabId)} tab selected`);
}

/**
 * Display full screen loading overlay with animated progress steps.
 */
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
    stepIdx = (stepIdx + 1) % LOADING_STEPS.length;
    if (stepEl) stepEl.textContent = LOADING_STEPS[stepIdx];
    progress = Math.min(progress + 15, 90);
    if (bar) {
      bar.style.width = `${progress}%`;
      bar.parentElement?.setAttribute('aria-valuenow', progress);
    }
  }, 700);
}

/**
 * Hide loading overlay and finalize progress bar.
 */
function hideLoading() {
  clearInterval(loadingInterval);
  const overlay = $('#loading-overlay');
  const bar = $('#loading-bar');
  if (!overlay) return;

  if (bar) {
    bar.style.width = '100%';
    bar.parentElement?.setAttribute('aria-valuenow', 100);
  }

  setTimeout(() => {
    overlay.classList.add('hidden');
    overlay.removeAttribute('aria-busy');
  }, 400);
}

/**
 * Bind form navigation buttons and step clickers.
 */
function bindStepNavigation() {
  $$('.next-step').forEach(btn => {
    btn.addEventListener('click', () => goToStep(parseInt(btn.dataset.next, 10)));
  });
  $$('.prev-step').forEach(btn => {
    btn.addEventListener('click', () => goToStep(parseInt(btn.dataset.prev, 10)));
  });
}

/**
 * Bind priority selection chips with selection caps.
 */
function bindPriorityChips() {
  $$('.priority-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const pressed = chip.getAttribute('aria-pressed') === 'true';
      const selected = $$('.priority-chip[aria-pressed="true"]').length;
      if (pressed) {
        chip.setAttribute('aria-pressed', 'false');
      } else if (selected < MAX_PRIORITIES) {
        chip.setAttribute('aria-pressed', 'true');
      } else {
        announce(`You can select up to ${MAX_PRIORITIES} priorities.`, 'assertive');
      }
    });
  });
}

/**
 * Synchronize budget input with formatted INR preview label.
 */
function bindBudgetPreview() {
  const input = $('#total_budget_inr');
  const display = $('#budget-display');
  if (!input || !display) return;

  input.addEventListener('input', () => {
    const val = parseFloat(input.value);
    if (!isNaN(val) && val > 0) {
      if (val > BUDGET_LIMITS.MAX) {
        display.textContent = `= ${formatINR(val)} (Maximum allowed is ₹10 Crore)`;
        display.style.color = 'var(--color-error, #f87171)';
      } else {
        display.textContent = `= ${formatINR(val)} (₹${val.toLocaleString('en-IN')})`;
        display.style.color = '';
      }
    } else {
      display.textContent = 'Enter your total budget (₹1,000 to ₹10 Crore)';
      display.style.color = '';
    }
  });
}

/**
 * Bind demo panel toggle and card selection handlers.
 */
function bindDemoPanel() {
  const btn = $('#load-demo-btn');
  const panel = $('#demo-panel');
  btn?.addEventListener('click', async () => {
    const isExpanded = btn.getAttribute('aria-expanded') === 'true';
    panel?.classList.toggle('hidden', isExpanded);
    btn.setAttribute('aria-expanded', String(!isExpanded));
    if (!isExpanded && $('#demo-cards .loading-spinner')) {
      try {
        const demos = await fetchDemos();
        renderDemos(demos);
      } catch (err) {
        const c = $('#demo-cards');
        if (c) c.innerHTML = '<p class="form-hint">Could not load demos. Please fill the form manually.</p>';
      }
    }
  });
}

/**
 * Render demo cards into panel.
 * @param {Array<object>} demos
 */
function renderDemos(demos) {
  const container = $('#demo-cards');
  if (!container) return;
  const icons = ['💍', '🎂', '🪔'];
  container.innerHTML = demos.map((demo, i) => `
    <div class="demo-card" role="listitem" tabindex="0" data-demo-id="${escapeHtml(demo.id)}"
      aria-label="Load demo: ${escapeHtml(demo.title)}">
      <span class="demo-card-icon" aria-hidden="true">${icons[i] || '🎊'}</span>
      <div class="demo-card-title">${escapeHtml(demo.title)}</div>
      <div class="demo-card-desc">${escapeHtml(demo.description)}</div>
    </div>
  `).join('');

  $$('.demo-card').forEach((card, i) => {
    const pick = () => loadDemoPayload(demos[i].payload);
    card.addEventListener('click', pick);
    card.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); }
    });
  });
}

/**
 * Populate form inputs with payload from chosen demo scenario.
 * @param {object} payload
 */
function loadDemoPayload(payload) {
  const fieldMap = {
    event_type: '#event_type', event_date: '#event_date',
    city: '#city', city_tier: '#city_tier', guest_count: '#guest_count',
    total_budget_inr: '#total_budget_inr', theme: '#theme', dietary: '#dietary',
    venue_type: '#venue_type', religion_culture: '#religion_culture',
    cultural_customs: '#cultural_customs', special_requirements: '#special_requirements',
  };

  Object.entries(fieldMap).forEach(([key, sel]) => {
    const el = $(sel);
    if (el && payload[key] !== undefined) {
      el.value = payload[key];
      el.dispatchEvent(new Event('input'));
    }
  });

  const priorities = payload.priorities || [];
  $$('.priority-chip').forEach(chip => {
    chip.setAttribute('aria-pressed', String(priorities.includes(chip.dataset.value)));
  });

  $('#demo-panel')?.classList.add('hidden');
  $('#load-demo-btn')?.setAttribute('aria-expanded', 'false');
  $('#planning-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  announce(`Demo loaded: ${payload.event_type} event. Review and submit.`);
}

/**
 * Bind form submit event to API plan generation pipeline.
 */
function bindFormSubmission() {
  $('#event-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    for (let s = 1; s <= 3; s++) {
      if (!validateStep(s)) {
        goToStep(s);
        return;
      }
    }

    const formData = collectFormData();
    if (!formData) return;

    showLoading();
    try {
      const plan = await generatePlan(formData);
      renderPlan(plan);
    } catch (err) {
      const msg = extractErrorMessage(err.payload || err, 'Failed to generate plan.');
      announce(msg, 'assertive');
      alert(`Error:\n${msg}`);
    } finally {
      hideLoading();
    }
  });
}

/**
 * Bind tab navigation buttons and arrow keys.
 */
function bindTabNavigation() {
  $$('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    tab.addEventListener('keydown', e => {
      const tabs = $$('.tab');
      const idx = tabs.indexOf(tab);
      if (e.key === 'ArrowRight') { e.preventDefault(); tabs[(idx + 1) % tabs.length]?.click(); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); tabs[(idx - 1 + tabs.length) % tabs.length]?.click(); }
    });
  });
}

/**
 * Bind new plan button to reset form and state.
 */
function bindNewPlanButton() {
  $('#new-plan-btn')?.addEventListener('click', () => {
    $('#results-section')?.classList.add('hidden');
    $('#planning-section')?.scrollIntoView({ behavior: 'smooth' });
    goToStep(1);
    setCurrentPlan(null);
    document.getElementById('event-form')?.reset();
    $$('.priority-chip').forEach(c => {
      c.setAttribute('aria-pressed', ['food', 'venue', 'decor'].includes(c.dataset.value) ? 'true' : 'false');
    });
    announce('New plan form ready');
  });

  $('#start-planning-btn')?.addEventListener('click', () => {
    $('#planning-section')?.scrollIntoView({ behavior: 'smooth' });
    $('#event_type')?.focus();
  });
}

/**
 * Initialize application listeners and defaults.
 */
export function init() {
  initTheme();
  applyTranslations();
  bindStepNavigation();
  bindPriorityChips();
  bindBudgetPreview();
  bindDemoPanel();
  bindFormSubmission();
  bindTabNavigation();
  bindNewPlanButton();
  initChat(renderPlan);
  initExport();

  $('#theme-toggle')?.addEventListener('click', toggleTheme);
  $('#lang-toggle')?.addEventListener('click', toggleLanguage);

  const dateInput = $('#event_date');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.min = today;
    const defaultDate = new Date();
    defaultDate.setMonth(defaultDate.getMonth() + 3);
    dateInput.value = defaultDate.toISOString().split('T')[0];
  }
}

// Auto-run if executed in browser context
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}
