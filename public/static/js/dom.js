/**
 * @fileoverview DOM manipulation, escaping, and formatting utility functions.
 */

import { EVENT_EMOJIS } from './constants.js';

/**
 * Escape HTML to prevent XSS. All user-supplied text must pass through this.
 * @param {unknown} str
 * @returns {string}
 */
export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

/**
 * Format a number as Indian currency with K/L/Cr shorthand.
 * @param {number|string} amount
 * @returns {string}
 */
export function formatINR(amount) {
  const num = Math.abs(Number(amount));
  if (num >= 10_000_000) return `₹${(num / 10_000_000).toFixed(1)}Cr`;
  if (num >= 100_000) return `₹${(num / 100_000).toFixed(1)}L`;
  if (num >= 1_000) return `₹${(num / 1_000).toFixed(1)}K`;
  return `₹${num.toLocaleString('en-IN')}`;
}

/**
 * Format exact INR value with Indian grouping commas.
 * @param {number|string} amount
 * @returns {string}
 */
export function formatINRFull(amount) {
  return `₹${Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

/**
 * Announce message to assistive technology via ARIA live regions.
 * @param {string} message
 * @param {'polite'|'assertive'} priority
 */
export function announce(message, priority = 'polite') {
  const targetId = priority === 'assertive' ? 'aria-assertive' : 'aria-live';
  const el = document.getElementById(targetId);
  if (!el) return;
  el.textContent = '';
  requestAnimationFrame(() => {
    el.textContent = message;
  });
}

/**
 * Query a single DOM element.
 * @param {string} sel
 * @param {ParentNode} ctx
 * @returns {Element|null}
 */
export const $ = (sel, ctx = document) => ctx.querySelector(sel);

/**
 * Query all matching DOM elements as an Array.
 * @param {string} sel
 * @param {ParentNode} ctx
 * @returns {Element[]}
 */
export const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

/**
 * Convert snake_case or slug string to Title Case.
 * @param {string} str
 * @returns {string}
 */
export function titleCase(str) {
  return String(str).replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Retrieve emoji corresponding to an event type.
 * @param {string} type
 * @returns {string}
 */
export function getEventEmoji(type) {
  return EVENT_EMOJIS[type] || '🎊';
}

/**
 * Map category name to sprite SVG markup.
 * @param {string} category
 * @returns {string}
 */
export function getCategorySvgIcon(category) {
  const cat = String(category || '').toLowerCase();
  let iconId = 'icon-venue';
  if (/food|cater|biryani|cake|sweet|fasting/.test(cat)) {
    iconId = 'icon-food';
  } else if (/decor|floral|light|balloon|branding/.test(cat)) {
    iconId = 'icon-decor';
  } else if (/photo|video/.test(cat)) {
    iconId = 'icon-photography';
  } else if (/music|dj|entertainment|artist|performer|av|equipment|sound/.test(cat)) {
    iconId = 'icon-music';
  } else if (/invitation|stationery|card|promotion|gift|return/.test(cat)) {
    iconId = 'icon-invitation';
  } else if (/transport|vehicle|logistic/.test(cat)) {
    iconId = 'icon-transport';
  } else if (/pandit|officiant|puja|religious|ceremonial/.test(cat)) {
    iconId = 'icon-priest';
  } else if (/makeup|groom|attire|bridal/.test(cat)) {
    iconId = 'icon-makeup';
  } else if (/permission|noc|security|cleanup/.test(cat)) {
    iconId = 'icon-permissions';
  }
  return `<svg class="category-svg-icon" width="20" height="20" aria-hidden="true" focusable="false"><use href="/assets/icons/sprite.svg#${iconId}" /></svg>`;
}

/**
 * Extract human-readable error text from backend error payload.
 * @param {unknown} data
 * @param {string} fallback
 * @returns {string}
 */
export function extractErrorMessage(data, fallback = 'Failed to process request.') {
  if (!data) return fallback;
  if (typeof data === 'string') return data;
  if (typeof data.detail === 'string') return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail.map(item => parseErrorItem(item)).join('\n');
  }
  if (typeof data.detail === 'object') {
    return data.detail.message || data.detail.msg || JSON.stringify(data.detail);
  }
  return data.message || fallback;
}

/**
 * Internal helper to parse individual FastAPI validation item.
 * @param {unknown} item
 * @returns {string}
 */
function parseErrorItem(item) {
  if (typeof item === 'string') return item;
  if (item && item.msg) {
    const cleanMsg = item.msg.replace(/^Value error,\s*/i, '');
    const loc = Array.isArray(item.loc) ? item.loc.filter(l => l !== 'body') : [];
    const field = loc.length > 0 ? `${loc.join('.').replace(/_/g, ' ')}: ` : '';
    return `${field}${cleanMsg}`;
  }
  return JSON.stringify(item);
}
