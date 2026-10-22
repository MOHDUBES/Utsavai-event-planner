# 🎊 UtsavAI – Smart Celebration & Event Planner

> **India's AI-powered event planning assistant** — from intimate birthdays to grand weddings and community Diwali melas. Instant budget breakdowns, backward-planned timelines, vendor checklists, and personalized ideas — all in INR.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 159 Passed](https://img.shields.io/badge/tests-159%20passed%20(92%25%20cov)-brightgreen)](tests/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: Mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy.readthedocs.io/)
[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live-success?logo=vercel)](https://utsavai-event-planner.vercel.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-MOHDUBES%2FUtsavai--event--planner-181717?logo=github)](https://github.com/MOHDUBES/Utsavai-event-planner)

> 🌐 **Live Deployed URL:** [https://utsavai-event-planner.vercel.app/](https://utsavai-event-planner.vercel.app/)  
> 📱 **Mobile & Desktop Web App:** Fully responsive, PWA-enabled, serverless on Vercel

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
            B2[Timeline Generator<br>Backward planned T-365 to Day-of]
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
| **Timeline Generator** | T-365 to Day-of, compressed for close dates, overdue detection, outdoor tasks |
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
git clone https://github.com/mohd-ubes/utsavai-event-planner.git
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

## 🌐 Deployment (Vercel)

UtsavAI is pre-configured for zero-friction serverless deployment on [Vercel](https://vercel.com):
- **Static Frontend (`public/`):** Served globally from Vercel's Edge CDN with instant response times and zero server runtime.
- **Python ASGI Backend (`api/index.py`):** Serverless function execution via FastAPI on Python 3.12 with `/api/*` rewrites defined in `vercel.json`.

### Option 1: Deploy with Vercel CLI

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy preview
vercel

# 3. Deploy to production
vercel --prod
```

### Option 2: Deploy via GitHub Integration

1. Push your repository to GitHub.
2. Go to [vercel.com/new](https://vercel.com/new) and import `utsavai-event-planner`.
3. Framework Preset: **Other**.
4. Root Directory: `./` (default).
5. Configure Environment Variables in Project Settings:
   - `AI_PROVIDER`: `gemini` (or `none` for offline fallback)
   - `GEMINI_API_KEY`: `your_gemini_api_key`
   - `GEMINI_MODEL`: `gemini-3.8-flash`
   - `CORS_ORIGINS`: `https://utsavai-event-planner.vercel.app`
   - `CORS_ORIGIN_REGEX`: `^https://.*\.vercel\.app$`
6. Click **Deploy**. Your app will be live within seconds!

---

## 🧪 Testing

```bash
# Install development and testing dependencies
pip install -r requirements-dev.txt

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
| `tests/test_api_and_validators.py` | 51 tests | REST endpoints, Pydantic schemas, security headers, rate limiting, Vercel ASGI entrypoint, config re-exports |
| `tests/test_ai_service.py` | 8 tests | Mocked LLM responses, malformed JSON fallback, timeouts, caching, injection scrubbing |
| `tests/test_chat_assistant.py` | 9 tests | Engine re-run on decor cost cut, 2-week reschedule re-run, stateless plan context, timeline/vendor/guest queries |
| `tests/test_demo_scenarios.py` | 4 tests | Verification of all 3 demo scenarios (Delhi Wedding, Mumbai Birthday, Jaipur Mela) |
| `tests/test_frontend_static.py` | 8 tests | Viewport meta (`viewport-fit=cover`), PWA manifest integrity, asset paths, HTTP 200 |
| **Total** | **143 tests** | **100% passing, 91% statement coverage across core codebase** |

#### Real Test Suite Execution Output

```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
plugins: anyio-4.14.2, asyncio-1.4.0, cov-7.1.0
collected 136 items

tests/test_ai_service.py ........                                        [  6%]
tests/test_api_and_validators.py ...................................     [ 32%]
...............                                                          [ 43%]
tests/test_budget_engine.py ...............................              [ 65%]
tests/test_chat_assistant.py ...                                         [ 68%]
tests/test_demo_scenarios.py ....                                        [ 71%]
tests/test_frontend_static.py ........                                   [ 76%]
tests/test_timeline_engine.py ....................                       [ 91%]
tests/test_vendor_engine.py ............                                 [100%]

============================= 136 passed in ~76s =============================
Statement coverage: 86%
```

---

## 🏛️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Backend** | Python 3.11+ + FastAPI | Async, strictly typed, fast, production DX |
| **Validation** | Pydantic v2 | High-performance type safety & automatic string sanitization |
| **AI SDK & Models** | `google-genai` ≥ 2.25.0 (`gemini-2.5-flash`), `openai` ≥ 1.58.0 (`gpt-4o-mini`), `anthropic` ≥ 0.40.0 (`claude-3-5-haiku-latest`) | Fast, structured JSON generation with multi-provider fallback |
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
| **WCAG AA Contrast** | Theme colors: Deep Maroon `#451A03` on Cream `#FFF7ED` = **14.11:1** (AAA), Heritage Maroon `#7C2D12` on Cream = **8.83:1** (AAA), Cream `#FFF7ED` on Dark Canvas `#0A0A14` = **18.55:1** (AAA), Saffron `#F59E0B` on Dark Canvas = **9.17:1** (AAA), Indigo `#818CF8` on Dark Canvas = **6.60:1** (AA), Indigo `#3730A3` on Cream = **9.36:1** (AAA) |
| **Responsive/Mobile-first** | CSS `clamp()` for fluid typography; grid layout adapts to all screen sizes |
| **Dark/Light Mode** | CSS custom properties with `data-theme` toggle; saved to localStorage |
| **Reduced Motion** | `@media (prefers-reduced-motion: reduce)` disables all animations |
| **Error Announcements** | Form validation errors announced via `aria-live="assertive"` |
| **i18n** | English + Hindi toggle for labels and descriptions |

---

## 📱 Mobile & Responsive Design

UtsavAI is engineered with a **mobile-first architecture** designed to feel native, responsive, and tactile on small phones (320px–430px) as well as tablets and desktops:

### 1. Breakpoints & Viewport Adaptation
- **Tested Widths:** `320px` (iPhone SE / compact devices), `360px` (standard mobile), `390px` (iPhone 12/13/14), `414px` (iPhone Plus/XR), `430px` (iPhone Pro Max), `768px` (iPads/tablets), and `1280px` (laptops/desktops).
- **Mobile-First CSS:** Base styles target small touchscreens first, followed by min-width progressive enhancements:
  - `@media (min-width: 600px)`: Tablet 2-column layouts and expanded navigation.
  - `@media (min-width: 900px)`: Desktop cards, side-by-side forms, and expanded charts.
  - `@media (min-width: 1200px)`: Large desktop wide canvas.
- **Viewport & Notch Support:** `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">` paired with `env(safe-area-inset-*)` guarantees seamless rendering around camera notches, dynamic islands, and bottom home gesture indicators.
- **Dynamic Viewports (`100dvh`):** Full-height containers (loading overlay, mobile chat drawer) utilize dynamic viewport units (`100dvh`) to avoid sudden jumps when mobile address bars collapse/expand.

### 2. Touch Targets & Form Ergonomics
- **44×44px Touch Targets:** Strict adherence to WCAG 2.5.5 target size; all buttons, chips, tabs, demo cards, and toggles provide a minimum 44×44px active touch area with `touch-action: manipulation`.
- **Zero iOS Auto-Zoom:** All form inputs, selects, and textareas enforce a minimum `16px` font size, preventing unwanted iOS Safari page magnification on focus.
- **Smart Keypads & Attributes:** Inputs provide semantic `inputmode="numeric"` for guests and budget, `type="date"` with auto-min/defaults, and explicit autocomplete configurations.
- **Virtual Keyboard Awareness:** Focused inputs automatically trigger smooth `scrollIntoView({ block: 'nearest' })`, ensuring mobile software keyboards never occlude active form fields or the chat input.
- **Sticky Wizard Action Bar:** On small viewports, Next/Back actions stay anchored at the bottom of the screen with safe-area padding for effortless one-handed thumb interaction.

### 3. Small-Screen Component Polish
- **Horizontally Scrollable Tabs:** Result navigation uses CSS scroll-snap (`scroll-snap-type: x mandatory`) with hidden scrollbars, center-alignment on active tab selection, and full keyboard arrow navigation.
- **SVG Donut Chart:** Budget breakdown renders a scalable SVG donut chart with a center total label in compact INR (`₹10L`, `₹40K`), paired with a clean, stacked category legend below it.
- **Stacked Cards for Lists:** Vendor checklist items and timeline tasks convert from wide tables into touch-friendly cards with high-contrast priority chips and large 44px hit-box checkboxes.
- **Full-Width Chat Assistant:** Conversational drawer spans 100% width on mobile with max 85% speech bubbles, a pinned bottom input, and swipeable horizontal quick-suggestion chips.
- **Web Share API (`navigator.share`):** Action bar incorporates native system sharing for instant distribution to WhatsApp/Messages, with automatic fallback to Markdown file download.

### 4. Progressive Web App (PWA)
- **Manifest:** Configured with `display: standalone`, `theme_color`, and `background_color`.
- **Maskable Icons:** Generated high-resolution 192×192 and 512×512 maskable PNG icons (< 6 KB each, well below the 20 KB budget).
- **Dynamic Theme Color:** `<meta name="theme-color">` dynamically updates between dark (`#0A0A14`) and light (`#FFF7ED`) modes to match the browser address bar chrome.
- **System Fonts:** Pure system font stack eliminates external web font requests, zero render-blocking, and instant cold start.

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
- **Vector Assets (`public/assets/`):**
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
├── api/
│   ├── __init__.py
│   └── index.py                 # Vercel serverless ASGI entrypoint (FastAPI)
├── backend/
│   ├── __init__.py
│   ├── config.py                # Canonical BaseSettings configuration facade
│   ├── constants.py             # Centralized multipliers, benchmarks, calendar rules
│   ├── exceptions.py            # Custom domain exception hierarchy
│   ├── main.py                  # FastAPI app factory, CORS, static mounts & security headers
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py            # HTTP REST endpoints (/plan, /chat, /demos, /health)
│   ├── data/
│   │   ├── __init__.py
│   │   └── demos.py             # Curated demo scenarios
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic v2 domain schemas & input sanitizers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py        # Multi-provider LLM adapter, cache & offline fallback
│   │   ├── budget_engine.py     # Deterministic budget calculator (INR)
│   │   ├── chat_service.py      # Conversational assistant intent parsers & plan updater
│   │   ├── sanity_checks.py     # 8 cultural & weather validation checks
│   │   ├── timeline_engine.py   # Backward-planned timeline generator
│   │   └── vendor_engine.py     # Category vendor checklist generator
│   └── utils/
│       ├── __init__.py
│       └── config.py            # Backward-compatibility alias to backend.config
├── public/
│   ├── index.html               # Single-page app with brand meta & bilingual i18n
│   ├── manifest.webmanifest     # Web app manifest
│   ├── assets/
│   │   ├── logo.svg             # Light theme full logo
│   │   ├── logo-dark.svg        # Dark theme full logo
│   │   ├── icon.svg             # Square brand emblem
│   │   ├── icon-192.png         # 192x192 maskable PWA icon (< 20 KB)
│   │   ├── icon-512.png         # 512x512 maskable PWA icon (< 20 KB)
│   │   ├── favicon.svg          # 32x32 tab icon
│   │   ├── apple-touch-icon.png # 180x180 touch icon (< 20 KB)
│   │   ├── og-image.svg         # 1200x630 social preview card
│   │   └── icons/               # 10 category SVGs & sprite.svg
│   └── static/
│       ├── css/
│       │   ├── a11y.css         # High contrast focus-visible rings & screen reader styles
│       │   ├── base.css         # Reset, typography, and foundational CSS variables
│       │   ├── components.css   # Cards, tabs, badges, forms, and dialog styling
│       │   ├── layout.css       # Responsive grid, wizard steps, and containers
│       │   ├── responsive.css   # Viewport breakpoints (600px, 900px, 1200px)
│       │   ├── style.css        # Root entrypoint stylesheet
│       │   └── theme.css        # WCAG AA brand design tokens & dark/light palettes
│       └── js/
│           ├── api.js           # Async HTTP client wrapper for /api/v1/*
│           ├── app.js           # Backward-compatible ES module entrypoint
│           ├── chat.js          # Interactive chat assistant panel controller
│           ├── constants.js     # Default form values, sample data & endpoints
│           ├── dom.js           # Safe HTML escape, selectors & notification toasts
│           ├── export.js        # Markdown, JSON, and print export generation
│           ├── i18n.js          # English / Hindi translation dictionaries
│           ├── main.js          # Main orchestrator initializing wizard, tabs & events
│           ├── state.js         # Reactive central application state store
│           ├── theme.js         # Dark/light mode theme toggle & localStorage sync
│           └── render/
│               ├── budget.js    # Budget table, summary cards & SVG donut chart
│               ├── ideas.js     # AI personalized theme, menu & decor cards
│               ├── timeline.js  # Backward-planned milestone checklist
│               └── vendors.js   # Vendor categories, lead-times & questionnaires
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures & test client
│   ├── test_ai_service.py       # Mocked AI provider tests & fallback validation
│   ├── test_api_and_validators.py # API, schema, security, and sanity tests
│   ├── test_budget_engine.py    # Deterministic budget calculation tests
│   ├── test_chat_assistant.py   # Chat assistant engine re-run integration tests
│   ├── test_chat_service.py     # Pure unit tests for intent parsing & constants
│   ├── test_demo_scenarios.py   # Verification of all 3 demo scenarios
│   ├── test_frontend_static.py  # Viewport meta, asset integrity & PWA tests
│   ├── test_timeline_engine.py  # Backward planning timeline tests
│   └── test_vendor_engine.py    # Vendor checklist engine tests
├── docs/
│   ├── architecture.md          # In-depth system architecture, module layout & formulas
│   └── branding.md              # Brand identity guide & usage rules
├── .editorconfig                # Multi-language editor consistency
├── .env.example                 # Environment configuration template
├── .gitignore                   # Excludes caches, venv, and large files
├── .prettierrc                  # Frontend formatting guidelines
├── eslint.config.js             # Frontend lint configuration
├── mypy.ini                     # Static type checking rules
├── CONTRIBUTING.md              # Contributor onboarding & quality standards
├── Makefile                     # Developer targets (lint, format, typecheck, test, check)
├── pyproject.toml               # Pytest + coverage configuration
├── requirements.txt             # Minimal production runtime dependencies
├── requirements-dev.txt         # Development & test dependencies (pytest, ruff, mypy)
├── ruff.toml                    # Strict Ruff linter & formatter rules (E, F, I, B, UP, SIM, C90, N, D, ANN, PL)
├── vercel.json                  # Vercel routing & security headers config
└── README.md
```

---

## 🛠️ Developer Tooling & Verification

UtsavAI enforces modern code quality, formatting, and strict typing:

```bash
# Run all checks (linter, typechecker, full test suite)
make check

# Lint and auto-format
make lint
make format

# Static type checking
make typecheck

# Run test suite with coverage
make test
```

---

## 📊 Demo Scenarios

### 💍 Wedding in Delhi – ₹10 Lakh *(Top categories shown)*

| Category | Allocation | Amount |
|---|---|---|
| Catering | 28% | ₹2,52,000 |
| Venue | 22% | ₹1,98,000 |
| Photography | 13% | ₹1,17,000 |
| Decor & Florals | 10% | ₹90,000 |
| Makeup & Attire | 5% | ₹45,000 |
| Contingency | 10% | ₹1,00,000 |

### 🎂 Kid's Birthday in Mumbai – ₹40,000 *(Top categories shown)*

| Category | Allocation | Amount |
|---|---|---|
| Catering | 28% | ₹10,080 |
| Decor | 20% | ₹7,200 |
| Entertainment | 14% | ₹5,040 |
| Venue | 18% | ₹6,480 |
| Cake | 6% | ₹2,160 |
| Contingency | 10% | ₹4,000 |

### 🪔 Diwali Mela in Jaipur – ₹1.5 Lakh *(Top categories shown)*

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
8. **Serverless Execution (Vercel)**: When hosted on Vercel, API routes execute as ephemeral Python serverless functions. The client passes `previous_plan_context` during chat interactions so state is maintained statelessly across separate lambda invocations without relying on sticky server memory. In-memory caches and rate limits operate locally per lambda instance.

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
- [x] **Tests passing** (159 tests covering all engines, AI mocking, chat re-runs, pure intent parsers, Vercel entrypoint, and demo scenarios with 92% coverage)
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

*Made with ❤️ for India's celebrations. Jai Hind! 🇮🇳*

Built by MOHD UBES
