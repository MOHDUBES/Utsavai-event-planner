/**
 * @fileoverview Export utilities for Markdown, JSON, Print, Web Share, and LocalStorage persistence.
 */

import { escapeHtml, formatINR, announce, titleCase, $ } from './dom.js';
import { getCurrentPlan, getCurrentSessionId } from './state.js';
import { STORAGE_KEY, MAX_SAVED_PLANS } from './constants.js';

/**
 * Initialize all export action button event listeners.
 */
export function initExport() {
  $('#export-md-btn')?.addEventListener('click', exportMarkdown);
  $('#export-json-btn')?.addEventListener('click', exportJson);
  $('#print-btn')?.addEventListener('click', () => { window.print(); announce('Opening print dialog'); });
  $('#save-btn')?.addEventListener('click', savePlan);
  $('#share-btn')?.addEventListener('click', sharePlan);
}

/**
 * Export plan as Markdown file download.
 */
export function exportMarkdown() {
  const plan = getCurrentPlan();
  if (!plan) return;
  const md = generateMarkdown(plan);
  downloadFile(md, 'utsavai-plan.md', 'text/markdown');
  announce('Plan exported as Markdown');
}

/**
 * Export plan as structured JSON file download.
 */
export function exportJson() {
  const plan = getCurrentPlan();
  if (!plan) return;
  const json = JSON.stringify(plan, null, 2);
  downloadFile(json, 'utsavai-plan.json', 'application/json');
  announce('Plan exported as JSON');
}

/**
 * Save current plan to browser LocalStorage.
 */
export function savePlan() {
  const plan = getCurrentPlan();
  const sessionId = getCurrentSessionId();
  if (!plan) return;
  try {
    const raw = localStorage.getItem(STORAGE_KEY) || '[]';
    const saves = JSON.parse(raw);
    saves.unshift({ id: sessionId, savedAt: new Date().toISOString(), plan });
    if (saves.length > MAX_SAVED_PLANS) saves.length = MAX_SAVED_PLANS;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saves));

    const btn = $('#save-btn');
    if (btn) {
      btn.textContent = '✅ Saved!';
      setTimeout(() => { btn.innerHTML = '<span aria-hidden="true">💾</span> Save'; }, 2000);
    }
    announce('Plan saved to browser storage');
  } catch (e) {
    alert('Could not save plan. Browser storage may be full.');
  }
}

/**
 * Share plan via Web Share API or fall back to file download.
 */
export async function sharePlan() {
  const plan = getCurrentPlan();
  if (!plan) {
    announce('No plan to share. Generate a plan first.', 'assertive');
    return;
  }
  const req = plan.event_request;
  const shareData = {
    title: `${titleCase(req.event_type.replace(/_/g, ' '))} Plan – UtsavAI`,
    text: `UtsavAI celebration plan for ${req.guest_count} guests in ${req.city} with budget ${formatINR(plan.budget.total_inr)}.`,
    url: window.location.href,
  };

  if (navigator.share) {
    try {
      await navigator.share(shareData);
      announce('Plan shared');
      return;
    } catch (err) {
      if (err.name === 'AbortError') return;
    }
  }
  exportMarkdown();
}

/**
 * Trigger client-side browser file download from string content.
 * @param {string} content
 * @param {string} filename
 * @param {string} type
 */
export function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Generate human-readable Markdown summary of event plan.
 * @param {object} plan
 * @returns {string}
 */
export function generateMarkdown(plan) {
  const req = plan.event_request;
  const b = plan.budget;
  const t = plan.timeline;

  const allocationsTable = b.allocations
    .map(a => `| ${a.category} | ${a.percentage.toFixed(1)}% | ₹${a.amount_inr.toLocaleString('en-IN')} |`)
    .join('\n');

  const tasksList = t.tasks
    .map(tk => `- [ ] **[${tk.label}]** ${tk.task} *(${tk.category})*${tk.notes ? `\n  > ${tk.notes}` : ''}`)
    .join('\n');

  const vendorsList = plan.vendor_checklist.items
    .map(v => `### ${v.category}\n- **Estimated cost:** ₹${v.estimated_cost_min_inr.toLocaleString('en-IN')} – ₹${v.estimated_cost_max_inr.toLocaleString('en-IN')}\n- **Book:** ${v.booking_lead_time_days} days in advance\n${v.questions_to_ask.map(q => `- ${q}`).join('\n')}`)
    .join('\n\n');

  return `# ${titleCase(req.event_type.replace(/_/g, ' '))} Plan by UtsavAI\nGenerated: ${plan.generated_at}\n\n## Event Details\n- **Event:** ${req.event_type}\n- **Date:** ${req.event_date}\n- **City:** ${req.city} (${req.city_tier})\n- **Guests:** ${req.guest_count}\n- **Budget:** ₹${req.total_budget_inr.toLocaleString('en-IN')}\n\n## Budget Breakdown\n| Category | % | Amount (₹) |\n|---|---|---|\n${allocationsTable}\n| **Contingency (10%)** | 10% | ₹${b.contingency_inr.toLocaleString('en-IN')} |\n| **TOTAL** | 100% | ₹${b.total_inr.toLocaleString('en-IN')} |\n\n## Timeline\n${tasksList}\n\n## Vendor Checklist\n${vendorsList}\n\n## AI Personalization\n### Theme Ideas\n${plan.ai_personalization.theme_ideas.map(th => `- ${th}`).join('\n')}\n\n### Menu Suggestions\n${plan.ai_personalization.menu_suggestions.map(m => `- ${m}`).join('\n')}\n\n### Speech / Toast\n${plan.ai_personalization.speech_toast}\n\n---\n*Generated by UtsavAI – India's Smart Event Planner*\n`;
}
