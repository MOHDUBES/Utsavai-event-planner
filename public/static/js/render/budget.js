/**
 * @fileoverview Render module for Budget breakdown, visual donut chart, and stat cards.
 */

import { escapeHtml, formatINR, getCategorySvgIcon, $, $$ } from '../dom.js';
import { DONUT_COLORS } from '../constants.js';

/**
 * Render the entire budget tab content.
 * @param {object} budget
 */
export function renderBudget(budget) {
  const container = $('#budget-content');
  if (!container) return;

  const maxAmount = Math.max(...budget.allocations.map(a => a.amount_inr));

  container.innerHTML = `
    ${renderBudgetStats(budget)}
    ${renderDonutChart(budget.allocations, budget.total_inr)}
    ${renderAllocationBars(budget.allocations, maxAmount)}
    ${renderBudgetAlerts(budget.warnings, budget.suggestions)}
  `;

  animateBars();
}

/**
 * Render top summary stat cards.
 * @param {object} budget
 * @returns {string}
 */
function renderBudgetStats(budget) {
  return `
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
  `;
}

/**
 * Render Donut chart SVG and interactive legend.
 * @param {Array<object>} allocations
 * @param {number} totalInr
 * @returns {string}
 */
export function renderDonutChart(allocations, totalInr) {
  const radius = 68;
  const circumference = 2 * Math.PI * radius;
  let accumulatedPercent = 0;

  const circles = allocations.map((alloc, idx) => {
    const color = DONUT_COLORS[idx % DONUT_COLORS.length];
    const pct = alloc.percentage;
    const strokeDasharray = `${(pct / 100) * circumference} ${circumference}`;
    const strokeDashoffset = -((accumulatedPercent / 100) * circumference);
    accumulatedPercent += pct;

    return `
      <circle cx="100" cy="100" r="${radius}" fill="transparent"
        stroke="${color}" stroke-width="22" stroke-linecap="round"
        stroke-dasharray="${strokeDasharray}" stroke-dashoffset="${strokeDashoffset}"
        class="donut-segment">
        <title>${escapeHtml(alloc.category)}: ${pct.toFixed(1)}% (${formatINR(alloc.amount_inr)})</title>
      </circle>
    `;
  }).join('');

  const legend = allocations.map((alloc, idx) => {
    const color = DONUT_COLORS[idx % DONUT_COLORS.length];
    return `
      <div class="legend-item" role="listitem">
        <span class="legend-cat">
          <span class="legend-color" style="background-color: ${color};" aria-hidden="true"></span>
          <span>${escapeHtml(alloc.category)}</span>
        </span>
        <span class="legend-val">${alloc.percentage.toFixed(0)}% · ${formatINR(alloc.amount_inr)}</span>
      </div>
    `;
  }).join('');

  return `
    <div class="budget-visual">
      <div class="donut-chart-container">
        <svg class="donut-chart-svg" viewBox="0 0 200 200" role="img" aria-label="Budget distribution donut chart">
          <g transform="rotate(-90 100 100)">
            <circle cx="100" cy="100" r="${radius}" fill="transparent" stroke="var(--color-bg-3)" stroke-width="22" />
            ${circles}
          </g>
          <text x="100" y="94" text-anchor="middle" font-size="16" font-weight="800" fill="var(--color-text)" font-family="var(--font-sans)">${formatINR(totalInr)}</text>
          <text x="100" y="112" text-anchor="middle" font-size="10" font-weight="700" fill="var(--color-text-muted)" letter-spacing="1" font-family="var(--font-sans)">TOTAL</text>
        </svg>
      </div>
      <div class="donut-legend" role="list" aria-label="Budget categories legend">${legend}</div>
    </div>
  `;
}

/**
 * Render detailed horizontal progress bars for each budget category.
 * @param {Array<object>} allocations
 * @param {number} maxAmount
 * @returns {string}
 */
function renderAllocationBars(allocations, maxAmount) {
  const items = allocations.map(alloc => `
    <div class="budget-bar-item" role="listitem">
      <div class="bar-header">
        <span class="bar-category">${getCategorySvgIcon(alloc.category)}<span>${escapeHtml(alloc.category)}</span></span>
        <span class="bar-amount">${escapeHtml(alloc.percentage.toFixed(1))}% · ${formatINR(alloc.amount_inr)}</span>
      </div>
      <div class="bar-track" role="progressbar"
        aria-valuenow="${alloc.percentage.toFixed(0)}" aria-valuemin="0" aria-valuemax="100"
        aria-label="${escapeHtml(alloc.category)}: ${alloc.percentage.toFixed(1)}%">
        <div class="bar-fill" style="width: 0%" data-target="${(alloc.amount_inr / maxAmount * 100).toFixed(1)}%"></div>
      </div>
      ${alloc.notes ? `<div class="bar-notes">${escapeHtml(alloc.notes)}</div>` : ''}
    </div>
  `).join('');

  return `
    <div class="budget-chart">
      <h3 class="chart-title">Budget Allocation</h3>
      <div role="list" aria-label="Budget breakdown by category">${items}</div>
    </div>
  `;
}

/**
 * Render warnings and suggestions list.
 * @param {string[]} warnings
 * @param {string[]} suggestions
 * @returns {string}
 */
function renderBudgetAlerts(warnings, suggestions) {
  if (warnings.length === 0 && suggestions.length === 0) return '';
  const wItems = warnings.map(w => `<div class="alert-item warning" role="listitem">${escapeHtml(w)}</div>`).join('');
  const sItems = suggestions.map(s => `<div class="alert-item suggestion" role="listitem">${escapeHtml(s)}</div>`).join('');
  return `<div class="alert-list" role="list" aria-label="Budget warnings and suggestions">${wItems}${sItems}</div>`;
}

/**
 * Animate progress bar widths on render.
 */
function animateBars() {
  requestAnimationFrame(() => {
    setTimeout(() => {
      $$('.bar-fill').forEach(bar => {
        bar.style.width = bar.dataset.target || '0%';
      });
    }, 100);
  });
}
