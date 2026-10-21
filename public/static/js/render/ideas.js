/**
 * @fileoverview Render module for AI personalization ideas (Themes, Menus, Decor, Activities, Speeches).
 */

import { escapeHtml, $ } from '../dom.js';

/**
 * Render the entire AI ideas tab content.
 * @param {object} ai
 */
export function renderAI(ai) {
  const container = $('#ai-content');
  if (!container) return;

  container.innerHTML = `
    ${renderProviderBadge(ai)}
    <div class="ai-grid">
      ${renderListCard('Theme Ideas', '🎨', ai.theme_ideas, 'Theme ideas')}
      ${renderListCard('Menu Suggestions', '🍽️', ai.menu_suggestions, 'Menu suggestions')}
      ${renderListCard('Decor Ideas', '💐', ai.decor_ideas, 'Decor ideas')}
      ${renderListCard('Games & Activities', '🎮', ai.games_activities, 'Games and activities')}
      ${renderProseCard('Invitation Wording', '💌', ai.invitation_wording, 'Invitation text')}
      ${renderProseCard('Speech / Toast', '🥂', ai.speech_toast, 'Speech or toast')}
    </div>
  `;
}

/**
 * Render AI provider badge indicating whether content is generated or template fallback.
 * @param {object} ai
 * @returns {string}
 */
function renderProviderBadge(ai) {
  const badge = ai.is_ai_generated
    ? `✨ AI Generated (${escapeHtml(ai.provider_used)})`
    : '📝 Template-based (No API Key)';
  const link = !ai.is_ai_generated
    ? '— <a href="/api/docs#/events/get_demos_api_v1_demos_get" style="color:var(--color-primary)">Add API key for AI suggestions</a>'
    : '';

  return `
    <div class="ai-provider-badge" aria-label="Content source">
      <span aria-hidden="true">${ai.is_ai_generated ? '🤖' : '📝'}</span>
      ${badge} ${link}
    </div>
  `;
}

/**
 * Render an AI card containing bulleted list items.
 * @param {string} title
 * @param {string} icon
 * @param {string[]} items
 * @param {string} ariaLabel
 * @returns {string}
 */
function renderListCard(title, icon, items, ariaLabel) {
  return `
    <div class="ai-card">
      <div class="ai-card-header">
        <span class="ai-card-icon" aria-hidden="true">${icon}</span>
        <span class="ai-card-title">${escapeHtml(title)}</span>
      </div>
      <ul class="ai-list" aria-label="${ariaLabel}">
        ${items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
      </ul>
    </div>
  `;
}

/**
 * Render a full-width AI card containing prose text.
 * @param {string} title
 * @param {string} icon
 * @param {string} text
 * @param {string} ariaLabel
 * @returns {string}
 */
function renderProseCard(title, icon, text, ariaLabel) {
  return `
    <div class="ai-card ai-card-full">
      <div class="ai-card-header">
        <span class="ai-card-icon" aria-hidden="true">${icon}</span>
        <span class="ai-card-title">${escapeHtml(title)}</span>
      </div>
      <div class="ai-prose" aria-label="${ariaLabel}">${escapeHtml(text)}</div>
    </div>
  `;
}
