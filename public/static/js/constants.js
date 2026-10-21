/**
 * @fileoverview Central application constants and magic numbers for UtsavAI.
 */

export const API_BASE = '/api/v1';
export const STORAGE_KEY = 'utsavai_saved_plans';
export const THEME_STORAGE_KEY = 'utsavai_theme';

export const BUDGET_LIMITS = Object.freeze({
  MIN: 1_000,
  MAX: 100_000_000,
});

export const GUEST_LIMITS = Object.freeze({
  MIN: 1,
  MAX: 10_000,
});

export const MAX_PRIORITIES = 6;
export const MAX_SAVED_PLANS = 5;

export const LOADING_STEPS = Object.freeze([
  'Calculating budget allocation…',
  'Planning vendor checklist…',
  'Building your timeline…',
  'Running sanity checks…',
  'Getting AI personalization…',
  'Finalizing your plan…',
]);

export const DONUT_COLORS = Object.freeze([
  '#F59E0B', '#6366F1', '#10B981', '#EC4899',
  '#8B5CF6', '#3B82F6', '#F97316', '#14B8A6',
  '#EAB308', '#06B6D4', '#84CC16', '#A855F7',
]);

export const EVENT_EMOJIS = Object.freeze({
  wedding: '💍',
  birthday: '🎂',
  diwali_mela: '🪔',
  eid_celebration: '🌙',
  navratri: '💃',
  college_fest: '🎓',
  corporate: '🏢',
  anniversary: '💕',
  baby_shower: '👶',
  rwa_event: '🏘️',
  other: '🎉',
});

export const STEP_NAMES = Object.freeze([
  '',
  'Basic Information',
  'Event Details',
  'Budget Priorities',
]);
