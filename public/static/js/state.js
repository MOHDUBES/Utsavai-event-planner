/**
 * @fileoverview Application state management with strict encapsulation.
 */

const state = {
  currentPlan: null,
  currentSessionId: null,
  currentStep: 1,
  currentLang: 'en',
};

/**
 * Get the currently active event plan.
 * @returns {object|null}
 */
export function getCurrentPlan() {
  return state.currentPlan;
}

/**
 * Set the currently active event plan and session ID.
 * @param {object|null} plan
 */
export function setCurrentPlan(plan) {
  state.currentPlan = plan;
  state.currentSessionId = plan ? plan.session_id : null;
}

/**
 * Get active session ID.
 * @returns {string|null}
 */
export function getCurrentSessionId() {
  return state.currentSessionId;
}

/**
 * Set active session ID.
 * @param {string|null} id
 */
export function setCurrentSessionId(id) {
  state.currentSessionId = id;
}

/**
 * Get active form step number (1-3).
 * @returns {number}
 */
export function getCurrentStep() {
  return state.currentStep;
}

/**
 * Set active form step number.
 * @param {number} step
 */
export function setCurrentStep(step) {
  state.currentStep = step;
}

/**
 * Get active language code ('en' | 'hi').
 * @returns {string}
 */
export function getCurrentLang() {
  return state.currentLang;
}

/**
 * Set active language code.
 * @param {string} lang
 */
export function setCurrentLang(lang) {
  state.currentLang = lang;
}
