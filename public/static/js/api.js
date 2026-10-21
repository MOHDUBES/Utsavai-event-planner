/**
 * @fileoverview Network API client for UtsavAI backend endpoints.
 */

import { API_BASE } from './constants.js';

/**
 * Fetch pre-configured demo scenarios from the server.
 * @returns {Promise<Array<object>>}
 */
export async function fetchDemos() {
  const res = await fetch(`${API_BASE}/demos`);
  if (!res.ok) {
    throw new Error(`Failed to load demos: ${res.status}`);
  }
  return res.json();
}

/**
 * Submit event intake form and receive generated event plan.
 * @param {object} formData
 * @returns {Promise<object>}
 */
export async function generatePlan(formData) {
  const res = await fetch(`${API_BASE}/plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(formData),
  });
  const data = await res.json();
  if (!res.ok) {
    const error = new Error('Plan generation failed');
    error.payload = data;
    throw error;
  }
  return data;
}

/**
 * Post a chat message to the assistant and retrieve follow-up plan updates.
 * @param {string} sessionId
 * @param {string} message
 * @param {object|null} previousPlanContext
 * @returns {Promise<object>}
 */
export async function sendChatMessage(sessionId, message, previousPlanContext = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      previous_plan_context: previousPlanContext,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    const error = new Error('Chat failed');
    error.payload = data;
    throw error;
  }
  return data;
}
