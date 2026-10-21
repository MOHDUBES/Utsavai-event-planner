/**
 * @fileoverview Render module for Vendor checklist items and Sanity checks alerts.
 */

import { escapeHtml, formatINR, getCategorySvgIcon, $, $$ } from '../dom.js';

/**
 * Render sanity check alerts at the top of results.
 * @param {Array<object>} checks
 */
export function renderSanityChecks(checks) {
  const container = $('#sanity-alerts');
  if (!container) return;

  const errors = checks.filter(c => c.status === 'error');
  const warnings = checks.filter(c => c.status === 'warning');
  const oks = checks.filter(c => c.status === 'ok');
  const toShow = [...errors, ...warnings, ...(oks.length > 0 ? [oks[0]] : [])];

  container.innerHTML = toShow.map(check => {
    const icon = check.status === 'ok' ? '✅' : check.status === 'warning' ? '⚠️' : '❌';
    return `
      <div class="sanity-alert ${escapeHtml(check.status)}" role="status">
        <span aria-hidden="true">${icon}</span>
        <div>
          <strong>${escapeHtml(check.check_name)}:</strong> ${escapeHtml(check.message)}
          ${check.suggestion ? `<br><em>💡 ${escapeHtml(check.suggestion)}</em>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Render vendor checklist tab content.
 * @param {object} checklist
 */
export function renderVendors(checklist) {
  const container = $('#vendors-content');
  if (!container) return;

  container.innerHTML = `
    <div class="section-badge" aria-hidden="true">
      📋 ${escapeHtml(String(checklist.total_categories))} vendor categories
    </div>
    <div class="vendor-grid" role="list" aria-label="Vendor checklist">
      ${checklist.items.map((vendor, idx) => renderVendorCard(vendor, idx)).join('')}
    </div>
  `;

  bindVendorToggles();
}

/**
 * Render individual vendor card article.
 * @param {object} vendor
 * @param {number} idx
 * @returns {string}
 */
function renderVendorCard(vendor, idx) {
  return `
    <article class="vendor-card" role="listitem">
      <div class="vendor-card-header" tabindex="0" data-idx="${idx}"
        aria-expanded="true" aria-controls="vendor-body-${idx}">
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
  `;
}

/**
 * Bind keyboard and click toggle handlers to vendor card headers.
 */
function bindVendorToggles() {
  $$('.vendor-card-header').forEach(header => {
    const idx = header.dataset.idx;
    const toggle = () => toggleVendor(header, idx);
    header.addEventListener('click', toggle);
    header.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggle();
      }
    });
  });
}

/**
 * Toggle collapse state of a vendor card body.
 * @param {HTMLElement} header
 * @param {string|number} idx
 */
function toggleVendor(header, idx) {
  const body = $(`#vendor-body-${idx}`);
  const arrow = $(`#vendor-arrow-${idx}`);
  if (!body) return;
  const isExpanded = header.getAttribute('aria-expanded') === 'true';
  body.style.display = isExpanded ? 'none' : '';
  header.setAttribute('aria-expanded', String(!isExpanded));
  if (arrow) arrow.textContent = isExpanded ? '▼' : '▲';
}
