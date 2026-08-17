# DeckForge — Presentation Builder

Build presentations from slide templates with `{{placeholders}}`, fill in the
data (or type straight into the slide), and present — all in the browser.

![stack](https://img.shields.io/badge/runtime-Python%20stdlib%20only-2ea44f)

## Quick start

Requires **Python 3.8+** — no other dependencies.

```bash
python server.py
# Open http://127.0.0.1:8420
```

On Windows you can also double-click **`start.bat`** (starts the server and
opens your browser). Use `python server.py --port 9000` to pick another port.

## Features

- **Decks of slides** — every presentation is a list of slides, each with its
  own template and data.
- **Insert slides with options** — the **Insert slide** button offers **Title**
  (large centered heading + subtitle), **Content** (heading + body), **Section**
  (dark chapter divider), **Exercise** (fill-in-the-blank placeholders) and
  **Blank** layouts, plus duplicate-the-current-slide.
- **Slide management** — click to select, drag on the strip to reorder, and the
  **⋯** menu renames, duplicates, moves left/right, or deletes a slide.
- **Scenario library (Available Simulations)** — a scenario-selection screen in
  the style of an INJECT-style simulation deck: two categories
  (**INFORMATION TECHNOLOGY** in cyan, **BUSINESS OPERATIONS** in amber) with
  scenario cards showing difficulty badges (INTERMEDIATE / ADVANCED), a
  description, and **Flowchart** (open in the editor) / **Start** (open and
  present) actions. Click **Simulations** in the sidebar to open it; it is the
  landing view on load.
- **Template engine** — `{{variable}}`, dotted paths (`{{client.address.city}}`),
  filters (`upper`, `money`, `date:%B %d, %Y`, `sum:amount`, `join:, `, …),
  conditional blocks (`{{#if x}}…{{else}}…{{/if}}`, `{{#unless}}`) and loops
  (`{{#each items}}` with `{{this}}`, `{{@index}}`, `{{@number}}`, …).
- **Markdown or HTML slide templates** — both render in the live preview and in
  the exported presentation.
- **Auto-generated data form** — every variable in the current slide becomes a
  form field; types are inferred (date, number, email, list→JSON).
- **Live preview** — updates as you type, inside a sandboxed iframe.
- **Fill-in-the-blanks preview** — toggle **Fill in** on the Preview tab to type
  values directly into the slide. Every variable becomes an underlined blank
  (computed values stay read-only), **+ Add item / − Last** grows and trims
  `{{#each}}` lists — ideal for classroom exercises.
- **Present** — fullscreen mode with ← → / Space navigation, a slide counter,
  progress bar, swipe support on touch devices, and `F` for fullscreen.
- **Export** — **Presentation (.html)**: a self-contained interactive slideshow
  that works anywhere; **Handout (.doc)**: every slide stacked with page breaks
  (open in Word, print, or save as PDF).
- **Import decks** — the sidebar **Import** button (or drag & drop a file onto
  the app) accepts `.json` deck bundles (`{name, slides}`), arrays, or
  `{decks: [...]}`, plus `.md` / `.txt` / `.html` (imported as a one-slide deck).
  Old DocForge template bundles (`{name, body, data}`) are imported as a
  single-slide deck.
- **Local storage** — decks persist to `data/decks.json` (the old
  `data/templates.json` is backed up as `.bak` on first run).
- Sixteen **Table Top Exercise** decks are seeded on first run, all aligned to
  **ISO/IEC 27001:2022** (Annex A controls) and **ISO/IEC 27002:2022**
  (implementation guidance): three BPO cyber-incident exercises
  (`exercises.py` — Ransomware at a BPO, Breach via Remote-Access Vendor,
  Insider Data Theft by an Agent) plus the thirteen-scenario INJECT catalog
  (`scenarios.py` — 8 × Information Technology and 5 × Business Operations,
  each with an INTERMEDIATE/ADVANCED difficulty). The Information Technology
  roster includes **Backup & Recovery DR Test** — a quarterly disaster-recovery
  exercise where a scheduled restore test exposes a corrupt backup set, a
  silent backup gap, and a blown recovery-time objective (aligned to A.8.13
  backup, A.8.16 monitoring, A.8.14 redundancy and A.5.30 ICT readiness). Every deck runs the classic
  exercise arc — objectives & ground rules, scenario background, roles,
  a three-inject timeline, decision points with discussion questions, an
  ISO/IEC 27001 clause map (Annex A controls with 27002 guidance), hotwash,
  and after-action review — plus an **After Action Executive Summary** slide
  (executive recap, exercise highlights, lessons learned, recommendations
  and a Corrective & Preventive Actions (CAPA) register) that every exercise
  deck carries. The executive summary follows the standard
  **executive-summary template** (based on the
  `EXECUTIVE_SUMMARY_CYBER_INTRUSION_03102026.docx` format): a full
  executive assessment with readiness score, capability assessment across
  five domains, framework alignment (SOC 2 / TISAX AL3 / ISO 27001-27002),
  priority recommendations, a typed CAPA action plan, a roadmap view, an
  audit-ready evidence pack, recommended executive KPIs, and executive
  decisions requested.
- **Integrated inject-slide exercises** — every exercise deck carries an
  `injects` timeline (time, title, detail per inject) stored on the deck, and
  the exercise lives *inside the deck itself*: each **Inject #N** slide shows
  an inline **Team Response — Critical decision point** box where the team
  records its decision, and the **Hotwash** / **After Action Executive
  Summary** slides render a log of all recorded responses. Present the deck
  (or the exported `.html`) to run the exercise — no separate runner.
  The **Add Inject** button in the editor appends a custom inject slide to
  the deck (persisted). Cyber-Intrusion uses the canonical inject chain
  (VPN anomaly detected 08:15 → new admin accounts 08:30 → logs disabled
  on the DC 08:45); every other scenario has a suggested inject chain in the
  same pattern.
- **Roles & participation picker** — every exercise deck's **Roles** slide
  lists the aligned role roster and an interactive picker to select which
  roles are participating. Information Technology decks carry eight roles
  (Corporate Security; IT Server & System Team; IT Desktop Team; IT Network
  Team; Compliance; Human Resources; Marketing; Executive Leadership), and
  Business Operations decks add **Team Leaders** and **Operations Manager &
  Director**. In Present mode, checking the boxes and confirming records the
  selection, which then appears in the Hotwash / After-Action response log.
- **After-Action Report (.doc)** — the Export menu on any deck with an After
  Action Executive Summary slide downloads a Word-ready executive summary in
  the standard 14-section template (title block, meta table, executive
  summary with assessment callout, readiness score, exercise highlights,
  capability assessment, key lessons learned, framework alignment summary,
  priority recommendations, executive action plan (CAPA), roadmap view,
  audit-ready evidence pack, recommended executive KPIs and executive
  decisions requested) as `After-Action-Report.doc`. The Simulations
  dashboard also shows an **AAR ↓** button on every scenario card that
  downloads that exercise's executive summary (.doc) directly.

## Syntax cheat sheet

| Syntax | Meaning |
|---|---|
| `{{name}}` | Insert a value (HTML-escaped in HTML output) |
| `{{{name}}}` / `{{&name}}` | Insert raw (unescaped) |
| `{{name | upper}}` | Filters: `upper lower title capitalize trim length default:x number money currency:€ date:%B %d, %Y join:, sum:amount json raw` |
| `{{#if field}}…{{else}}…{{/if}}` | Conditional section |
| `{{#unless field}}…{{/if}}` | Inverted conditional |
| `{{#each items}}…{{/each}}` | Loop; inside use `{{this}} {{@index}} {{@number}} {{@first}} {{@last}} {{@length}}` |
| `{{! comment }}` | Hidden comment |

Dates work best as ISO strings (`2026-08-05`) combined with the `date` filter.

## API

| Endpoint | Description |
|---|---|
| `GET /api/decks` | List decks (name, slide count, updated) |
| `GET /api/decks/:id` | Full deck (name, slides) |
| `POST /api/decks` | Create deck `{name, slides, injects?, meta?}` |
| `PUT /api/decks/:id` | Update deck (name and/or slides and/or injects/meta) |
| `DELETE /api/decks/:id` | Delete deck |
| `POST /api/render` | `{body, data, fill?}` → `{html, text, variables, errors}` — set `fill: true` to render editable blanks for the fill-in preview |
| `POST /api/export` | `{name, slides, format}` → file download (`presentation` \| `handout` \| `afteraction`) |

## Project layout

```
server.py       HTTP server (static files + JSON API)
renderer.py     template engine + markdown → HTML
store.py        JSON persistence (data/decks.json)
samples.py      seed decks (demo + tabletop exercises)
exercises.py    BPO cyber tabletop exercise decks (27001/27002)
scenarios.py    INJECT scenario catalog + deck generator
static/         frontend (index.html, style.css, app.js)
data/           created at runtime
```
