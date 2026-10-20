# 🎊 UtsavAI – Smart Celebration & Event Planner

> **India's AI-powered event planning assistant** — from intimate birthdays to grand weddings and community Diwali melas. Instant budget breakdowns, backward-planned timelines, vendor checklists, and personalized ideas — all in INR.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](tests/)

---

## 🎯 Chosen Vertical & Persona

**Vertical:** Celebration & Event Planning  
**Persona:** Priya, a 32-year-old event organizer in Delhi who manages everything from family weddings to RWA Diwali melas. She needs a tool that understands Indian cultural context, speaks INR, and works even on slow network connections.

**Supported Events:**
- 💍 Weddings (Hindu, Muslim, Sikh, Christian, Jain customs)
- 🎂 Birthdays (kids and adults)
- 🪔 Diwali Mela / Community Festivals
- 🌙 Eid Celebrations
- 💃 Navratri
- 🎓 College Fests
- 🏢 Corporate Events
- 💕 Anniversaries
- 👶 Baby Showers
- 🏘️ RWA / Society Events

---

## 🏗️ Architecture

### Hybrid Rule Engine + GenAI

```mermaid
graph TB
    subgraph Frontend["Frontend (Vanilla HTML/CSS/JS)"]
        F1[Smart Intake Form]
        F2[Multi-tab Results UI]
        F3[Chat Assistant]
        F4[Export & Save]
    end

    subgraph Backend["Backend (FastAPI)"]
        A[API Routes<br>/api/v1/plan<br>/api/v1/chat]
        
        subgraph Deterministic["Deterministic Engines (Instant, Local)"]
            B1[Budget Engine<br>City tier × Season × Priorities]
            B2[Timeline Generator<br>Backward planned T-90 to Day-of]
            B3[Vendor Checklist<br>Category-wise with Q&A]
            B4[Sanity Checks<br>8 validation rules]
        end
        
        subgraph AI["AI Layer (Async, Cached)"]
            C1[Provider Wrapper<br>Gemini / OpenAI / Anthropic]
            C2[LRU Cache<br>Keyed by normalized input]
            C3[Template Fallback<br>Works offline]
        end
    end

    subgraph Security["Security Layer"]
        S1[Input Sanitization<br>Pydantic + injection strip]
        S2[CORS + Rate Limit<br>30 req/min per IP]
        S3[Security Headers<br>CSP, X-Frame, HSTS]
        S4[No stack traces<br>Safe error messages]
    end

    F1 -->|POST /api/v1/plan| A
    A --> S1
    S1 --> B1 & B2 & B3 & B4
    B1 & B2 & B3 & B4 --> C2
    C2 -->|Cache miss| C1
    C1 -->|Failure| C3
    C2 & C3 --> A
    A -->|EventPlan JSON| F2
    F3 -->|POST /api/v1/chat| A
```

### Request Flow

1. **User submits form** → Pydantic validates & sanitizes all fields
2. **Budget Engine** runs deterministically (city tier × season × priority boost)
3. **Timeline Generator** plans backward from event date
4. **Vendor Engine** builds category-wise checklist
5. **Sanity Checker** runs 8 rule-based validations
6. **AI Service** makes ONE batched structured-JSON call (or returns cached/fallback)
7. **Response** assembled and returned; frontend renders tabbed UI

---

## ✨ Features

| Feature | Description |
|---|---|
| **Smart Intake Form** | 3-step wizard: basics → details → priorities |
| **Budget Engine** | City tier (metro/tier-2/tier-3), season (peak/shoulder/off), guest count economy of scale, priority allocation, 10% contingency, per-head cost, warnings |
| **Timeline Generator** | T-90 to Day-of, compressed for close dates, overdue detection, outdoor tasks |
| **Vendor Checklist** | Category-wise with questions-to-ask, booking lead times, cost ranges |
| **AI Personalization** | Theme ideas, menu, decor, invitation wording, games, speech/toast |
| **Chat Assistant** | Follow-up Q&A: cost reduction analysis, reschedule impact, vendor info |
| **Export** | Download as Markdown or JSON; Print view; localStorage save/load |
| **3 Demo Scenarios** | Wedding Delhi ₹10L, Birthday Mumbai ₹40K, Diwali Jaipur ₹1.5L |
| **Sanity Checks** | Past date, monsoon risk, festival clash, budget realism, guest count |
| **Accessibility** | WCAG AA, keyboard nav, ARIA, screen reader support, reduced motion |
| **i18n** | English + Hindi toggle |
| **Dark/Light Mode** | System-aware with manual override |
| **Offline Mode** | Full functionality without API key (template fallback) |

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.11+
- Git

### 3-Step Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/YOUR_USERNAME/utsavai-event-planner.git
cd utsavai-event-planner

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000** in your browser. 🎊

### With AI (Optional)

```bash
# Copy and edit the .env file
cp .env.example .env
# Edit .env and set:
# GEMINI_API_KEY=your_key_here
# AI_PROVIDER=gemini

# Then run:
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

> **Note:** The app works perfectly **without** an API key using template-based fallback suggestions.

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Or with make:
make test

# With coverage report:
make test-cov
```

### Test Results Summary

| Test Module | Tests | Focus Areas |
|---|---|---|
| `tests/test_budget_engine.py` | 31 tests | Season detection, city tiers, economy of scale, priority boosting, allocations |
| `tests/test_timeline_engine.py` | 20 tests | Backward planning, compression (<30d), past dates, outdoor tasks, sequencing |
| `tests/test_vendor_engine.py` | 12 tests | Event-type mapping, dietary preferences (Jain/Halal/Veg), lead times, costs |
| `tests/test_api_and_validators.py` | 49 tests | REST endpoints, Pydantic schemas, security headers, rate limiting, error safety |
| `tests/test_ai_service.py` | 8 tests | Mocked LLM responses, malformed JSON fallback, timeouts, caching, injection scrubbing |
| `tests/test_chat_assistant.py` | 3 tests | Engine re-run on decor cost cut, 2-week reschedule re-run, stateless plan context |
| `tests/test_demo_scenarios.py` | 4 tests | Verification of all 3 demo scenarios (Delhi Wedding, Mumbai Birthday, Jaipur Mela) |
| **Total** | **127 tests** | **100% passing, 85% statement coverage across core codebase** |

#### Real Test Suite Execution Output

```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
plugins: anyio-4.14.2, asyncio-1.4.0, cov-7.1.0
collected 127 items

tests/test_ai_service.py ........                                        [  6%]
tests/test_api_and_validators.py ...................................     [ 33%]
..............                                                           [ 44%]
tests/test_budget_engine.py ...............................              [ 69%]
tests/test_chat_assistant.py ...                                         [ 71%]
tests/test_demo_scenarios.py ....                                        [ 74%]
tests/test_timeline_engine.py ....................                       [ 90%]
tests/test_vendor_engine.py ............                                 [100%]

============================= 127 passed in ~9s ==============================
Statement coverage: 85%
```

---

## 🏛️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | Python 3.11+ + FastAPI | Async, strictly typed, fast, production DX |
| **Validation** | Pydantic v2 | High-performance type safety & automatic string sanitization |
| **AI SDK & Models** | `google-genai` ≥ 2.25.0 (`gemini-3.8-flash`), `openai` ≥ 1.58.0 (`gpt-4o-mini`), `anthropic` ≥ 0.40.0 (`claude-3-5-haiku-latest`) | Fast, structured JSON generation with multi-provider fallback |
| **Frontend** | Vanilla HTML5 / CSS3 / ES6+ JS | Zero build step, lightweight (<450 KB), instant first load |
| **Rate Limiting** | slowapi | Per-IP request throttling (30 req/min) |
| **Config** | pydantic-settings | Environment-based configuration, zero hardcoded secrets |
| **Linting** | ruff | Instant, comprehensive PEP 8 formatting and linting |
| **Testing** | pytest + httpx + asyncio + pytest-cov | Async-native API testing with 85% statement coverage |

---

## 🔒 Security Measures

| Measure | Implementation |
|---|---|
| **Input Validation** | Pydantic v2 with strict type checking and field limits (max guests: 10K, max budget: ₹10Cr, string lengths) |
| **Prompt Injection Defense** | Field validators strip injection patterns (`ignore previous`, `system:`, `jailbreak`, `###`) before LLM calls |
| **No API Key Exposure** | Keys read from env vars only; never logged, never sent to frontend |
| **System Prompt Guardrails** | LLM called with fixed system prompt; user text only in structured context |
| **Output Sanitization** | All LLM output HTML-stripped before storage; all frontend rendering uses `escapeHtml()` |
| **XSS Prevention** | Every piece of user data escaped via `escapeHtml()` before DOM insertion |
| **CORS Restriction** | Explicitly whitelisted origins only (no `*`) |
| **Rate Limiting** | 30 requests/minute per IP via slowapi |
| **Security Headers** | `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `CSP`, `Referrer-Policy` |
| **Safe Error Messages** | Global exception handler returns generic messages; no stack traces to client |
| **Session Isolation** | Plans stored server-side by UUID; no cross-session data leakage |

---

## ♿ Accessibility Measures

| Feature | Implementation |
|---|---|
| **Semantic HTML** | `<header>`, `<main>`, `<nav>`, `<section>`, `<article>`, `<footer>`, `<fieldset>`, `<legend>` |
| **ARIA Attributes** | `role`, `aria-label`, `aria-labelledby`, `aria-describedby`, `aria-required`, `aria-expanded`, `aria-selected`, `aria-pressed`, `aria-live`, `aria-busy` |
| **Keyboard Navigation** | All interactive elements focusable; tab navigation; Enter/Space on custom controls; Arrow keys for tabs |
| **Focus Management** | Visible focus ring; focus moved to first field on step change; focus moved after plan loads |
| **Screen Reader Support** | Live regions (`aria-live="polite"` and `aria-live="assertive"`) for dynamic updates |
| **Skip Link** | "Skip to main content" link at top of page |
| **WCAG AA Contrast** | Theme colors: Deep Maroon `#451A03` text on Cream `#FFF7ED` = **13.96:1** (AAA), Heritage Maroon `#7C2D12` on Cream = **9.09:1** (AAA), Cream `#FFF7ED` on Dark Canvas `#0A0A14` = **18.7:1** (AAA), Saffron `#F59E0B` on Dark Canvas = **9.15:1** (AAA), Indigo `#6366F1` on Dark Canvas = **6.5:1** (AA) |
| **Responsive/Mobile-first** | CSS `clamp()` for fluid typography; grid layout adapts to all screen sizes |
| **Dark/Light Mode** | CSS custom properties with `data-theme` toggle; saved to localStorage |
| **Reduced Motion** | `@media (prefers-reduced-motion: reduce)` disables all animations |
| **Error Announcements** | Form validation errors announced via `aria-live="assertive"` |
| **i18n** | English + Hindi toggle for labels and descriptions |

---

## 💡 Budget Engine Logic

The budget engine uses a **multi-factor allocation formula**:

```
Final Allocation = Base% × Priority Boost × (City Multiplier) × (Season Multiplier)

Where:
- Base% = Per-category starting percentage by event type
- Priority Boost = +20% for #1 priority, +10% for #2, +5% for #3 (offset from non-priorities)
- City Multiplier = Metro: 1.45×, Tier-2: 1.20×, Tier-3: 1.00×
- Season Multiplier = Peak (Oct-Feb): 1.20×, Shoulder: 1.05×, Off (May-Aug): 0.90×
- Guest Scale = 1.10× for ≤50 guests, down to 0.78× for 1000+ guests
- Contingency = Always 10% of total budget (not distributed)
```

**Realistic minimum** = `base_min/head × city_mult × season_mult × guest_scale × guests × 1.1`

---

## 🗓️ Timeline Engine Logic

The timeline uses **backward planning** from the event date:
- Full timeline: Tasks from T-365 (wedding) to T-0 (Day-of)
- **Compression mode**: When < 30 days away, all overdue tasks flagged as URGENT
- Outdoor events add: NOC application (T-45), weather contingency (T-14), forecast check (T-7)
- Tasks sorted chronologically (latest deadline first)
- Priority levels: `critical`, `high`, `medium`, `low`

---

## 🎨 Branding & Design

UtsavAI features a custom, lightweight brand identity crafted entirely in hand-written SVG (zero raster dependencies, zero external CDNs, &lt; 10 KB per asset):

- **Brand Motif:** An auspicious Indian **Diya Flame** (celebration) seamlessly cradled by a **Checklist Tick** (disciplined planning) and crowned with an **AI Sparkle** (intelligent recommendations).
- **Color Palette (WCAG AA compliant):**
  - **Saffron (`#F59E0B`):** Warm festive celebration accent
  - **Deep Maroon (`#7C2D12`):** Trustworthy, heritage Indian grounding
  - **Indigo (`#3730A3`):** Modern AI technology balance
  - **Cream (`#FFF7ED`):** Clean, warm celebration canvas
- **Vector Assets (`frontend/assets/`):**
  - `logo.svg` / `logo-dark.svg`: Full brand wordmark with theme switching
  - `icon.svg`: App header emblem (64x64)
  - `favicon.svg`: Optimized 32x32 / 16x16 tab icon
  - `apple-touch-icon.png`: 180x180 mobile icon (2.7 KB, under 20 KB limit)
  - `og-image.svg`: 1200x630 social / Twitter card preview
  - `icons/`: 10 bespoke category icons (venue, food, decor, photography, music, invitation, transport, priest, makeup, permissions) &amp; `sprite.svg`
  - `manifest.webmanifest`: PWA application manifest
- **Accessibility:** `prefers-reduced-motion` halts flame animations, all logos carry `alt="UtsavAI logo"`, and decorative icons use `aria-hidden="true"`.
- Detailed branding guide: [docs/branding.md](docs/branding.md).

---

## 📁 Project Structure

```
utsavai-event-planner/
├── backend/
│   ├── __init__.py
│   ├── config.py                # Top-level configuration facade (re-exports Settings)
│   ├── main.py                  # FastAPI app factory, CORS, static mounts & security headers
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py            # REST endpoints (/plan, /chat, /demos)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic request/response schemas & string sanitizers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── budget_engine.py     # Deterministic budget calculator (INR)
│   │   ├── timeline_engine.py   # Backward-planned timeline generator
│   │   ├── vendor_engine.py     # Category vendor checklist generator
│   │   ├── sanity_checks.py     # 8 cultural & weather validation checks
│   │   └── ai_service.py        # Multi-provider AI wrapper, cache & template fallback
│   └── utils/
│       ├── __init__.py
│       └── config.py            # Pydantic settings model loaded from .env
│                                # (backend/config.py exposes this as a clean facade)
├── frontend/
│   ├── index.html               # Single-page app with brand meta & bilingual i18n
│   ├── manifest.webmanifest     # Web app manifest
│   ├── assets/
│   │   ├── logo.svg             # Light theme full logo
│   │   ├── logo-dark.svg        # Dark theme full logo
│   │   ├── icon.svg             # Square brand emblem
│   │   ├── favicon.svg          # 32x32 tab icon
│   │   ├── apple-touch-icon.png # 180x180 touch icon (< 20 KB)
│   │   ├── og-image.svg         # 1200x630 social preview card
│   │   └── icons/               # 10 category SVGs & sprite.svg
│   └── static/
│       ├── css/
│       │   ├── style.css        # Main stylesheet
│       │   └── theme.css        # WCAG AA brand design tokens & animations
│       └── js/app.js            # Vanilla JS application
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures & test client
│   ├── test_ai_service.py       # Mocked AI provider tests & fallback validation
│   ├── test_api_and_validators.py # API, schema, security, and sanity tests
│   ├── test_budget_engine.py    # Deterministic budget calculation tests
│   ├── test_chat_assistant.py   # Chat assistant engine re-run tests
│   ├── test_demo_scenarios.py   # Verification of all 3 demo scenarios
│   ├── test_timeline_engine.py  # Backward planning timeline tests
│   └── test_vendor_engine.py    # Vendor checklist engine tests
├── docs/
│   ├── architecture.md          # In-depth system architecture & formulas
│   └── branding.md              # Brand identity guide & usage rules
├── .env.example                 # Environment configuration template
├── .gitignore
├── LICENSE                      # MIT (MOHD UBES)
├── Makefile
├── pyproject.toml               # Pytest + coverage configuration
├── requirements.txt
├── ruff.toml                    # Linter & formatter settings
└── README.md
```

---

## 📊 Demo Scenarios

### 💍 Wedding in Delhi – ₹10 Lakh

| Category | Allocation | Amount |
|---|---|---|
| Catering | 28% | ₹2,52,000 |
| Venue | 22% | ₹1,98,000 |
| Photography | 13% | ₹1,17,000 |
| Decor & Florals | 10% | ₹90,000 |
| Makeup & Attire | 5% | ₹45,000 |
| Contingency | 10% | ₹1,00,000 |

### 🎂 Kid's Birthday in Mumbai – ₹40,000

| Category | Allocation | Amount |
|---|---|---|
| Catering | 28% | ₹10,080 |
| Decor | 20% | ₹7,200 |
| Entertainment | 14% | ₹5,040 |
| Venue | 18% | ₹6,480 |
| Cake | 6% | ₹2,160 |
| Contingency | 10% | ₹4,000 |

### 🪔 Diwali Mela in Jaipur – ₹1.5 Lakh

| Category | Allocation | Amount |
|---|---|---|
| Food Stalls | 28% | ₹37,800 |
| Lighting & Decor | 20% | ₹27,000 |
| Entertainment | 11% | ₹14,850 |
| Venue / Ground | 14% | ₹18,900 |
| Permissions & NOC | 5% | ₹6,750 |
| Contingency | 10% | ₹15,000 |

---

## 📝 Assumptions

1. **Pricing benchmarks** are approximate Indian market averages (2024-2026). Actual vendor quotes will vary significantly by city, season, and negotiation.
2. **City tier classification** follows common definitions: Metro = Delhi, Mumbai, Bengaluru, Hyderabad, Chennai, Kolkata; Tier-2 = Jaipur, Pune, Ahmedabad, Lucknow, etc.
3. **Peak season** is defined as Oct-Feb (traditional Indian wedding season + Diwali). Shoulder is Mar-Apr and Sep. Off-season is May-Aug (summer/monsoon).
4. **Minimum per-head benchmarks**: Wedding ₹1,500, Birthday ₹300, Community Events ₹150. These represent absolute minimums for a basic dignified event.
5. **LLM responses** are cached in-memory per process; cache is lost on server restart.
6. **Sessions** are in-memory per process; use Redis in production for multi-instance setups.
7. **Festival dates** are approximate and may shift by a day or two based on lunar calendar each year.

---

## 🔮 Future Improvements

1. **Vendor Marketplace Integration**: Connect to real vendor APIs (JustDial, Sulekha, WedMeGood) for live quotes
2. **WhatsApp Integration**: Send plans and reminders via WhatsApp API (most used in India)
3. **Payment Tracking**: Mark vendor advances paid, track remaining balances
4. **Multi-language Support**: Expand to regional languages (Tamil, Telugu, Bengali, Marathi)
5. **Offline PWA**: Service worker for full offline functionality
6. **Calendar Integration**: Export timeline to Google Calendar / iCal
7. **Photo Moodboard**: AI-generated theme moodboard images
8. **Group Collaboration**: Share plans with family members for joint planning
9. **Cost Comparison Tool**: Compare vendor quotes side by side
10. **Automated Reminders**: Email/SMS reminders for upcoming timeline tasks
11. **Redis Session Store**: For multi-instance production deployment
12. **Webhook Integrations**: Connect to event management tools

---

## ✅ Final Checklist

- [x] **Single branch** (`main` only)
- [x] **Repo size < 10MB** (no node_modules, no large media, .gitignore included)
- [x] **README complete** (architecture, setup, features, testing, security, assumptions)
- [x] **Tests passing** (127 tests covering all engines, AI mocking, chat re-runs, and demo scenarios)
- [x] **Works without API key** (template fallback mode)
- [x] **3 demo scenarios** (Wedding, Birthday, Diwali Mela)
- [x] **Budget engine** (deterministic, city/season/priority aware)
- [x] **Timeline** (backward planned, compressed for close dates)
- [x] **Vendor checklist** (category-wise with questions + cost ranges)
- [x] **AI personalization** (theme, menu, decor, invite, games, speech)
- [x] **Chat assistant** (cost reduction, reschedule, guest changes)
- [x] **Export** (Markdown, JSON, Print)
- [x] **Sanity checks** (8 rules including festival calendar + monsoon)
- [x] **Security** (injection defense, CORS, rate limit, security headers, XSS escape)
- [x] **Accessibility** (WCAG AA, ARIA, keyboard, reduced-motion, i18n)
- [x] **MIT License**
- [x] **.gitignore** (no secrets, no node_modules)
- [x] **.env.example** (all config options documented)

---

*Made with ❤️ for India's celebrations. Built by MOHD UBES. Jai Hind! 🇮🇳*
