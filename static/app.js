/* ============================================================
   DeckForge — frontend application
   ============================================================ */
'use strict';

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

const state = {
  decks: [],
  deckId: null,
  name: '',
  slides: [],
  currentSlide: 0,
  variables: [],
  formVariables: [],
  loopVariables: [],
  mode: 'form',          // 'form' | 'json'
  dirty: false,
  renderTimer: null,
  saveTimer: null,
  search: '',
  previewHtml: '',
  fillMode: (() => { try { return localStorage.getItem('deckforge.fillMode') === '1'; } catch { return false; } })(),
  injects: [],
  meta: null,
};

const els = {};
const IDS = ['deck-name', 'deck-list', 'btn-new', 'search', 'btn-help', 'btn-help-close',
  'help-modal', 'empty-state', 'workspace', 'editor', 'editor-hl', 'editor-code', 'editor-wrap',
  'insert-var', 'insert-block', 'preview', 'tab-preview', 'tab-data', 'btn-form', 'btn-json',
  'json-editor', 'json-error', 'form-wrap', 'btn-reset-data', 'btn-print', 'btn-export',
  'export-menu', 'save-state', 'err-pill', 'var-count', 'gutter', 'toast', 'deck-count',
  'btn-empty-new', 'btn-empty-sample', 'empty-decks', 'editor-pane', 'right-pane',
  'btn-import', 'file-import', 'deck-menu', 'btn-preview-mode', 'btn-fill-mode',
  'fill-wrap', 'preview-fill', 'btn-insert-slide', 'slide-strip', 'slide-menu',
  'btn-present', 'present-overlay', 'present-frame', 'btn-exit-present', 'deck-bar', 'slide-count',
  'btn-simulations', 'btn-dashboard', 'scenario-lib', 'scenario-cats', 'btn-add-inject'];
for (const id of IDS) els[id.replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = document.getElementById(id);

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const uid = () => (window.crypto && crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2, 12));

/* ============================================================
   API
   ============================================================ */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  const ct = res.headers.get('Content-Type') || '';
  const data = ct.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) throw new Error(typeof data === 'object' ? (data.error || res.statusText) : data);
  return data;
}

/* ============================================================
   Init
   ============================================================ */
async function init() {
  bindEvents();
  applyFillModeUi();
  try {
    await reloadDecks();
    if (state.decks.length) showLibrary();
  } catch (e) {
    showToast('Could not reach the server: ' + e.message, true);
  }
}

function applyFillModeUi() {
  els.btnPreviewMode.classList.toggle('active', !state.fillMode);
  els.btnFillMode.classList.toggle('active', state.fillMode);
  els.preview.hidden = state.fillMode;
  els.fillWrap.hidden = !state.fillMode;
}

function setFillMode(on) {
  if (state.fillMode === on) return;
  state.fillMode = on;
  try { localStorage.setItem('deckforge.fillMode', on ? '1' : '0'); } catch { /* ignore */ }
  applyFillModeUi();
  refreshRender();
}

/* ============================================================
   Scenario library (Available Simulations)
   ============================================================ */
const SCENARIOS = [
  { title: 'Cyber-Intrusion', cat: 'IT', diff: 'INTERMEDIATE', desc: 'Active Directory compromise via VPN with shadow admin accounts and disabled logging.' },
  { title: 'Data Loss', cat: 'IT', diff: 'INTERMEDIATE', desc: 'Sensitive customer data exposed via misconfigured cloud storage permissions.' },
  { title: 'Ransomware', cat: 'IT', diff: 'ADVANCED', desc: 'Mass encryption attack with backup integrity concerns and ransom demand.' },
  { title: 'Denial of Service', cat: 'IT', diff: 'INTERMEDIATE', desc: 'DDoS attack targeting public-facing infrastructure causing service degradation.' },
  { title: 'Insider Threat', cat: 'IT', diff: 'ADVANCED', desc: 'Disgruntled employee attempts to exfiltrate proprietary data and disrupt operations.' },
  { title: 'Compromised Credentials', cat: 'IT', diff: 'INTERMEDIATE', desc: 'Multiple user credentials leaked in dark web forum enabling lateral movement.' },
  { title: 'Cyberattack on CRM System', cat: 'IT', diff: 'ADVANCED', desc: 'CRM system used for client interactions is compromised, exposing sensitive customer data.' },
  { title: 'Backup & Recovery DR Test', cat: 'IT', diff: 'ADVANCED', desc: 'A scheduled disaster-recovery test exposes a corrupt backup set, a silent backup gap, and a blown recovery-time objective.' },
  { title: 'Network Outage Affecting Global Connectivity', cat: 'BO', diff: 'INTERMEDIATE', desc: 'Critical network failure disrupts connectivity between BPO center and client systems globally.' },
  { title: 'Fire at Secondary Site During Peak Hours', cat: 'BO', diff: 'ADVANCED', desc: 'Fire breaks out at secondary BPO site during peak operational hours, forcing evacuation and shutdown.' },
  { title: 'Complete Power Outage at HQ', cat: 'BO', diff: 'ADVANCED', desc: 'Sudden power outage at primary BPO delivery center affecting all workstations and servers. Backup generators fail to start.' },
  { title: 'Geopolitic Concerns Reducing Workforce Availability', cat: 'BO', diff: 'ADVANCED', desc: 'Sudden pandemic wave results in 60% absenteeism among BPO staff, impacting service delivery.' },
  { title: 'Vishing Attack', cat: 'BO', diff: 'INTERMEDIATE', desc: 'Attackers impersonate executives and IT support via spoofed phone calls to harvest credentials and authorize a fraudulent wire transfer.' },
];

const CAT_META = {
  IT: { label: 'INFORMATION TECHNOLOGY', cls: 'cat-it', icon: `<svg viewBox="0 0 16 16" width="15" height="15"><path d="M8 1.5l5 2v4c0 3.2-2.1 5.7-5 7-2.9-1.3-5-3.8-5-7v-4z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M5.6 8l1.7 1.7 3-3.4" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
  BO: { label: 'BUSINESS OPERATIONS', cls: 'cat-bo', icon: `<svg viewBox="0 0 16 16" width="15" height="15"><path d="M1.5 8h3l2-5 3 9 2-4h3" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
};

function scenarioDeckName(title) {
  return 'Table Top Exercise · ' + title;
}

function renderLibrary() {
  const cats = {};
  for (const s of SCENARIOS) (cats[s.cat] = cats[s.cat] || []).push(s);
  els.scenarioCats.innerHTML = Object.keys(CAT_META).map((key) => {
    const meta = CAT_META[key];
    const cards = (cats[key] || []).map((s) => `
      <div class="scenario-card" data-title="${esc(s.title)}">
        <div class="sc-card-head">
          <span class="sc-icon">${meta.icon}</span>
          <span class="sc-diff ${s.diff === 'ADVANCED' ? 'advanced' : 'intermediate'}">${s.diff}</span>
        </div>
        <h3>${esc(s.title)}</h3>
        <p class="sc-desc">${esc(s.desc)}</p>
        <div class="sc-actions">
          <button class="btn ghost small" data-act="flowchart">Flowchart</button>
          <button class="btn ghost small" data-act="aar" title="Download this exercise's After Action Executive Summary (.doc)">AAR ↓</button>
          <button class="btn primary small" data-act="start">Start</button>
        </div>
      </div>`).join('');
    return `<section class="scenario-cat ${meta.cls}">
      <div class="cat-head"><span class="cat-bar"></span><span class="cat-title">${meta.label}</span></div>
      <div class="scenario-grid">${cards}</div>
    </section>`;
  }).join('');
}

function showLibrary() {
  els.emptyState.hidden = true;
  els.workspace.hidden = true;
  els.deckBar.hidden = true;
  els.scenarioLib.hidden = false;
  els.btnSimulations.classList.add('active');
  els.btnDashboard.classList.remove('active');
  renderLibrary();
}

function showDeckView() {
  els.scenarioLib.hidden = true;
  els.btnSimulations.classList.remove('active');
  els.btnDashboard.classList.add('active');
}

async function downloadAfterAction(deck) {
  try {
    let full = deck;
    if (!full.slides) full = await api('/api/decks/' + deck.id);
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: full.name, slides: full.slides, format: 'afteraction',
                             injects: full.injects, meta: full.meta }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || res.statusText);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = slug(full.name) + '-executive-summary.doc';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Executive summary downloaded: ' + slug(deck.name));
  } catch (e) {
    showToast('Download failed: ' + e.message, true);
  }
}

function runScenario(act, title) {
  const deck = state.decks.find((d) => d.name === scenarioDeckName(title));
  if (!deck) {
    showToast('Scenario deck not loaded — refresh the page', true);
    return;
  }
  if (act === 'aar') {
    downloadAfterAction(deck);
    return;
  }
  selectDeck(deck.id).then(() => {
    if (act === 'start') {
      openPresent();
      showToast('Exercise started: ' + deck.name);
    }
  });
}

function renderEmptyDecks() {
  els.emptyDecks.innerHTML = state.decks.length
    ? state.decks
        .map((d) => `<button class="sample-chip" data-id="${d.id}">${esc(d.name)}</button>`)
        .join('')
    : '';
}

async function reloadDecks() {
  state.decks = await api('/api/decks');
  renderDecks();
  renderEmptyDecks();
  if (!state.decks.length) showEmpty(true);
}

/* ============================================================
   Sidebar
   ============================================================ */
function renderDecks() {
  const q = state.search.toLowerCase();
  const list = state.decks.filter((d) => d.name.toLowerCase().includes(q));
  els.deckList.innerHTML = list.length
    ? list.map((d) => `
      <div class="deck-item ${d.id === state.deckId ? 'active' : ''}" data-id="${d.id}" role="button" tabindex="0">
        <span class="deck-name">${esc(d.name)}</span>
        <span class="deck-meta">
          <span class="deck-slides">${d.slide_count} ${d.slide_count === 1 ? 'slide' : 'slides'}</span>
          <span class="deck-date">${fmtDate(d.updated)}</span>
        </span>
        <span class="deck-more" title="More actions" data-more="${d.id}">⋯</span>
        <span class="deck-del" title="Delete deck" data-del="${d.id}">✕</span>
      </div>`).join('')
    : `<div class="side-empty">${q ? 'No decks match “' + esc(q) + '”' : 'No decks yet'}</div>`;
  els.deckCount.textContent = state.decks.length === 1
    ? '1 deck' : state.decks.length + ' decks';
}

function fmtDate(iso) {
  if (!iso) return '';
  const d = new Date(iso.length === 10 ? iso + 'T00:00:00' : iso);
  if (isNaN(d)) return '';
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function showEmpty(on) {
  els.emptyState.hidden = !on;
  els.workspace.hidden = on;
  els.deckBar.hidden = on;
  els.scenarioLib.hidden = true;
  els.btnSimulations.classList.remove('active');
  els.btnDashboard.classList.remove('active');
  els.deckName.value = '';
  els.errPill.hidden = true;
  if (on) {
    els.saveState.textContent = '';
    els.saveState.className = 'save-state';
    els.preview.srcdoc = '';
    els.previewFill.innerHTML = '';
    els.formWrap.innerHTML = '';
    els.varCount.textContent = '';
    els.slideStrip.innerHTML = '';
    els.slideCount.textContent = '';
  }
}

function cur() {
  return state.slides[state.currentSlide] || null;
}

async function selectDeck(id) {
  let deck;
  try {
    deck = await api('/api/decks/' + id);
  } catch (e) {
    showToast('Could not load deck: ' + e.message, true);
    return;
  }
  showDeckView();
  state.deckId = id;
  state.name = deck.name;
  state.slides = Array.isArray(deck.slides) ? deck.slides : [];
  state.injects = Array.isArray(deck.injects) ? deck.injects : [];
  state.meta = deck.meta || null;
  els.btnAddInject.hidden = !state.injects.length;
  state.currentSlide = 0;
  state.dirty = false;
  els.deckName.value = deck.name;
  els.emptyState.hidden = true;
  els.workspace.hidden = false;
  els.deckBar.hidden = false;
  els.saveState.textContent = '';
  els.saveState.className = 'save-state';
  renderDecks();
  renderStrip();
  updateSlideCount();
  if (state.slides.length) {
    selectSlide(0);
  } else {
    els.editor.value = '';
    els.jsonEditor.value = '{}';
    els.formWrap.innerHTML = '';
    els.preview.srcdoc = '';
    els.previewFill.innerHTML = '';
    els.varCount.textContent = '';
    updateHighlight();
  }
}

async function createDeck() {
  try {
    const deck = await api('/api/decks', {
      method: 'POST',
      body: JSON.stringify({ name: 'Untitled presentation', slides: [] }),
    });
    state.decks.unshift({ id: deck.id, name: deck.name, updated: deck.updated, slide_count: 0 });
    renderDecks();
    await selectDeck(deck.id);
    insertSlide('title');
    els.editor.focus();
    showToast('Deck created — start adding slides');
  } catch (e) {
    showToast('Could not create deck: ' + e.message, true);
  }
}

async function deleteDeck(id) {
  const deck = state.decks.find((d) => d.id === id);
  if (!deck) return;
  if (!confirm(`Delete presentation “${deck.name}”? This cannot be undone.`)) return;
  try {
    await api('/api/decks/' + id, { method: 'DELETE' });
    state.decks = state.decks.filter((d) => d.id !== id);
    if (state.deckId === id) {
      state.deckId = null;
      if (state.decks.length) selectDeck(state.decks[0].id);
      else showEmpty(true);
    }
    renderDecks();
    renderEmptyDecks();
    showToast('Deck deleted');
  } catch (e) {
    showToast('Could not delete deck: ' + e.message, true);
  }
}

/* ============================================================
   Import decks
   ============================================================ */
async function importDecks(fileList) {
  const file = fileList && fileList[0];
  if (!file) return;
  const ext = (file.name.split('.').pop() || '').toLowerCase();
  const baseName = file.name.replace(/\.[^.]+$/, '') || 'Imported deck';
  const text = await file.text();
  const created = [];
  try {
    if (ext === 'json') {
      const parsed = JSON.parse(text);
      const list = Array.isArray(parsed) ? parsed
        : parsed && Array.isArray(parsed.decks) ? parsed.decks
        : [parsed];
      for (const d of list) {
        if (!d || typeof d !== 'object') continue;
        if (typeof d.name !== 'string' && !Array.isArray(d.slides)) continue;
        let slides = Array.isArray(d.slides) ? d.slides : [];
        // accept old DocForge template bundles as a single-slide deck
        if (!slides.length && typeof d.body === 'string') {
          slides = [{ name: 'Slide 1', layout: 'content', body: d.body, data: d.data || {} }];
        }
        slides = slides
          .filter((s) => s && typeof s === 'object')
          .map((s) => ({
            id: uid(),
            name: String(s.name || 'Slide'),
            layout: ['title', 'content', 'section', 'blank'].includes(s.layout) ? s.layout : 'content',
            body: typeof s.body === 'string' ? s.body : '',
            data: s.data && typeof s.data === 'object' ? s.data : {},
          }));
        const deck = await api('/api/decks', {
          method: 'POST',
          body: JSON.stringify({ name: (d.name || baseName).trim() || baseName, slides }),
        });
        created.push(deck.id);
      }
      if (!created.length) {
        showToast('No decks found in that JSON file.', true);
        return;
      }
    } else {
      // .md / .txt / .html — a new deck from the file contents (one slide)
      const deck = await api('/api/decks', {
        method: 'POST',
        body: JSON.stringify({
          name: baseName,
          slides: [{ id: uid(), name: 'Slide 1', layout: 'content', body: text, data: {} }],
        }),
      });
      created.push(deck.id);
    }
    await reloadDecks();
    if (created.length) await selectDeck(created[0]);
    showToast('Imported ' + created.length + ' deck' + (created.length > 1 ? 's' : ''));
  } catch (e) {
    showToast('Import failed: ' + e.message, true);
  } finally {
    els.fileImport.value = ''; // allow re-importing the same file
  }
}

/* ============================================================
   Per-deck actions (⋯ menu)
   ============================================================ */
let deckMenuFor = null;

function openDeckMenu(id, x, y) {
  const deck = state.decks.find((d) => d.id === id);
  if (!deck) return;
  els.deckMenu.innerHTML = `
    <div class="menu-head">${esc(deck.name)}</div>
    <button class="menu-item" data-act="open">Open</button>
    <button class="menu-item" data-act="rename">✎ Rename</button>
    <button class="menu-item" data-act="duplicate">⧉ Duplicate</button>
    <button class="menu-item" data-act="download">↓ Download (.json)</button>
    <div class="menu-sep"></div>
    <button class="menu-item danger" data-act="delete">✕ Delete</button>`;
  els.deckMenu.hidden = false;
  deckMenuFor = id;
  const rect = els.deckMenu.getBoundingClientRect();
  els.deckMenu.style.left = Math.max(8, Math.min(x, window.innerWidth - rect.width - 8)) + 'px';
  els.deckMenu.style.top = Math.max(8, Math.min(y, window.innerHeight - rect.height - 8)) + 'px';
}

function closeDeckMenu() {
  els.deckMenu.hidden = true;
  deckMenuFor = null;
}

async function renameDeck(id) {
  const deck = state.decks.find((d) => d.id === id);
  if (!deck) return;
  const name = prompt('Rename presentation:', deck.name);
  if (name === null) return;
  const trimmed = name.trim();
  if (!trimmed) {
    showToast('Name cannot be empty.', true);
    return;
  }
  if (trimmed === deck.name) return;
  try {
    await api('/api/decks/' + id, { method: 'PUT', body: JSON.stringify({ name: trimmed }) });
    if (state.deckId === id) {
      state.name = trimmed;
      els.deckName.value = trimmed;
    }
    await reloadDecks();
    showToast('Renamed to “' + trimmed + '”');
  } catch (e) {
    showToast('Rename failed: ' + e.message, true);
  }
}

async function duplicateDeck(id) {
  try {
    const deck = await api('/api/decks/' + id);
    const created = await api('/api/decks', {
      method: 'POST',
      body: JSON.stringify({
        name: deck.name + ' (copy)',
        slides: deck.slides.map((s) => ({ ...s, id: uid() })),
      }),
    });
    await reloadDecks();
    await selectDeck(created.id);
    showToast('Duplicated “' + deck.name + '”');
  } catch (e) {
    showToast('Duplicate failed: ' + e.message, true);
  }
}

async function downloadDeck(id) {
  try {
    const deck = await api('/api/decks/' + id);
    const blob = new Blob(
      [JSON.stringify({ name: deck.name, slides: deck.slides }, null, 2)],
      { type: 'application/json' },
    );
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = slug(deck.name) + '.deck.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Downloaded ' + slug(deck.name) + '.deck.json');
  } catch (e) {
    showToast('Download failed: ' + e.message, true);
  }
}

/* ============================================================
   Slides — strip, insert, reorder
   ============================================================ */
const LAYOUT_LABEL = { title: 'Title', content: 'Content', section: 'Section', blank: 'Blank', exercise: 'Exercise' };

const SLIDE_TEMPLATES = {
  title: {
    name: 'Title slide', layout: 'title',
    body: '# {{title}}\n\n{{subtitle | default:"Add a subtitle"}}',
    data: { title: 'Presentation title', subtitle: '' },
  },
  content: {
    name: 'Content slide', layout: 'content',
    body: '## {{heading}}\n\n- First point\n- Second point\n- Third point',
    data: { heading: 'Section title' },
  },
  section: {
    name: 'Section divider', layout: 'section',
    body: '# {{heading}}',
    data: { heading: 'New section' },
  },
  exercise: {
    name: 'Exercise slide', layout: 'exercise',
    body: '## {{heading}}\n\n{{question}}\n\nAnswer: {{answer}}',
    data: { heading: 'Practice exercise', question: 'Write the question here', answer: 'Write the answer here' },
  },
  blank: {
    name: 'Blank slide', layout: 'blank',
    body: '<!-- Blank slide — add your content -->',
    data: {},
  },
};

function renderStrip() {
  const idx = state.currentSlide;
  els.slideStrip.innerHTML = state.slides.length
    ? state.slides.map((s, i) => `
      <div class="slide-card ${i === idx ? 'active' : ''}" data-idx="${i}" draggable="true" title="Slide ${i + 1}">
        <span class="slide-idx">${i + 1}</span>
        <span class="slide-name">${esc(s.name || 'Slide')}</span>
        <span class="slide-layout lay-${esc(s.layout || 'content')}">${LAYOUT_LABEL[s.layout] || 'Content'}</span>
        <span class="slide-more" data-more="${i}">⋯</span>
      </div>`).join('')
    : `<div class="side-empty" style="padding:8px 12px">No slides yet — hit “Insert slide”.</div>`;
}

function updateSlideCount() {
  els.slideCount.textContent = state.slides.length === 1
    ? '1 slide' : state.slides.length + ' slides';
}

function selectSlide(i) {
  if (i < 0 || i >= state.slides.length) return;
  state.currentSlide = i;
  const sl = cur();
  els.editor.value = sl.body || '';
  els.jsonEditor.value = JSON.stringify(sl.data || {}, null, 2);
  renderStrip();
  updateSlideCount();
  updateHighlight();
  buildForm();
  refreshRender();
}

function insertSlide(layout) {
  const t = SLIDE_TEMPLATES[layout] || SLIDE_TEMPLATES.content;
  const sl = {
    id: uid(),
    name: t.name,
    layout: t.layout,
    body: t.body,
    data: JSON.parse(JSON.stringify(t.data)),
  };
  state.slides.splice(state.currentSlide + 1, 0, sl);
  const newIdx = Math.min(state.currentSlide + 1, state.slides.length - 1);
  state.dirty = true;
  selectSlide(newIdx);
  els.editor.focus();
  scheduleSave();
  showToast(t.name + ' added');
}

function duplicateSlide(i) {
  const src = state.slides[i];
  if (!src) return;
  const copy = {
    id: uid(),
    name: src.name + ' (copy)',
    layout: src.layout,
    body: src.body,
    data: JSON.parse(JSON.stringify(src.data || {})),
  };
  state.slides.splice(i + 1, 0, copy);
  state.dirty = true;
  selectSlide(Math.min(i + 1, state.slides.length - 1));
  scheduleSave();
  showToast('Slide duplicated');
}

function deleteSlide(i) {
  if (!state.slides.length) return;
  if (!confirm(`Delete slide “${state.slides[i].name || 'Slide ' + (i + 1)}”?`)) return;
  state.slides.splice(i, 1);
  state.currentSlide = Math.max(0, Math.min(state.currentSlide, state.slides.length - 1));
  state.dirty = true;
  if (state.slides.length) {
    selectSlide(state.currentSlide);
  } else {
    els.editor.value = '';
    els.jsonEditor.value = '{}';
    els.formWrap.innerHTML = '';
    els.preview.srcdoc = '';
    els.previewFill.innerHTML = '';
    els.varCount.textContent = '';
    renderStrip();
    updateSlideCount();
    updateHighlight();
  }
  scheduleSave();
  showToast('Slide deleted');
}

function moveSlide(i, dir) {
  const j = i + dir;
  if (j < 0 || j >= state.slides.length) return;
  const [m] = state.slides.splice(i, 1);
  state.slides.splice(j, 0, m);
  state.currentSlide = j;
  state.dirty = true;
  selectSlide(j);
  scheduleSave();
}

function renameSlide(i) {
  const sl = state.slides[i];
  if (!sl) return;
  const name = prompt('Rename slide:', sl.name || '');
  if (name === null) return;
  sl.name = name.trim() || 'Slide';
  state.dirty = true;
  renderStrip();
  scheduleSave();
}

let slideMenuFor = null;

function openSlideMenu(i, x, y) {
  const sl = state.slides[i];
  if (!sl) return;
  els.slideMenu.innerHTML = `
    <div class="menu-head">Slide ${i + 1} · ${esc(sl.name || '')}</div>
    <button class="menu-item" data-act="rename">✎ Rename</button>
    <button class="menu-item" data-act="duplicate">⧉ Duplicate</button>
    <button class="menu-item" data-act="left" ${i === 0 ? 'disabled style="opacity:.4"' : ''}>← Move left</button>
    <button class="menu-item" data-act="right" ${i === state.slides.length - 1 ? 'disabled style="opacity:.4"' : ''}>Move right →</button>
    <div class="menu-sep"></div>
    <button class="menu-item danger" data-act="delete">✕ Delete</button>`;
  els.slideMenu.hidden = false;
  slideMenuFor = i;
  const rect = els.slideMenu.getBoundingClientRect();
  els.slideMenu.style.left = Math.max(8, Math.min(x, window.innerWidth - rect.width - 8)) + 'px';
  els.slideMenu.style.top = Math.max(8, Math.min(y, window.innerHeight - rect.height - 8)) + 'px';
}

function closeSlideMenu() {
  els.slideMenu.hidden = true;
  slideMenuFor = null;
}

function openInsertMenu() {
  slideMenuFor = null; // the insert menu is not attached to a specific slide
  els.slideMenu.innerHTML = `
    <div class="menu-head">Insert slide after</div>
    <button class="menu-item" data-layout="title"><span class="badge md">T</span><span>Title slide<span class="mi-desc">Large heading + subtitle</span></span></button>
    <button class="menu-item" data-layout="content"><span class="badge doc">C</span><span>Content slide<span class="mi-desc">Heading + body / bullets</span></span></button>
    <button class="menu-item" data-layout="section"><span class="badge txt">S</span><span>Section divider<span class="mi-desc">Dark chapter break</span></span></button>
    <button class="menu-item" data-layout="exercise"><span class="badge html">E</span><span>Exercise slide<span class="mi-desc">Fill-in-the-blank placeholders</span></span></button>
    <button class="menu-item" data-layout="blank"><span class="badge txt">B</span><span>Blank slide<span class="mi-desc">Empty canvas</span></span></button>
    <div class="menu-sep"></div>
    <button class="menu-item" data-act="duplicate">⧉ Duplicate current slide</button>`;
  els.slideMenu.hidden = false;
  const btn = els.btnInsertSlide.getBoundingClientRect();
  const rect = els.slideMenu.getBoundingClientRect();
  els.slideMenu.style.left = Math.max(8, Math.min(btn.left, window.innerWidth - rect.width - 8)) + 'px';
  els.slideMenu.style.top = Math.min(btn.bottom + 8, window.innerHeight - rect.height - 8) + 'px';
}

/* drag-and-drop reorder */
let dragIdx = null;

function initSlideDnd() {
  els.slideStrip.addEventListener('dragstart', (e) => {
    const card = e.target.closest('.slide-card');
    if (!card) return;
    dragIdx = +card.dataset.idx;
    e.dataTransfer.effectAllowed = 'move';
    card.classList.add('dragging');
  });
  els.slideStrip.addEventListener('dragover', (e) => {
    const card = e.target.closest('.slide-card');
    if (!card || dragIdx == null) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const over = +card.dataset.idx;
    if (over === dragIdx) return;
    const [m] = state.slides.splice(dragIdx, 1);
    state.slides.splice(over, 0, m);
    if (state.currentSlide === dragIdx) state.currentSlide = over;
    else if (dragIdx < state.currentSlide && over >= state.currentSlide) state.currentSlide--;
    else if (dragIdx > state.currentSlide && over <= state.currentSlide) state.currentSlide++;
    dragIdx = over;
    state.dirty = true;
    scheduleSave();
    renderStrip();
  });
  els.slideStrip.addEventListener('dragend', () => {
    dragIdx = null;
    renderStrip();
  });
}

/* ============================================================
   Editor highlight overlay
   ============================================================ */
const TOKEN_RE = /(\{\{\{.*?\}\}\}|\{\{.*?\}\})/g;

function isBlockToken(m) {
  return m.startsWith('{{#') || m.startsWith('{{/') || m.startsWith('{{!') || m === '{{else}}';
}

function updateHighlight() {
  const body = els.editor.value;
  const hl = body
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(TOKEN_RE, (m) => `<span class="${isBlockToken(m) ? 'tok-block' : 'tok'}">${m}</span>`)
    .replace(/\n$/, '\n ');
  els.editorCode.innerHTML = hl || '<span class="ph">Start typing…</span>';
  syncScroll();
}

function syncScroll() {
  els.editorHl.scrollTop = els.editor.scrollTop;
  els.editorHl.scrollLeft = els.editor.scrollLeft;
}

/* ============================================================
   Editor events / insert helpers
   ============================================================ */
function onEditorInput() {
  const sl = cur();
  if (!sl) return;
  sl.body = els.editor.value;
  state.dirty = true;
  updateHighlight();
  scheduleRender();
  scheduleSave();
}

function insertAtCursor(text, extraAfter = '') {
  const ta = els.editor;
  const start = ta.selectionStart, end = ta.selectionEnd;
  const value = ta.value;
  ta.value = value.slice(0, start) + text + extraAfter + value.slice(end);
  ta.selectionStart = ta.selectionEnd = start + text.length;
  ta.focus();
  onEditorInput();
}

function refreshInsertVar() {
  const sel = els.insertVar;
  sel.innerHTML = '<option value="">＋ Insert variable</option>' +
    state.variables.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join('');
}

/* ============================================================
   Rendering (live preview)
   ============================================================ */
const PREVIEW_CSS = `
  /* uniform dark palette — matches the exported presentation */
  html,body{height:100%;margin:0}
  body{display:flex;align-items:flex-start;justify-content:center;padding:26px 18px;
       font-family:Georgia,'Times New Roman',serif;color:#dfe4f0;line-height:1.6;background:#10131f}
  .wrap{max-width:860px;width:100%;border-radius:10px;padding:46px 52px;
        box-shadow:0 10px 40px rgba(0,0,0,.45);
        background:radial-gradient(700px 380px at 50% -28%, rgba(108,123,255,.12), transparent 60%), #0f1322}
  h1,h2,h3,h4{font-family:'Segoe UI',Arial,sans-serif;color:#ffffff;line-height:1.25}
  h1{font-size:30px;margin:6px 0 4px;letter-spacing:.4px}h2{font-size:21px;
     border-bottom:1px solid rgba(108,123,255,.5);padding-bottom:8px;margin:26px 0 12px}
  h3{font-size:17px;margin:16px 0 6px}p{margin:8px 0;color:#dfe4f0}
  strong{color:#ffffff}
  table{border-collapse:collapse;width:100%;margin:12px 0;font-size:14px}
  th,td{border:1px solid #2a3352;padding:8px 12px;text-align:left}
  th{background:#1a2034;color:#ffffff;font-family:'Segoe UI',Arial,sans-serif;font-weight:600}
  td{background:rgba(255,255,255,.02)}
  .muted{color:#8b93b8;font-size:13px}
  code{background:#1a2034;color:#aeb6f0;padding:1px 6px;border-radius:5px;font-size:13px}
  blockquote{border-left:3px solid #4b5478;margin:10px 0;padding:2px 16px;color:#aeb6cc}
  ul,ol{margin:8px 0;padding-left:26px}li{margin:4px 0}
  pre{background:#161b2c;border:1px solid #2a3352;color:#dfe4f0;padding:12px;overflow:auto;border-radius:8px}
`;

function scheduleRender() {
  clearTimeout(state.renderTimer);
  state.renderTimer = setTimeout(refreshRender, 220);
}

let renderSeq = 0;

async function refreshRender(focus = null) {
  const sl = cur();
  if (!sl || !state.deckId) return;
  const seq = ++renderSeq;
  try {
    const r = await api('/api/render', {
      method: 'POST',
      body: JSON.stringify({ body: sl.body || '', data: sl.data || {}, fill: state.fillMode }),
    });
    if (seq !== renderSeq) return; // a newer render superseded this one
    if (state.fillMode) {
      const scrollTop = els.previewFill.scrollTop;
      let targetPath = null, caret = null;
      const active = document.activeElement;
      if (focus && active && els.previewFill.contains(active)) {
        if (active.classList.contains('tpl-fill')) {
          targetPath = active.dataset.path === focus.path ? focus.path : (active.dataset.path || null);
          if (targetPath === focus.path) caret = focus.caret;
        }
      }
      els.previewFill.innerHTML = (sl.body || '').trim()
        ? '<div class="doc">' + r.html + '</div>'
        : '<div class="fill-empty">Write a template on the left — its blanks will appear here.</div>';
      els.previewFill.scrollTop = scrollTop;
      if (targetPath) {
        const el = els.previewFill.querySelector('[data-path="' + CSS.escape(targetPath) + '"]');
        if (el) {
          el.focus();
          if (caret != null) {
            const at = Math.min(caret, el.value.length);
            el.setSelectionRange(at, at);
          }
        }
      }
    } else {
      els.preview.srcdoc = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${PREVIEW_CSS}</style></head><body><div class="wrap">${r.html}</div></body></html>`;
      state.previewHtml = r.html;
    }
    if (JSON.stringify(r.variables) !== JSON.stringify(state.variables)
        || JSON.stringify(r.form_variables || r.variables) !== JSON.stringify(state.formVariables)
        || JSON.stringify(r.loop_variables || []) !== JSON.stringify(state.loopVariables)) {
      state.variables = r.variables;
      state.formVariables = r.form_variables || r.variables;
      state.loopVariables = r.loop_variables || [];
      buildForm();
      refreshInsertVar();
    }
    els.varCount.textContent = state.variables.length ? state.variables.length + ' variables' : '';
    const errors = r.errors || [];
    if (errors.length) {
      els.errPill.textContent = errors.length + ' syntax issue' + (errors.length > 1 ? 's' : '');
      els.errPill.title = errors.join('\n');
      els.errPill.hidden = false;
    } else {
      els.errPill.hidden = true;
    }
  } catch (e) {
    showToast('Render failed: ' + e.message, true);
  }
}

/* ============================================================
   Fill-in-the-blanks preview
   ============================================================ */
let fillRenderTimer = null;

function syncFormValue(path, val) {
  const field = els.formWrap.querySelector('[data-path="' + CSS.escape(path) + '"]');
  if (field && field.dataset.kind !== 'json') field.value = val;
}

function coerceFillValue(v) {
  return /^-?(0|[1-9]\d*)(\.\d+)?$/.test(v) ? Number(v) : v;
}

function handleFillInput(e) {
  const input = e.target.closest('.tpl-fill');
  if (!input) return;
  const sl = cur();
  if (!sl) return;
  const path = input.dataset.path;
  if (!sl.data || typeof sl.data !== 'object') sl.data = {};
  setByPath(sl.data, path, coerceFillValue(input.value));
  state.dirty = true;
  els.jsonEditor.value = JSON.stringify(sl.data, null, 2);
  syncFormValue(path, input.value);
  scheduleSave();
  clearTimeout(fillRenderTimer);
  const caret = input.selectionStart;
  fillRenderTimer = setTimeout(() => {
    buildForm();
    refreshRender({ path, caret });
  }, 150);
}

function addLoopItem(loopPath) {
  const sl = cur();
  if (!sl) return;
  if (!sl.data || typeof sl.data !== 'object') sl.data = {};
  let arr = getByPath(sl.data, loopPath);
  if (!Array.isArray(arr)) {
    arr = [];
    setByPath(sl.data, loopPath, arr);
  }
  const objectItems = arr.length > 0 && typeof arr[0] === 'object' && arr[0] !== null;
  arr.push(objectItems ? {} : '');
  state.dirty = true;
  els.jsonEditor.value = JSON.stringify(sl.data, null, 2);
  buildForm();
  scheduleSave();
  showToast('Item added — fill it in below');
  refreshRender();
}

function removeLoopItem(loopPath) {
  const sl = cur();
  if (!sl) return;
  const arr = getByPath(sl.data, loopPath);
  if (!Array.isArray(arr) || !arr.length) {
    showToast('No items left to remove', true);
    return;
  }
  arr.pop();
  state.dirty = true;
  els.jsonEditor.value = JSON.stringify(sl.data, null, 2);
  buildForm();
  scheduleSave();
  showToast('Last item removed');
  refreshRender();
}

function removeLoopItemAt(loopPath, idx) {
  const sl = cur();
  if (!sl) return;
  const arr = getByPath(sl.data, loopPath);
  if (!Array.isArray(arr) || !arr.length) {
    showToast('No items left to remove', true);
    return;
  }
  if (!Number.isInteger(idx) || idx < 0 || idx >= arr.length) {
    showToast('Item not found', true);
    return;
  }
  arr.splice(idx, 1);
  state.dirty = true;
  els.jsonEditor.value = JSON.stringify(sl.data, null, 2);
  buildForm();
  scheduleSave();
  showToast('Item removed');
  refreshRender();
}

/* ============================================================
   Data editing: form mode
   ============================================================ */
function getByPath(obj, path) {
  return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
}

function setByPath(obj, path, val) {
  const keys = path.split('.');
  let o = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    if (typeof o[keys[i]] !== 'object' || o[keys[i]] === null) o[keys[i]] = {};
    o = o[keys[i]];
  }
  o[keys[keys.length - 1]] = val;
}

function inferFieldType(path, value) {
  if (state.loopVariables.includes(path)) return 'json';
  if (Array.isArray(value) || (value && typeof value === 'object')) return 'json';
  const name = path.toLowerCase();
  if (typeof value === 'number') return 'number';
  if (/(^|\.)(date|issued|due|created|updated|day|when)$/.test(name)) return 'date';
  if (name.includes('email')) return 'email';
  if (name.includes('url') || name.includes('site')) return 'url';
  if (value && String(value).includes('\n')) return 'textarea';
  return 'text';
}

function buildForm() {
  const wrap = els.formWrap;
  wrap.innerHTML = '';
  if (!state.variables.length) {
    wrap.innerHTML = '<div class="empty-note">No variables yet — add <code>{{placeholder}}</code> tokens to this slide and a form will appear here automatically.</div>';
    return;
  }
  const grid = document.createElement('div');
  grid.className = 'form-grid';
  let normalized = false;

  for (const path of state.formVariables.length ? state.formVariables : state.variables) {
    const sl = cur();
    const value = getByPath(sl ? sl.data : {}, path);
    const type = inferFieldType(path, value);
    const field = document.createElement('label');
    field.className = 'field' + (type === 'textarea' || type === 'json' ? ' wide' : '');

    const label = document.createElement('span');
    label.className = 'field-label';
    label.textContent = path;
    label.title = path;
    field.appendChild(label);

    let input;
    if (type === 'json') {
      input = document.createElement('textarea');
      input.className = 'field-input json';
      let shown = value;
      if (typeof value === 'string') {
        try {
          shown = JSON.parse(value);
          setByPath(sl.data, path, shown); // normalize persisted strings
          normalized = true;
        } catch { /* keep raw string */ }
      }
      input.value = shown == null ? '' : JSON.stringify(shown, null, 2);
      const hint = document.createElement('span');
      hint.className = 'field-hint';
      hint.innerHTML = 'List / object — edit as JSON (used by <code>{{#each}}</code>)';
      field.appendChild(hint);
    } else {
      input = document.createElement('input');
      input.className = 'field-input';
      if (type === 'number') input.type = 'number';
      else input.type = type; // text | date | email | url
      input.value = value == null ? '' : String(value);
    }
    input.dataset.path = path;
    input.dataset.kind = type;
    input.addEventListener('input', () => onFieldChange(path, input));
    field.appendChild(input);
    grid.appendChild(field);
  }
  wrap.appendChild(grid);
  if (normalized) {
    els.jsonEditor.value = JSON.stringify(cur().data, null, 2);
    scheduleRender();
    scheduleSave();
  }
}

function onFieldChange(path, input) {
  const sl = cur();
  if (!sl) return;
  if (!sl.data || typeof sl.data !== 'object') sl.data = {};
  let val = input.value;
  const kind = input.dataset.kind;
  if (kind === 'number') val = val === '' ? '' : Number(val);
  else if (kind === 'json') {
    try {
      val = JSON.parse(val);
    } catch {
      input.style.borderColor = 'rgba(248,113,113,.6)';
      return;
    }
    input.style.borderColor = '';
  }
  setByPath(sl.data, path, val);
  state.dirty = true;
  els.jsonEditor.value = JSON.stringify(sl.data, null, 2);
  scheduleRender();
  scheduleSave();
}

/* ============================================================
   Data editing: JSON mode
   ============================================================ */
function switchDataMode(mode) {
  state.mode = mode;
  els.btnForm.classList.toggle('active', mode === 'form');
  els.btnJson.classList.toggle('active', mode === 'json');
  els.formWrap.hidden = mode !== 'form';
  els.jsonEditor.hidden = mode !== 'json';
  els.jsonError.hidden = true;
  if (mode === 'json') els.jsonEditor.focus();
}

function onJsonInput() {
  const sl = cur();
  if (!sl) return;
  try {
    const parsed = JSON.parse(els.jsonEditor.value);
    sl.data = parsed && typeof parsed === 'object' ? parsed : {};
    els.jsonError.hidden = true;
    els.jsonEditor.style.borderColor = '';
    state.dirty = true;
    buildForm();
    scheduleRender();
    scheduleSave();
  } catch (e) {
    els.jsonError.textContent = 'JSON error: ' + e.message;
    els.jsonError.hidden = false;
    els.jsonEditor.style.borderColor = 'rgba(248,113,113,.6)';
  }
}

/* ============================================================
   Saving
   ============================================================ */
function setSaveState(text, cls) {
  els.saveState.textContent = text;
  els.saveState.className = 'save-state' + (cls ? ' ' + cls : '');
}

let saving = false;
let saveQueued = false;

function scheduleSave() {
  if (!state.deckId) return;
  clearTimeout(state.saveTimer);
  setSaveState('Saving…');
  const snap = {
    id: state.deckId,
    name: state.name,
    slides: JSON.parse(JSON.stringify(state.slides)),
    injects: JSON.parse(JSON.stringify(state.injects)),
    meta: state.meta || null,
  };
  state.saveTimer = setTimeout(() => doSave(snap), 700);
}

async function doSave(snap) {
  const target = snap || { id: state.deckId, name: state.name, slides: state.slides };
  if (!target.id) return;
  if (saving) {
    saveQueued = true;
    return;
  }
  saving = true;
  try {
    const deck = await api('/api/decks/' + target.id, {
      method: 'PUT',
      body: JSON.stringify({ name: target.name, slides: target.slides, injects: target.injects, meta: target.meta }),
    });
    state.dirty = false;
    setSaveState('Saved ✓', 'ok');
    const meta = state.decks.find((d) => d.id === target.id);
    if (meta) {
      meta.name = deck.name;
      meta.updated = deck.updated;
      meta.slide_count = (deck.slides || []).length;
      renderDecks();
    }
  } catch (e) {
    setSaveState('Save failed', 'err');
    showToast('Save failed: ' + e.message, true);
  } finally {
    saving = false;
    if (saveQueued) {
      saveQueued = false;
      scheduleSave();
    }
  }
}

/* ============================================================
   Present & export
   ============================================================ */
function slug(s) {
  return (s || 'presentation').toLowerCase().replace(/[^\w\- ]+/g, '').trim().replace(/\s+/g, '-') || 'presentation';
}

async function openPresent() {
  if (!state.slides.length) {
    showToast('Add a slide before presenting', true);
    return;
  }
  try {
    const html = await api('/api/export', {
      method: 'POST',
      body: JSON.stringify({ name: state.name, slides: state.slides, format: 'presentation',
                            injects: state.injects, meta: state.meta }),
    });
    els.presentOverlay.hidden = false;
    els.presentFrame.srcdoc = html;
    els.presentFrame.addEventListener('load', () => {
      try { els.presentFrame.contentWindow.focus(); } catch { /* ignore */ }
    });
  } catch (e) {
    showToast('Could not start presentation: ' + e.message, true);
  }
}

function closePresent() {
  if (els.presentOverlay.hidden) return;
  if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen();
  els.presentOverlay.hidden = true;
  els.presentFrame.srcdoc = '';
}

async function exportDeck(fmt) {
  try {
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: state.name, slides: state.slides, format: fmt,
                             injects: state.injects, meta: state.meta }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || res.statusText);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = slug(state.name) + '.' + (fmt === 'presentation' ? 'html' : 'doc');
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Exported ' + slug(state.name) + '.' + (fmt === 'presentation' ? 'html' : 'doc'));
  } catch (e) {
    showToast('Export failed: ' + e.message, true);
  }
}

async function doPrint() {
  try {
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: state.name, slides: state.slides, format: 'handout' }),
    });
    if (!res.ok) throw new Error('Export failed');
    const text = await res.text();
    const w = window.open('', '_blank');
    if (!w) {
      showToast('Please allow pop-ups to print.', true);
      return;
    }
    w.document.write(text);
    w.document.close();
    w.focus();
    setTimeout(() => { w.print(); }, 350);
  } catch (e) {
    showToast('Print failed: ' + e.message, true);
  }
}

/* ============================================================
   Add Inject — appends an inject slide to the deck's timeline
   ============================================================ */
function addInject() {
  const inj = {
    time: '09:00',
    title: 'New inject',
    detail: 'Describe what the team observes at this point in the scenario.',
    prompt: 'Team Response — Critical decision point',
  };
  state.injects.push(inj);
  const n = state.injects.length;
  const sl = {
    id: uid(),
    name: 'Inject #' + n + ' — ' + inj.title,
    layout: 'section',
    body: '# Inject #' + n + ' — {{title}}\n\n**{{time}}** — {{detail}}\n\n> {{prompt}}',
    data: { number: n, time: inj.time, title: inj.title, detail: inj.detail, prompt: inj.prompt },
  };
  state.slides.push(sl);
  state.dirty = true;
  scheduleSave();
  selectSlide(state.slides.length - 1);
  showToast('Inject #' + n + ' added to the deck — saved');
}

/* ============================================================
   Toast
   ============================================================ */
let toastTimer = null;
function showToast(msg, isErr = false) {
  els.toast.textContent = msg;
  els.toast.className = 'toast' + (isErr ? ' err' : '');
  els.toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { els.toast.hidden = true; }, 2600);
}

/* ============================================================
   Gutter resize
   ============================================================ */
function initGutter() {
  let dragging = false;
  const onMove = (e) => {
    if (!dragging) return;
    const rect = els.workspace.getBoundingClientRect();
    const pct = Math.min(0.75, Math.max(0.25, (e.clientX - rect.left) / rect.width)) * 100;
    els.editorPane.style.flex = `${pct} 1 0`;
    els.rightPane.style.flex = `${100 - pct} 1 0`;
  };
  els.gutter.addEventListener('mousedown', (e) => {
    dragging = true;
    els.gutter.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    e.preventDefault();
  });
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', () => {
    dragging = false;
    els.gutter.classList.remove('dragging');
    document.body.style.cursor = '';
  });
}

/* ============================================================
   Event wiring
   ============================================================ */
function bindEvents() {
  els.deckName.addEventListener('input', () => {
    state.name = els.deckName.value;
    state.dirty = true;
    scheduleSave();
  });

  els.deckList.addEventListener('click', (e) => {
    const more = e.target.closest('[data-more]');
    if (more) {
      const rect = more.getBoundingClientRect();
      openDeckMenu(more.dataset.more, rect.left, rect.bottom + 6);
      return;
    }
    const del = e.target.closest('[data-del]');
    if (del) { deleteDeck(del.dataset.del); return; }
    const item = e.target.closest('.deck-item');
    if (item) selectDeck(item.dataset.id);
  });
  els.deckList.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      const item = e.target.closest('.deck-item');
      if (item) {
        e.preventDefault();
        selectDeck(item.dataset.id);
      }
    }
  });

  els.search.addEventListener('input', () => {
    state.search = els.search.value;
    renderDecks();
  });

  els.btnNew.addEventListener('click', createDeck);
  els.btnSimulations.addEventListener('click', showLibrary);
  els.btnDashboard.addEventListener('click', () => {
    if (state.deckId && !els.workspace.hidden) return; // already on the deck view
    if (state.deckId) selectDeck(state.deckId);
    else showLibrary();
  });
  els.scenarioCats.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const card = btn.closest('.scenario-card');
    if (card) runScenario(btn.dataset.act, card.dataset.title);
  });
  els.btnImport.addEventListener('click', () => els.fileImport.click());
  els.fileImport.addEventListener('change', (e) => importDecks(e.target.files));
  els.btnEmptyNew.addEventListener('click', createDeck);
  els.btnEmptySample.addEventListener('click', () => {
    const first = state.decks[0];
    if (first) selectDeck(first.id);
  });
  els.emptyDecks.addEventListener('click', (e) => {
    const chip = e.target.closest('.sample-chip');
    if (chip) selectDeck(chip.dataset.id);
  });

  /* slide strip */
  els.slideStrip.addEventListener('click', (e) => {
    const more = e.target.closest('.slide-more');
    if (more) {
      const rect = more.getBoundingClientRect();
      openSlideMenu(+more.dataset.more, rect.left, rect.bottom + 6);
      return;
    }
    const card = e.target.closest('.slide-card');
    if (card) selectSlide(+card.dataset.idx);
  });
  els.btnInsertSlide.addEventListener('click', (e) => {
    e.stopPropagation();
    openInsertMenu();
  });
  els.slideMenu.addEventListener('click', (e) => {
    const item = e.target.closest('[data-layout], [data-act]');
    if (!item) return;
    if (item.dataset.layout) {
      els.slideMenu.hidden = true;
      insertSlide(item.dataset.layout);
      return;
    }
    if (!item.dataset.act) return;
    const act = item.dataset.act;
    els.slideMenu.hidden = true;
    if (act === 'duplicate') {
      if (slideMenuFor != null) duplicateSlide(slideMenuFor);
      else if (state.slides.length) duplicateSlide(state.currentSlide);
    }
  });

  /* editor */
  els.editor.addEventListener('input', onEditorInput);
  els.editor.addEventListener('scroll', syncScroll);
  els.editor.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const ta = els.editor;
      const start = ta.selectionStart, end = ta.selectionEnd;
      ta.value = ta.value.slice(0, start) + '  ' + ta.value.slice(end);
      ta.selectionStart = ta.selectionEnd = start + 2;
      onEditorInput();
    }
  });

  els.insertVar.addEventListener('change', () => {
    const v = els.insertVar.value;
    if (v) insertAtCursor('{{' + v + '}}');
    els.insertVar.value = '';
  });

  els.insertBlock.addEventListener('change', () => {
    const kind = els.insertBlock.value;
    els.insertBlock.value = '';
    if (!kind) return;
    if (kind === 'if') insertAtCursor('{{#if ', '\n  \n{{/if}}');
    else if (kind === 'unless') insertAtCursor('{{#unless ', '\n  \n{{/unless}}');
    else if (kind === 'each') insertAtCursor('{{#each ', '\n  {{this}}\n{{/each}}');
    else if (kind === 'else') insertAtCursor('{{else}}');
    else if (kind === 'comment') insertAtCursor('{{! comment }}');
  });

  /* data editing */
  els.btnForm.addEventListener('click', () => switchDataMode('form'));
  els.btnJson.addEventListener('click', () => switchDataMode('json'));
  els.jsonEditor.addEventListener('input', debounce(onJsonInput, 350));

  els.btnResetData.addEventListener('click', async () => {
    if (!state.deckId) return;
    try {
      const deck = await api('/api/decks/' + state.deckId);
      state.slides = Array.isArray(deck.slides) ? deck.slides : [];
      state.currentSlide = Math.min(state.currentSlide, Math.max(0, state.slides.length - 1));
      if (state.slides.length) {
        selectSlide(state.currentSlide);
      } else {
        els.editor.value = '';
        els.jsonEditor.value = '{}';
        els.formWrap.innerHTML = '';
        els.preview.srcdoc = '';
        els.previewFill.innerHTML = '';
        renderStrip();
        updateSlideCount();
      }
      showToast('Data reset to last saved version');
    } catch (e) {
      showToast('Reset failed: ' + e.message, true);
    }
  });

  /* tabs */
  $$('.tab').forEach((tab) => tab.addEventListener('click', () => {
    $$('.tab').forEach((t) => t.classList.toggle('active', t === tab));
    els.tabPreview.hidden = tab.dataset.tab !== 'preview';
    els.tabData.hidden = tab.dataset.tab !== 'data';
  }));

  /* export menu */
  els.btnExport.addEventListener('click', (e) => {
    e.stopPropagation();
    els.exportMenu.hidden = !els.exportMenu.hidden;
  });
  els.exportMenu.addEventListener('click', (e) => {
    const item = e.target.closest('[data-fmt]');
    if (item) {
      els.exportMenu.hidden = true;
      exportDeck(item.dataset.fmt);
    }
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.export-wrap')) els.exportMenu.hidden = true;
    if (!e.target.closest('#deck-menu') && !e.target.closest('[data-more]')) closeDeckMenu();
    if (!e.target.closest('#slide-menu')
        && !e.target.closest('[data-more]')
        && e.target !== els.btnInsertSlide) closeSlideMenu();
  });

  els.deckMenu.addEventListener('click', (e) => {
    const item = e.target.closest('[data-act]');
    if (!item || !deckMenuFor) return;
    const id = deckMenuFor;
    const act = item.dataset.act;
    closeDeckMenu();
    if (act === 'open') selectDeck(id);
    else if (act === 'rename') renameDeck(id);
    else if (act === 'duplicate') duplicateDeck(id);
    else if (act === 'download') downloadDeck(id);
    else if (act === 'delete') deleteDeck(id);
  });

  /* drag & drop a deck file onto the app */
  window.addEventListener('dragover', (e) => {
    if (e.dataTransfer && [...e.dataTransfer.types].includes('Files')) e.preventDefault();
  });
  window.addEventListener('drop', (e) => {
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) {
      e.preventDefault();
      importDecks(e.dataTransfer.files);
    }
  });

  els.btnPrint.addEventListener('click', doPrint);
  els.btnPresent.addEventListener('click', openPresent);
  els.btnExitPresent.addEventListener('click', closePresent);

  els.btnAddInject.addEventListener('click', addInject);

  els.btnPreviewMode.addEventListener('click', () => setFillMode(false));
  els.btnFillMode.addEventListener('click', () => setFillMode(true));

  els.previewFill.addEventListener('input', handleFillInput);
  els.previewFill.addEventListener('click', (e) => {
    const add = e.target.closest('.tpl-add');
    if (add) { addLoopItem(add.dataset.loop); return; }
    const itemDel = e.target.closest('.tpl-item-del');
    if (itemDel) { removeLoopItemAt(itemDel.dataset.loop, +itemDel.dataset.idx); return; }
    const del = e.target.closest('.tpl-del');
    if (del) removeLoopItem(del.dataset.loop);
  });
  els.previewFill.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    const input = e.target.closest('.tpl-fill');
    if (!input) return;
    const fills = els.previewFill.querySelectorAll('.tpl-fill');
    const next = fills[[...fills].indexOf(input) + 1];
    if (!next) return;
    e.preventDefault();
    next.focus();
  });

  els.btnHelp.addEventListener('click', () => { els.helpModal.hidden = false; });
  els.btnHelpClose.addEventListener('click', () => { els.helpModal.hidden = true; });
  els.helpModal.addEventListener('click', (e) => {
    if (e.target === els.helpModal) els.helpModal.hidden = true;
  });

  window.addEventListener('message', (e) => {
    if (e.data && e.data.type === 'deckforge:exit') closePresent();
  });

  // Fullscreen the whole present overlay (Exit button included), so a
  // facilitator can leave the exercise with one click instead of exiting
  // fullscreen first. Called synchronously from inside the presentation
  // iframe (same origin), which preserves the user-gesture requirement.
  window.deckForgeToggleFullscreen = () => {
    if (els.presentOverlay.hidden) return;
    if (document.fullscreenElement) {
      if (document.exitFullscreen) document.exitFullscreen();
    } else if (els.presentOverlay.requestFullscreen) {
      els.presentOverlay.requestFullscreen();
    }
  };

  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      doSave();
    }
    if (e.key === 'Escape') {
      if (!els.helpModal.hidden) els.helpModal.hidden = true;
      if (!els.presentOverlay.hidden) closePresent();
      closeDeckMenu();
      closeSlideMenu();
    }
  });

  initGutter();
  initSlideDnd();
}

init();
