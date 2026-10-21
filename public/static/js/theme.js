/**
 * @fileoverview Theme management (dark / light mode) and PWA status bar sync.
 */

import { announce, $ } from './dom.js';
import { THEME_STORAGE_KEY } from './constants.js';

/**
 * Initialize theme from localStorage or default to dark mode.
 */
export function initTheme() {
  const saved = localStorage.getItem(THEME_STORAGE_KEY) || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeIcon(saved);
  updateThemeColorMeta(saved);
}

/**
 * Toggle active theme between dark and light modes.
 */
export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem(THEME_STORAGE_KEY, next);
  updateThemeIcon(next);
  updateThemeColorMeta(next);
  announce(`Switched to ${next} mode`);
}

/**
 * Synchronize theme-color meta tag for mobile browsers and PWA.
 * @param {'dark'|'light'} theme
 */
export function updateThemeColorMeta(theme) {
  let meta = $('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.name = 'theme-color';
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', theme === 'dark' ? '#0A0A14' : '#FFF7ED');
}

/**
 * Update theme toggle button icon and accessibility attributes.
 * @param {'dark'|'light'} theme
 */
export function updateThemeIcon(theme) {
  const icon = $('#theme-icon');
  const btn = $('#theme-toggle');
  if (!icon || !btn) return;
  icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  btn.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
  btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
}
