/**
 * @fileoverview Conversational AI planning assistant, message rendering, and typing indicators.
 */

import { escapeHtml, announce, $, $$ } from './dom.js';
import { getCurrentPlan, getCurrentSessionId, setCurrentPlan } from './state.js';
import { sendChatMessage } from './api.js';

let typingEl = null;

/**
 * Initialize chat form submission and chip listeners.
 * @param {Function} onPlanUpdated Callback invoked when assistant re-runs the plan
 */
export function initChat(onPlanUpdated) {
  const form = $('#chat-form');
  form?.addEventListener('submit', e => handleChatSubmit(e, onPlanUpdated));
  bindChatChips();
}

/**
 * Handle submission of chat input message.
 * @param {Event} e
 * @param {Function} onPlanUpdated
 */
async function handleChatSubmit(e, onPlanUpdated) {
  e.preventDefault();
  const input = $('#chat-input');
  const message = input ? input.value.trim() : '';
  const sessionId = getCurrentSessionId();

  if (!message || !sessionId) {
    if (!sessionId) announce('Please generate a plan first before chatting.', 'assertive');
    return;
  }

  input.value = '';
  addChatMessage(message, 'user');
  showTypingIndicator();

  try {
    const data = await sendChatMessage(sessionId, message, getCurrentPlan());
    hideTypingIndicator();
    const reply = data.reply || 'I could not generate a response.';
    addChatMessage(reply, 'assistant');

    if (data.is_plan_updated && data.updated_plan) {
      setCurrentPlan(data.updated_plan);
      if (typeof onPlanUpdated === 'function') {
        onPlanUpdated(data.updated_plan);
      }
      addChatMessage('✅ Your plan has been updated! Check the tabs above.', 'assistant');
    }
  } catch (err) {
    hideTypingIndicator();
    addChatMessage('Network error. Please check your connection.', 'assistant');
  }
}

/**
 * Append a chat message bubble to the messages log.
 * @param {string} text
 * @param {'user'|'assistant'} role
 */
export function addChatMessage(text, role) {
  const container = $('#chat-messages');
  if (!container) return;
  const avatar = role === 'assistant' ? '🤖' : '👤';
  const formatted = formatChatText(text);

  const msgEl = document.createElement('div');
  msgEl.className = `chat-message ${role}-message`;
  msgEl.innerHTML = `
    <div class="message-avatar" aria-hidden="true">${avatar}</div>
    <div class="message-content" aria-label="${role === 'assistant' ? 'Assistant' : 'You'}: ${escapeHtml(text.substring(0, 50))}">
      ${formatted}
    </div>
  `;

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
  announce(role === 'assistant' ? 'Assistant replied' : 'Message sent');
}

/**
 * Convert basic markdown asterisks and lists into HTML tags safely.
 * @param {string} text
 * @returns {string}
 */
function formatChatText(text) {
  return escapeHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/- (.*?)(<br>|$)/g, '<li>$1</li>')
    .replace(/((?:<li>.*?<\/li>)+)/g, '<ul>$1</ul>');
}

/**
 * Show animated typing indicator bubble.
 */
export function showTypingIndicator() {
  const container = $('#chat-messages');
  if (!container || typingEl) return;
  typingEl = document.createElement('div');
  typingEl.className = 'chat-message assistant-message';
  typingEl.innerHTML = `
    <div class="message-avatar" aria-hidden="true">🤖</div>
    <div class="typing-indicator" aria-label="Assistant is typing">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  container.appendChild(typingEl);
  container.scrollTop = container.scrollHeight;
}

/**
 * Hide active typing indicator bubble.
 */
export function hideTypingIndicator() {
  typingEl?.remove();
  typingEl = null;
}

/**
 * Bind quick recommendation chips inside the chat interface.
 */
function bindChatChips() {
  $$('.chat-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const input = $('#chat-input');
      if (!input) return;
      input.value = chip.textContent.trim();
      input.focus();
      $('#chat-form')?.dispatchEvent(new Event('submit', { cancelable: true }));
    });
  });
}
