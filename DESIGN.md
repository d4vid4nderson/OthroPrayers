# DESIGN.md — Prayers for Morning, Day & Night

The design system of record for this app. Authored in the spirit of the
`impeccable` methodology and the DESIGN.md format. Build (`build.py`, `styles.css`)
follows this; when in doubt, this file wins.

Register: **product** (the design serves the prayers). The *reading* surfaces are
editorial/illuminated; the *chrome* (nav, settings, resource lists, tools) is
product UI and must "disappear into the task." Earned familiarity over novelty.

---

## 1. Visual theme & atmosphere

An Orthodox prayer book as a quiet, premium object — an illuminated liturgical
book, not a SaaS dashboard. Warm, calm, reverent, unhurried. Restraint is the
mood: generous whitespace, one accent doing real work, gold used sparingly like
gilding. Premium reads as *quietly luxurious and sacred*, never flashy.

North stars (the feel, not the styles): Notion's warm minimalism & serif
headings, Linear's precision & restraint, Apple's whitespace & calm.

---

## 2. Color palette & roles

Identity is committed; do not drift it. Add tints toward the brand hues, never
generic warm/cool.

### Light
| Token | Hex | Role |
|---|---|---|
| `--paper` | `#faf6ee` | page background (warm ivory) |
| `--surface` | `#fffdf8` | raised surfaces (cards, sheets) — a hair brighter than paper |
| `--surface-sunk` | `#f3ecdd` | wells (inputs, progress tracks, highlights) |
| `--ink` | `#231f20` | primary text |
| `--ink-soft` | `ink @ 72%` | secondary text / descriptions |
| `--rubric` | `#b3322a` | accent: rubrics, titles, drop-caps, active state |
| `--rubric-deep` | `#7c2b22` | secondary rubrication / inline directions |
| `--gold` | `#9a7b1e` | gilding: rules, badges, the camera FAB ring, accents |
| `--link` | `#1e5e9e` | inline prose links only (not UI chrome) |
| `--hairline` | `#e7ddc8` | borders, dividers |
| `--hairline-strong` | `#d9cdb0` | tab bar / section rules |

### Dark (warm-neutral charcoal, not brown)
| Token | Hex | Role |
|---|---|---|
| `--paper` | `#232327` | page background |
| `--surface` | `#27272c` | raised surfaces |
| `--surface-sunk` | `#1d1d21` | wells |
| `--ink` | `#e8e6e2` | primary text |
| `--rubric` | `#c83e2f` | accent (lifted for contrast on dark) |
| `--rubric-deep` | `#b3322a` | gilt-plaque red |
| `--gold` | `#d9b85e` | gilding |
| `--hairline` | `#3a3a40` | borders |
| `--hairline-strong` | `#43434a` | tab bar / section rules |

**Rules.** Accent (rubric) = rubrics, titles, current selection, state — never
decoration. Gold = gilding accents only, kept rare. Verify contrast: body ≥4.5:1,
large/UI ≥3:1. Don't use light-gray "elegant" body text on the tint; push toward ink.

---

## 3. Typography

A serif system — the illuminated identity earns it. Two families on a real
contrast axis (display vs. text), never two similar ones.

- **Display** `--display: "Cormorant"` — divider titles, cover, card/section titles. Weight 600. Letter-spacing ≥ -0.02em (never cramped).
- **Text** `--serif: "EB Garamond"` — body, prayers, UI labels, buttons, badges, list rows. Old-style figures + ligatures on.
- **A11y** `OpenDyslexic` replaces both when dyslexia mode is on (and small-caps/uppercase collapse to normal case).
- Display fonts **only** for titles/headings — never tiny labels, data, or controls (those stay EB Garamond / small-caps).

Scale (UI chrome is a fixed rem ramp; the prayer column keeps its own measure):
`--t-display clamp(1.9rem,7vw,2.5rem)` · `--t-h2 1.5rem` · `--t-h3 1.28rem` ·
`--t-lead 1.22rem` · `--t-body 1.165rem` · `--t-ui 1rem` · `--t-sm .92rem` · `--t-xs .78rem`.

Prose measure 65–75ch (the 544px book column). `text-wrap: balance` on headings.

---

## 4. Spacing, radius & layout

- **Spacing (4px base):** `--sp-1 .25` `--sp-2 .5` `--sp-3 .75` `--sp-4 1` `--sp-5 1.5` `--sp-6 2` `--sp-7 3` (rem). Vary spacing for rhythm; don't use one gap everywhere.
- **Radius:** `--r-sm 8px` (buttons) · `--r-md 12px` (cards/sheets) · `--r-lg 16px` (large sheets) · `--r-pill 999px` (chips). Cards top out at 16px — never 24px+. The 2px icon-plate frame is a deliberate exception.
- **App shell:** body is a flex column at `100dvh`, `overflow:hidden`; `.scroll` is the only scroller; the tab bar is a fixed-height flex child. Keep `env(safe-area-inset-bottom)` with `max()` floors. Do not change.
- Flexbox for 1-D, Grid for 2-D. Responsive grids: `repeat(auto-fit, minmax(15rem,1fr))`.

---

## 5. Depth & elevation

Warm-tinted shadows in light (matching the page's brown shadow), low-alpha black in dark. Cards lift *just* off the page. **Never** pair a 1px border with a ≥16px shadow on the same element (ghost-card) — pick one.

```
--elev-1: 0 1px 2px rgba(60,40,20,.06), 0 1px 3px rgba(60,40,20,.08);   /* resting card */
--elev-2: 0 4px 10px rgba(60,40,20,.10), 0 2px 4px rgba(60,40,20,.07);  /* hover */
--elev-3: 0 12px 32px rgba(60,40,20,.16);                               /* sheets, FAB */
/* dark: rgba(0,0,0,.3) / .4 / .55 */
```
Surfaces: page `--paper` < card `--surface` < (sheet `--surface` + `--elev-3`). Wells use `--surface-sunk`, never a shadow.

---

## 6. Components

Every interactive element ships all states: default, hover, focus-visible, active, disabled, (loading/selected where relevant). Consistent vocabulary across every screen.

- **Buttons / CTAs:** filled = `--rubric` bg, paper text; ghost = `--rubric` text + 1px `--rubric` border. `--r-sm`. `:active{ transform:scale(.985) }`. No border+heavy-shadow.
- **Cards** (`res-card`, hub destinations): `--surface`, 1px `--hairline`, `--r-md`, `--elev-1` → `--elev-2`+`--hairline:gold` on hover. Title (display 600), description (`--ink-soft`), optional gilt emblem. Used **only** for genuine destinations — cards are the lazy answer; don't card every list.
- **List rows** (`link-card`, link lists): full-width row, `--hairline` divider or `--surface` card, title (serif 600 `--ink`) + description (`--ink-soft`) + external "host ↗" affordance + gold-outline "free" badge + chevron. **No blue link color**; ink title with gilt hover.
- **Tab bar:** fixed-height (~3.6rem) flex; small-caps labels `--t-xs`; active = rubric icon + a centered gilt ribbon (`::before`, `--r-pill`); top hairline `--hairline-strong`; modest blur only.
- **Camera FAB:** raised rubric circle, paper ring + a 1px gold rim, `--elev-3` (warm), `:active` press. The brand's hero — the one place gold rims red.
- **Sheets** (Settings only): bottom sheet, `--surface`, `--r-lg` top, `--elev-3`, grab handle, swipe/backdrop/Esc to dismiss. Reserve sheets for short, transient panels — never primary navigation menus.
- **Badges / pills:** small-caps; "free" = gold **outline** (not solid red); "Ancient Faith" = gold fill, dark text.
- **Inputs:** `--surface-sunk`, 1px `--hairline`, `--r-sm`, focus ring. Native controls; don't reinvent.
- **Checklist rows** (Fathers): grouped per era in a section card; large (44px) hit target; `accent-color: --rubric`; read/listen as gold-outline action chips, not blue links.

---

## 7. Motion

Product cadence: 150–250ms, ease-out (quart/expo), no bounce. Motion conveys
**state** (press, hover, sheet, loading, reveal) — never decoration. No orchestrated
page-load sequences. Press feedback = `scale(.985)` + shadow settle. Every animation
honors `@media (prefers-reduced-motion: reduce)`.

---

## 8. Do's & don'ts

**Do:** keep the reading column sacred and untouched; one accent + gilding; full
borders / bg tints / leading emblems for emphasis; real states & focus rings;
skeletons for loading; empty states that teach.

**Don't (hard bans):** side-stripe accent borders (`border-left/right` >1px as
decoration); gradient text (`background-clip:text`); glassmorphism as default;
identical icon+title+text card grids repeated endlessly; tiny tracked uppercase
eyebrows over every section; border + ≥16px shadow on one element; radii ≥24px on
cards; display fonts in labels/buttons/data; modal/sheet as first thought for
navigation; blue links in UI chrome.

---

## 9. Responsive · a11y · safe-areas

- Mobile-first; structural responsiveness (not fluid type). ≥640px: the book is a bound leaf on the desk.
- Touch targets ≥44px. Tab bar + FAB respect `env(safe-area-inset-bottom)`; standalone PWA adds room above the home indicator.
- Contrast verified in **both** themes. `:focus-visible` ring on every interactive element. Honor reduced-motion. Dyslexia + text-size modes must keep every layout intact.
- Offline service worker must keep working; no external fonts/CDNs/images in core UI (the Greek tool's external calls are the one isolated exception).
