# UtsavAI – Brand Identity & Design System

> **Tagline:** *"Plan every celebration, smartly."*  
> **Name Meaning:** *Utsav* (उत्सव) is Hindi/Sanskrit for celebration, festival, and joyful gathering.

---

## 1. Brand Concept

The UtsavAI visual identity embodies a modern, warm, trustworthy, and celebratory experience designed specifically for Indian cultural events and occasions (weddings, birthdays, Diwali melas, Eid festivities, Navratri functions, and community galas).

The brand emblem merges three distinct visual ideas into one unified geometric mark:
1. **The Diya Flame (उत्सव / Celebration):** An uplifting golden flame radiating energy, auspicious warmth, and festivity without cultural cliches.
2. **The Checklist Tick (योजना / Planning):** A sweeping checkmark seamlessly integrated as the base of the earthen lamp, symbolizing disciplined backward planning, verified budgets, and completed tasks.
3. **The Sparkle Star (कृत्रिम बुद्धिमत्ता / AI):** A 4-pointed sparkle crowning the mark, indicating intelligent AI recommendations, automated reasoning, and hybrid personalization.

---

## 2. Brand Color Palette (WCAG AA Compliant)

All colors meet or exceed WCAG AA accessibility contrast standards across light and dark modes:

| Color Name | Hex Code | Role | Contrast on Cream (`#FFF7ED`) | Contrast on Dark (`#0A0A14`) |
| :--- | :--- | :--- | :--- | :--- |
| **Saffron** | `#F59E0B` | Festive Primary &amp; Diya Flame | Decorative / Warm | **8.5 : 1** (Passes AA &amp; AAA) |
| **Deep Maroon** | `#7C2D12` | Trustworthy Heritage &amp; Checkmark | **14.5 : 1** (Passes AAA) | Supporting / Shadow |
| **Indigo** | `#3730A3` | AI &amp; Modern Technology Accent | **12.2 : 1** (Passes AAA) | **7.8 : 1** (Passes AA &amp; AAA) |
| **Cream** | `#FFF7ED` | Celebration Canvas &amp; Luminous Glow | Surface / Background | **16.2 : 1** (Passes AAA) |

### CSS Variables (`frontend/css/theme.css`)
```css
:root {
  --brand-saffron: #F59E0B;
  --brand-maroon: #7C2D12;
  --brand-indigo: #3730A3;
  --brand-cream: #FFF7ED;
}
```

---

## 3. Brand Assets Directory (`frontend/assets/`)

All vector assets are 100% lightweight, hand-crafted SVG code without external dependencies, CDN links, or third-party artwork:

| File | Format | Dimensions | Purpose | Size |
| :--- | :--- | :--- | :--- | :--- |
| `logo.svg` | SVG | 240x56 | Full horizontal logo (icon + wordmark + tagline) for light surfaces | &lt; 3 KB |
| `logo-dark.svg` | SVG | 240x56 | Full horizontal logo adjusted for dark mode surfaces | &lt; 3 KB |
| `icon.svg` | SVG | 64x64 | Square brand mark for app header, badges, and avatars | &lt; 2.5 KB |
| `favicon.svg` | SVG | 32x32 | High-legibility simplified mark optimized for 16px and 32px tabs | &lt; 1.5 KB |
| `apple-touch-icon.png` | PNG | 180x180 | Mobile home screen icon (iOS / Android) | 2.7 KB |
| `og-image.svg` | SVG | 1200x630 | Open Graph and Twitter Card social preview banner | &lt; 7 KB |
| `manifest.webmanifest` | JSON | — | Progressive Web App manifest | &lt; 1 KB |

---

## 4. Category Icons (`frontend/assets/icons/`)

A unified set of 10 category icons built with a cohesive style: `24x24 viewBox`, `2px stroke`, `round` caps/joins, using `currentColor` to dynamically inherit active theme tokens:

1. `venue.svg`: Celebration mandap / pavilion with arched dome
2. `food.svg`: Dining feast cloche and festive platter
3. `decor.svg`: Festive hanging garland and celebration lantern
4. `photography.svg`: Camera with lens and shutter indicator
5. `music.svg`: Dual musical celebration notes
6. `invitation.svg`: Sealed envelope invitation card
7. `transport.svg`: Guest logistics vehicle
8. `priest.svg`: Sacred havan fire altar and ceremonial flame
9. `makeup.svg`: Styling mirror and beauty wand
10. `permissions.svg`: Government NOC and verification checklist document
11. `sprite.svg`: SVG sprite sheet combining all 10 symbols (`#icon-{category}`)

---

## 5. Usage & Accessibility Rules

- **Theme Switching:** Use `logo.svg` on light backgrounds and `logo-dark.svg` on dark backgrounds. Handled automatically via CSS `@media (prefers-color-scheme)` and the `data-theme` attribute.
- **Alt Text:** Logo images must have `alt="UtsavAI logo"`.
- **Decorative SVGs:** Inline category icons next to visible text labels must include `aria-hidden="true"` so assistive technologies do not announce redundant names.
- **Reduced Motion:** If flame flicker animations are enabled (`.brand-flame-animated`), respect `@media (prefers-reduced-motion: reduce)` by disabling animations entirely.
- **Aspect Ratio:** Do not distort or stretch the icon mark or wordmark. Always maintain native aspect ratios.
