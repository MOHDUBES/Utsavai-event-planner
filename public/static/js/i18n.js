/**
 * @fileoverview Internationalization dictionary and language toggle functions.
 */

import { announce, $$, $ } from './dom.js';
import { getCurrentLang, setCurrentLang } from './state.js';

export const translations = Object.freeze({
  en: {
    hero_subtitle: "AI-powered planning for weddings, birthdays, Diwali melas & more. Instant budget breakdown, vendor checklists, and personalized ideas — in INR.",
    btn_start_planning: "Start Planning",
    btn_try_demo: "Try a Demo",
    form_title: "📋 Tell Us About Your Event",
    form_subtitle: "Fill in the details and we'll generate a complete plan in seconds.",
    label_event_type: "Event Type",
    label_date: "Event Date",
    label_city: "City",
    label_city_tier: "City Tier",
    label_guests: "Number of Guests",
    label_budget: "Total Budget (₹ INR)",
    label_theme: "Theme / Style (optional)",
    label_dietary: "Dietary Preference",
    label_venue_type: "Venue Type",
    label_religion: "Religion / Culture (optional)",
    label_customs: "Cultural Customs / Rituals (optional)",
    label_requirements: "Special Requirements (optional)",
    label_priorities: "What matters most to you?",
    btn_generate: "Generate My Plan",
    tab_budget: "💰 Budget",
    tab_timeline: "📅 Timeline",
    tab_vendors: "📋 Vendors",
    tab_ai: "✨ Ideas",
    tab_chat: "💬 Chat",
  },
  hi: {
    hero_subtitle: "शादी, जन्मदिन, दिवाली मेले और अन्य उत्सवों के लिए AI-संचालित योजना। तुरंत बजट, वेंडर सूची और व्यक्तिगत विचार — भारतीय रुपये में।",
    btn_start_planning: "योजना शुरू करें",
    btn_try_demo: "डेमो आज़माएं",
    form_title: "📋 अपने उत्सव के बारे में बताएं",
    form_subtitle: "विवरण भरें और हम कुछ ही सेकंड में पूरी योजना तैयार करेंगे।",
    label_event_type: "कार्यक्रम का प्रकार",
    label_date: "कार्यक्रम की तारीख",
    label_city: "शहर",
    label_city_tier: "शहर का स्तर",
    label_guests: "मेहमानों की संख्या",
    label_budget: "कुल बजट (₹ INR)",
    label_theme: "थीम / शैली (वैकल्पिक)",
    label_dietary: "आहार प्राथमिकता",
    label_venue_type: "स्थान का प्रकार",
    label_religion: "धर्म / संस्कृति (वैकल्पिक)",
    label_customs: "सांस्कृतिक रीति-रिवाज (वैकल्पिक)",
    label_requirements: "विशेष आवश्यकताएं (वैकल्पिक)",
    label_priorities: "आपकी प्राथमिकताएं क्या हैं?",
    btn_generate: "मेरी योजना बनाएं",
    tab_budget: "💰 बजट",
    tab_timeline: "📅 समयरेखा",
    tab_vendors: "📋 वेंडर्स",
    tab_ai: "✨ विचार",
    tab_chat: "💬 चैट",
  },
});

/**
 * Apply active language strings to all [data-i18n] DOM elements.
 */
export function applyTranslations() {
  const lang = getCurrentLang();
  $$('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (translations[lang] && translations[lang][key]) {
      el.textContent = translations[lang][key];
    }
  });
}

/**
 * Toggle active language between English and Hindi.
 */
export function toggleLanguage() {
  const current = getCurrentLang();
  const next = current === 'en' ? 'hi' : 'en';
  setCurrentLang(next);

  const btn = $('#lang-toggle');
  if (btn) {
    btn.setAttribute('aria-pressed', next === 'hi' ? 'true' : 'false');
    btn.setAttribute('aria-label', next === 'hi' ? 'Switch to English' : 'हिंदी में बदलें');
    const langEn = btn.querySelector('.lang-en');
    const langHi = btn.querySelector('.lang-hi');
    if (langEn && langHi) {
      langEn.classList.toggle('hidden', next === 'hi');
      langHi.classList.toggle('hidden', next === 'en');
    }
  }

  document.documentElement.setAttribute('lang', next);
  applyTranslations();
  announce(next === 'hi' ? 'हिंदी में बदल दिया गया' : 'Switched to English');
}
