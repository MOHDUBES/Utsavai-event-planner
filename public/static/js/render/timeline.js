/**
 * @fileoverview Render module for Timeline tasks, urgency badges, and checklist state.
 */

import { escapeHtml, announce, $, $$ } from '../dom.js';
import { getCurrentPlan } from '../state.js';

const PRIORITY_LABELS = Object.freeze({
  critical: '🔴',
  high: '🟡',
  medium: '🔵',
  low: '🟢',
});

/**
 * Render the complete timeline tab content.
 * @param {object} timeline
 */
export function renderTimeline(timeline) {
  const container = $('#timeline-content');
  if (!container) return;

  container.innerHTML = `
    ${renderTimelineMeta(timeline)}
    ${renderTimelineWarnings(timeline.warnings)}
    <div class="timeline-list" role="list" aria-label="Event planning timeline">
      ${timeline.tasks.map((task, idx) => renderTimelineTask(task, idx)).join('')}
    </div>
  `;

  bindTaskCheckboxes();
}

/**
 * Render top timeline metadata banner.
 * @param {object} timeline
 * @returns {string}
 */
function renderTimelineMeta(timeline) {
  return `
    <div class="timeline-meta" aria-label="Timeline summary">
      <span>📅 Event: <strong>${escapeHtml(String(timeline.event_date))}</strong></span>
      <span>⏳ Days remaining: <strong>${escapeHtml(String(timeline.days_until_event))}</strong></span>
      ${timeline.is_compressed ? '<span class="urgent-badge" role="alert">⚡ COMPRESSED TIMELINE</span>' : ''}
    </div>
  `;
}

/**
 * Render timeline warnings if any.
 * @param {string[]} warnings
 * @returns {string}
 */
function renderTimelineWarnings(warnings) {
  if (!warnings || warnings.length === 0) return '';
  return `
    <div class="alert-list" role="list" aria-label="Timeline warnings">
      ${warnings.map(w => `<div class="alert-item warning" role="listitem">${escapeHtml(w)}</div>`).join('')}
    </div>
  `;
}

/**
 * Render single timeline task item.
 * @param {object} task
 * @param {number} idx
 * @returns {string}
 */
function renderTimelineTask(task, idx) {
  const dotIcon = PRIORITY_LABELS[task.priority] || '⚪';
  return `
    <div class="timeline-item priority-${escapeHtml(task.priority)}" role="listitem">
      <div class="timeline-dot" aria-hidden="true" title="${escapeHtml(task.priority)} priority">${escapeHtml(dotIcon)}</div>
      <div class="timeline-body">
        <div class="timeline-header">
          <span class="timeline-label">${escapeHtml(task.label)}</span>
          ${task.is_urgent ? '<span class="urgent-badge">⚡ URGENT</span>' : ''}
        </div>
        <div class="timeline-task">
          <input type="checkbox" id="task-${idx}" data-idx="${idx}" aria-label="${escapeHtml(task.task)}"
            ${task.status === 'done' ? 'checked' : ''} />
          <label for="task-${idx}">${escapeHtml(task.task)}</label>
        </div>
        <div>
          <span class="timeline-category">${escapeHtml(task.category)}</span>
        </div>
        ${task.notes ? `<div class="timeline-notes">${escapeHtml(task.notes)}</div>` : ''}
      </div>
    </div>
  `;
}

/**
 * Bind change handlers to timeline checkboxes.
 */
function bindTaskCheckboxes() {
  $$('.timeline-task input[type="checkbox"]').forEach(box => {
    box.addEventListener('change', () => {
      const idx = parseInt(box.dataset.idx, 10);
      const plan = getCurrentPlan();
      if (plan && plan.timeline.tasks[idx]) {
        plan.timeline.tasks[idx].status = box.checked ? 'done' : 'pending';
        announce(`Task ${box.checked ? 'completed' : 'marked pending'}: ${plan.timeline.tasks[idx].task}`);
      }
    });
  });
}
