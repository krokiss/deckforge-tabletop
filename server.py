#!/usr/bin/env python3
"""DeckForge — presentation builder (dev server, Python stdlib only).

Run:  python server.py            # then open http://127.0.0.1:8420
Options:  --port 9000   --host 0.0.0.0
"""

import argparse
import hmac
import html as _html
import http.cookies as _cookies
import json
import os
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import renderer
from store import Store

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}

store = Store()

# -- optional authentication -------------------------------------------------
# Set the AUTH_PASSWORD environment variable to protect a deployed instance.
# When unset (local dev), the app behaves exactly as before — open access.
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "").strip()
AUTH_TTL = 12 * 3600  # session lifetime (sliding)
_SESSIONS = {}        # token -> expiry epoch
_SESS_LOCK = threading.Lock()
_LOGIN_ATTEMPTS = {}  # ip -> [attempt epochs]

LOGIN_PAGE = ("""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">"""
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
    "<title>DeckForge — Sign in</title>"
    "<style>"
    "body{font-family:'Segoe UI',Arial,sans-serif;background:#0e1320;color:#e6edf7;margin:0;"
    "min-height:100vh;display:flex;align-items:center;justify-content:center}"
    ".card{background:#171e30;border:1px solid #253049;border-radius:14px;padding:40px 36px;"
    "width:340px;box-shadow:0 10px 30px rgba(0,0,0,.35)}"
    "h1{font-size:20px;margin:0 0 4px;letter-spacing:.3px}"
    "p{color:#8fa1c4;font-size:13px;margin:0 0 22px}"
    "input{width:100%;box-sizing:border-box;padding:11px 12px;border-radius:8px;border:1px solid #2c3a5c;"
    "background:#0e1320;color:#e6edf7;font-size:14px;margin-bottom:14px}"
    "input:focus{outline:none;border-color:#38bdf8}"
    "button{width:100%;padding:11px;border:0;border-radius:8px;background:#0ea5e9;color:#04121c;"
    "font-weight:700;font-size:14px;cursor:pointer}"
    "button:hover{background:#38bdf8}"
    ".err{color:#f87171;font-size:13px;margin:0 0 12px;min-height:16px}"
    "</style></head><body>"
    "<form class=\"card\" id=\"f\" method=\"post\">"
    "<h1>DeckForge</h1><p>Table Top Exercise Builder — restricted access</p>"
    "<input type=\"password\" id=\"p\" placeholder=\"Password\" autofocus autocomplete=\"current-password\">"
    "<p class=\"err\" id=\"e\"></p><button type=\"submit\">Sign in</button></form>"
    "<script>"
    "const f=document.getElementById('f'),p=document.getElementById('p'),e=document.getElementById('e');"
    "f.addEventListener('submit',async ev=>{ev.preventDefault();e.textContent='';"
    "const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},"
    "body:JSON.stringify({password:p.value})});"
    "if(r.ok){location.href='/';}else{e.textContent=(await r.json().catch(()=>({}))).error||'Wrong password.';}});"
    "</script></body></html>")

LAYOUTS = ("title", "content", "section", "blank")

DOC_STYLE = (
    "body{font-family:Georgia,'Times New Roman',serif;max-width:720px;margin:40px auto;"
    "padding:0 28px;color:#1f2430;line-height:1.65;background:#fff}"
    "h1,h2,h3,h4{font-family:'Segoe UI',Arial,sans-serif;color:#111827;line-height:1.25}"
    "h1{font-size:26px;margin:8px 0 4px;letter-spacing:.4px}h2{font-size:18px;"
    "border-bottom:1px solid #e5e7eb;padding-bottom:6px;margin:28px 0 10px}"
    "h3{font-size:15px;margin:18px 0 6px}p{margin:8px 0}"
    "table{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px}"
    "th,td{border:1px solid #d7dce6;padding:7px 10px;text-align:left}"
    "th{background:#f4f6fa;font-family:'Segoe UI',Arial,sans-serif;font-weight:600}"
    ".muted{color:#6b7280;font-size:12.5px}.total{margin-top:16px;font-size:15px}"
    ".meta{margin:18px 0}.meta th{width:90px;background:none;border:none}"
    ".meta td{border:none}.meta tr{border-bottom:1px solid #eef1f6}"
    "code{background:#f3f4f6;padding:1px 5px;border-radius:4px;font-size:12.5px}"
    "blockquote{border-left:3px solid #e5e7eb;margin:10px 0;padding:2px 16px;color:#4b5563}"
    "hr{border:none;border-top:1px solid #e5e7eb;margin:24px 0}"
    "ul,ol{margin:8px 0;padding-left:24px}li{margin:3px 0}"
    "pre{background:#f6f8fb;border:1px solid #e5e7eb;padding:12px;overflow:auto;border-radius:6px}"
)

HANDOUT_CSS = (
    ".handout-slide{page-break-after:always}"
    ".handout-slide:last-child{page-break-after:auto}"
    ".handout-label{font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;font-weight:700;"
    "letter-spacing:.8px;text-transform:uppercase;color:#9aa3b8;border-bottom:1px solid #e5e7eb;"
    "padding-bottom:8px;margin-bottom:4px}"
)

AFTERACTION_CSS = (
    ".report-head{font-family:'Segoe UI',Arial,sans-serif;text-align:center;margin:6px 0 4px}"
    ".report-head h1{font-size:30px;margin:0 0 2px;letter-spacing:.4px}"
    ".report-head p{color:#6b7280;font-size:13px;margin:2px 0}"
    ".report-head .framework{font-size:11.5px;color:#6d28d9;font-weight:600;letter-spacing:.3px;margin-top:8px}"
    ".aar-meta{margin:18px 0 6px;border:0}"
    ".aar-meta td{border:none;padding:5px 10px;font-size:13px;background:#fff}"
    ".aar-meta td.k{width:150px;color:#6b7280;font-weight:600;font-family:'Segoe UI',Arial,sans-serif;"
    "background:#fafbfd}"
    ".aar-meta tr{border-bottom:1px solid #eef1f6}"
    ".aar-callout{border-left:4px solid #7c3aed;background:#f7f5ff;padding:12px 16px;margin:14px 0;"
    "border-radius:0 8px 8px 0;color:#3b3663;font-size:14px;line-height:1.6}"
    ".aar-callout b{color:#4c1d95}"
    ".aar-note{color:#6b7280;font-size:12px;font-style:italic;margin:6px 0 0}"
    ".aar-section h2{font-size:19px;margin:30px 0 8px}"
    "table{font-size:12.5px}"
    "th,td{padding:6px 9px;vertical-align:top}"
    "ol,ul{margin:8px 0;padding-left:24px}li{margin:4px 0;font-size:13.5px}"
)

# Standalone HTML presentation. Slides are designed on a 1280x720 canvas and
# scaled to fit the viewport, so typography is deterministic and printing can
# simply drop the transform. %%TITLE%% / %%SLIDES%% are replaced at export time.
PRESENT_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE%%</title>
<style>
html, body { margin: 0; height: 100%; overflow: hidden; background: #0b0e15; }
.stage {
  position: fixed; inset: 0;
  background:
    radial-gradient(1200px 640px at 50% -12%, rgba(108,123,255,.16), transparent 62%),
    radial-gradient(900px 500px at 108% 112%, rgba(160,107,255,.10), transparent 55%),
    #0b0e15;
}
/* One uniform dark palette for every slide layout (title | content | section | blank) */
.slide {
  position: absolute; left: 50%; top: 50%; width: 1280px; height: 720px;
  margin: -360px 0 0 -640px; background: #0f1322; border-radius: 6px; overflow: hidden;
  box-shadow: 0 34px 90px rgba(0,0,0,.55);
  transform: scale(var(--scale, 1)); display: none;
}
.slide.active { display: block; animation: fade .22s ease-out; }
@keyframes fade { from { opacity: 0; } }
.slide .inner {
  position: absolute; inset: 0; padding: 64px 84px; box-sizing: border-box;
  font-family: Georgia, 'Times New Roman', serif; color: #dfe4f0; line-height: 1.5;
  overflow: hidden;
  background:
    radial-gradient(900px 480px at 50% -18%, rgba(108,123,255,.14), transparent 60%),
    #0f1322;
}
.slide .inner h1 { font-size: 54px; margin: 4px 0 16px; color: #ffffff; line-height: 1.15; }
.slide .inner h2 { font-size: 32px; margin: 0 0 16px; padding-bottom: 10px;
  border-bottom: 2px solid rgba(108,123,255,.55); color: #ffffff; letter-spacing: .2px; }
.slide .inner h3 { font-size: 23px; margin: 14px 0 6px; color: #ffffff; }
.slide .inner p { font-size: 21px; margin: 10px 0; color: #dfe4f0; }
.slide .inner strong { color: #ffffff; }
.slide .inner ul, .slide .inner ol { margin: 12px 0; padding-left: 32px; }
.slide .inner li { font-size: 21px; margin: 7px 0; }
.slide .inner table { border-collapse: collapse; width: 100%; margin: 14px 0; font-size: 19px; }
.slide .inner th, .slide .inner td { border: 1px solid #2a3352; padding: 9px 12px; text-align: left; }
.slide .inner th { background: #1a2034; color: #ffffff; font-family: 'Segoe UI', Arial, sans-serif; font-weight: 600; }
.slide .inner td { background: rgba(255,255,255,.02); }
.slide .inner code { background: #1a2034; color: #aeb6f0; padding: 1px 6px; border-radius: 5px; font-size: 19px; }
.slide .inner blockquote { border-left: 3px solid #4b5478; margin: 12px 0; padding: 2px 18px; color: #aeb6cc; }
.slide .inner .muted { color: #8b93b8; font-size: 17px; }
.slide .inner pre { background: #161b2c; border: 1px solid #2a3352; color: #dfe4f0; padding: 14px; border-radius: 8px; font-size: 18px; }
.slide.title .inner, .slide.section .inner {
  display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;
}
.slide.title h1 { font-size: 72px; margin: 0 0 22px; letter-spacing: .4px; }
.slide.title h2 { border: none; padding: 0; font-size: 30px; color: #aeb6cc; }
.slide.title p { font-size: 28px; color: #8b93b8; margin: 0; }
.slide.section h1 { color: #ffffff; font-size: 62px; letter-spacing: .5px; margin: 0 0 18px; }
.slide.section p { color: #aeb6cc; font-size: 26px; margin: 0; }
.slide.blank .inner { padding: 0; }
.empty-deck {
  position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);
  color: #8b93b8; font-family: 'Segoe UI', Arial, sans-serif; font-size: 20px;
}
.controls {
  position: fixed; left: 50%; bottom: 22px; transform: translateX(-50%);
  display: flex; align-items: center; gap: 6px; z-index: 20;
  background: rgba(19,23,34,.85); border: 1px solid rgba(108,123,255,.35);
  border-radius: 999px; padding: 7px 10px; backdrop-filter: blur(8px);
}
.controls button {
  width: 34px; height: 34px; border-radius: 50%; border: 0; cursor: pointer;
  background: rgba(108,123,255,.18); color: #fff; font-size: 18px; line-height: 1;
  transition: background .15s;
}
.controls button:hover { background: rgba(108,123,255,.42); }
.controls .counter {
  color: #c9d1e5; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;
  font-weight: 600; padding: 0 8px; min-width: 60px; text-align: center;
}
.progress { position: fixed; top: 0; left: 0; height: 4px; width: 100%; z-index: 21;
  background: rgba(108,123,255,.15); }
.progress i { display: block; height: 100%; width: 0;
  background: linear-gradient(90deg, #6c7bff, #a06bff); transition: width .25s; }
@media print {
  html, body { overflow: visible; background: #fff; }
  .stage { position: static; background: none; }
  .slide { position: relative; left: auto; top: auto; margin: 0 auto; width: 100%;
    height: auto; transform: none; border-radius: 0; box-shadow: none;
    display: block !important; page-break-after: always; }
  .slide .inner { position: static; padding: 48px 60px; overflow: visible;
    background: none !important; color: #1f2430; }
  .slide .inner h1, .slide .inner h2, .slide .inner h3, .slide .inner strong { color: #111827; }
  .slide .inner h2 { border-bottom-color: #e5e7eb; }
  .slide .inner p { color: #1f2430; }
  .slide .inner th { background: #f4f6fa; color: #111827; }
  .slide .inner th, .slide .inner td { border-color: #d7dce6; }
  .slide .inner td { background: none; }
  .slide .inner code, .slide .inner pre { background: #f6f8fb; color: #1f2430; border-color: #e5e7eb; }
  .slide .inner blockquote { border-color: #e5e7eb; color: #4b5563; }
  .slide .inner .muted { color: #6b7280; }
  .slide.title h2, .slide.title p, .slide.section p { color: #4b5563; }
  .controls, .progress { display: none !important; }
}
%%INJECT_CSS%%
</style>
</head>
<body>
<div class="stage" id="stage">
%%SLIDES%%
</div>
<div class="progress"><i id="bar"></i></div>
<div class="controls">
  <button id="prev" title="Previous (←)">&#8249;</button>
  <span class="counter" id="counter">1 / 1</span>
  <button id="next" title="Next (→)">&#8250;</button>
  <button id="fs" title="Fullscreen (F)">&#9226;</button>
</div>
%%INJECT_HTML%%
<script>
(function () {
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var n = slides.length, i = -1;
  var counter = document.getElementById('counter');
  var bar = document.getElementById('bar');
  function show(k) {
    i = Math.max(0, Math.min(n - 1, k));
    slides.forEach(function (s, j) { s.classList.toggle('active', j === i); });
    if (counter) counter.textContent = (n ? i + 1 : 0) + ' / ' + n;
    if (bar) bar.style.width = (n > 1 ? (i / (n - 1)) * 100 : n ? 100 : 0) + '%';
  }
  function fit() {
    var maxH = 720;
    slides.forEach(function (s) { var h = parseInt(s.getAttribute('data-h') || '720', 10); if (h > maxH) maxH = h; });
    var s = Math.min(window.innerWidth / 1280, window.innerHeight / maxH);
    document.documentElement.style.setProperty('--scale', String(s));
  }
  function next() { show(i + 1); }
  function prev() { show(i - 1); }
  function toggleFs() {
    // When embedded in the app, delegate to the host so the whole present
    // overlay (Exit button included) goes fullscreen instead of just this
    // iframe. Standalone exports fall back to fullscreening the document.
    var host = (window.parent && window.parent !== window) ? window.parent : null;
    if (host && typeof host.deckForgeToggleFullscreen === 'function') {
      host.deckForgeToggleFullscreen();
      return;
    }
    if (document.fullscreenElement) { if (document.exitFullscreen) document.exitFullscreen(); }
    else { var el = document.documentElement;
      (el.requestFullscreen || function () {}).call(el); }
  }
  window.addEventListener('resize', fit);
  document.addEventListener('keydown', function (e) {
    // Never hijack keyboard when the user is typing in a textarea or input.
    var t = e.target;
    if (t && (t.tagName === 'TEXTAREA' || t.tagName === 'INPUT' || t.contentEditable === 'true')) return;
    if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown' || e.key === 'Enter') {
      e.preventDefault(); next();
    } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault(); prev();
    } else if (e.key === 'Home') { e.preventDefault(); show(0); }
    else if (e.key === 'End') { e.preventDefault(); show(n - 1); }
    else if (e.key.toLowerCase() === 'f') { toggleFs(); }
    else if (e.key === 'Escape') {
      if (document.fullscreenElement) { if (document.exitFullscreen) document.exitFullscreen(); }
      else { try { parent.postMessage({ type: 'deckforge:exit' }, '*'); } catch (err) {} }
    }
  });
  var nextBtn = document.getElementById('next'), prevBtn = document.getElementById('prev');
  if (nextBtn) nextBtn.addEventListener('click', next);
  if (prevBtn) prevBtn.addEventListener('click', prev);
  var fsBtn = document.getElementById('fs');
  if (fsBtn) fsBtn.addEventListener('click', toggleFs);
  var x0 = null;
  document.addEventListener('touchstart', function (e) { x0 = e.changedTouches[0].clientX; }, { passive: true });
  document.addEventListener('touchend', function (e) {
    if (x0 == null) return;
    var dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 60) { if (dx < 0) next(); else prev(); }
    x0 = null;
  }, { passive: true });
  fit();
  show(0);
})();
</script>
%%INJECT_JS%%
</body>
</html>
"""


def _render_slide_html(s):
    """Render one slide's body to HTML, never raising."""
    try:
        return renderer.render(s.get("body") or "", s.get("data") or {}, html_mode=True)["html"]
    except Exception as exc:  # noqa: BLE001 - surface renderer bugs inside the slide
        return "<p class='muted'>[Render error: %s]</p>" % _html.escape(str(exc))


# --------------------------------------------------------------------------- #
# Integrated inject interactivity for the exported presentation.             #
# Each Inject #N slide gets an inline team-response widget; Hotwash and      #
# After Action slides get a recorded-responses log. Self-contained so the     #
# exported .html works without the app.                                      #
# --------------------------------------------------------------------------- #
INJECT_CSS = (
    '.inj-widget{margin-top:22px;border-top:1px solid rgba(108,123,255,.4);padding-top:16px}'
    '.inj-widget .inj-ta{width:100%;box-sizing:border-box;background:#0d1220;color:#e6e9f2;'
    'border:1px solid rgba(255,255,255,.16);border-radius:8px;padding:12px 16px;'
    'font:16px/1.5 Segoe UI,Arial,sans-serif;min-height:230px;resize:vertical}'
    '.inj-widget .inj-ta:focus{outline:none;border-color:#6c7bff;box-shadow:0 0 0 3px rgba(108,123,255,.18)}'
    '.inj-widget .inj-saved{margin-top:10px;font-size:16px;color:#a7f3d0;'
    'background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.35);'
    'border-radius:8px;padding:10px 14px;white-space:pre-wrap}'
    '.inj-widget .inj-next{margin-top:12px;background:#6c7bff;color:#fff;border:0;'
    'border-radius:8px;padding:10px 20px;font:600 14px Segoe UI,Arial,sans-serif;cursor:pointer}'
    '.inj-widget .inj-next:hover{background:#5a68f0}'
    '.inj-widget .inj-note{color:#8b93b8;font-size:16px;font-style:italic;margin:2px 0 8px}'
    '.role-pick{margin-top:22px;border-top:1px solid rgba(108,123,255,.4);padding-top:16px}'
    '.role-opts{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px;margin:10px 0 12px}'
    '.role-opt{display:flex;align-items:flex-start;gap:9px;background:#141a2a;border:1px solid rgba(255,255,255,.1);'
    'border-radius:8px;padding:9px 12px;cursor:pointer;font:14px Segoe UI,Arial,sans-serif;color:#e6e9f2}'
    '.role-opt:hover{border-color:#6c7bff}'
    '.role-opt input{accent-color:#6c7bff;margin-top:2px}'
    '.role-opt .ro-owner{display:block;font-size:11.5px;color:#8b93b8;margin-top:1px}'
    '.role-confirm{margin-top:12px;background:#6c7bff;color:#fff;border:0;border-radius:8px;padding:10px 20px;'
    'font:600 14px Segoe UI,Arial,sans-serif;cursor:pointer}'
    '.role-confirm:hover{background:#5a68f0}'
    '.role-pick .inj-saved{white-space:normal}'
    # Roles slide: compact layout so the full roster + picker fit the 720p canvas
    '.slide.roles .inner h2{margin:0 0 10px;padding-bottom:6px}'
    '.slide.roles .inner table{font-size:15px;margin:10px 0}'
    '.slide.roles .inner th,.slide.roles .inner td{padding:5px 10px;font-size:15px}'
    '.slide.roles .role-pick{margin-top:12px;padding-top:10px}'
    '.slide.roles .role-opts{gap:6px;margin:8px 0 10px}'
    '.slide.roles .role-opt{padding:6px 10px;font-size:13.5px;gap:7px}'
    '.slide.roles .role-opt .ro-owner{display:inline;font-size:11px;margin-left:6px}'
    '.slide.roles .role-confirm{margin-top:8px;padding:8px 16px;font-size:13px}'
    # After Action slide: taller canvas + compact type so the full report fits.
    # overflow-y:auto is a safety net — content never clips, it scrolls.
    '.slide.aar-slide{height:940px;margin:-470px 0 0 -640px}'
    '.slide.aar-slide .inner{overflow-y:auto;padding:44px 76px}'
    '.slide.aar-slide .inner h2{font-size:24px;margin:0 0 8px;padding-bottom:5px}'
    '.slide.aar-slide .inner h3{font-size:14.5px;margin:9px 0 3px}'
    '.slide.aar-slide .inner p,.slide.aar-slide .inner li{font-size:13px;margin:3px 0}'
    '.slide.aar-slide .inner ul,.slide.aar-slide .inner ol{margin:6px 0;padding-left:22px}'
    '.slide.aar-slide .inner table{font-size:12px;margin:6px 0}'
    '.slide.aar-slide .inner th,.slide.aar-slide .inner td{padding:3px 7px;font-size:12px}'
    '.slide.aar-slide .inj-log{margin-top:10px;padding-top:8px}'
    '.slide.aar-slide .inj-log .inj-log-item{padding:6px 10px;margin:5px 0}'
    '.slide.aar-slide .inj-log h4{font-size:12.5px}'
    '.inj-log{margin-top:26px;border-top:2px dashed rgba(108,123,255,.45);padding-top:14px}'
    '.inj-log h4{margin:0 0 10px;color:#ffffff;font:700 15px Segoe UI,Arial,sans-serif;'
    'letter-spacing:.6px;text-transform:uppercase}'
    '.inj-log .inj-log-item{margin:8px 0;padding:10px 14px;background:rgba(255,255,255,.03);'
    'border:1px solid rgba(255,255,255,.1);border-radius:8px}'
    '.inj-log .inj-log-item b{color:#00f0ff;font-family:Segoe UI,Arial,sans-serif}'
    '.inj-log .inj-log-item .r{color:#a7f3d0;display:block;margin-top:4px;white-space:pre-wrap}'
    '.inj-log .inj-log-empty{color:#8b93b8;font-style:italic}'
)

INJECT_WIDGET_HTML = (
    '<div class="inj-widget">'
    '<div class="inj-note">Record the team\u2019s decision at this decision point.</div>'
    '<textarea class="inj-ta" rows="10" placeholder="Record the team\u2019s decision and rationale\u2026"></textarea>'
    '<div class="inj-saved" hidden></div>'
    '<button class="inj-next">Save &amp; next inject \u2192</button>'
    '</div>'
)

DECISION_CSS = (
    '.slide.content.dec-slide .inner{overflow-y:auto;padding-bottom:80px}'
    '.dec-widget{margin-top:12px;border-top:1px solid rgba(255,193,7,.4);padding-top:10px}'
    '.dec-widget .dec-note{color:#fbbf24;font:italic 12px Segoe UI,Arial,sans-serif;margin-bottom:4px}'
    '.dec-widget .dec-q{margin-bottom:6px}'
    '.dec-widget .dec-q-label{color:#93c5fd;font:600 12px Segoe UI,Arial,sans-serif;margin-bottom:2px}'
    '.dec-widget .dec-q-ta{width:100%;box-sizing:border-box;background:#0d1220;color:#e6e9f2;'
    'border:1px solid rgba(255,255,255,.16);border-radius:6px;padding:6px 10px;'
    'font:13px/1.3 Segoe UI,Arial,sans-serif;height:44px;resize:none}'
    '.dec-widget .dec-q-ta:focus{outline:none;border-color:#fbbf24;box-shadow:0 0 0 3px rgba(251,191,36,.18)}'
    '.dec-widget .dec-saved{margin-top:4px;padding:4px 8px;background:rgba(251,191,36,.08);'
    'border:1px solid rgba(251,191,36,.3);border-radius:6px;color:#fde68a;white-space:pre-wrap;'
    'font:12px/1.3 Segoe UI,Arial,sans-serif}'
    '.dec-widget .dec-save{display:block;margin:6px auto 0;background:#f59e0b;color:#000;border:0;'
    'border-radius:8px;padding:7px 22px;font:700 13px Segoe UI,Arial,sans-serif;cursor:pointer}'
    '.dec-widget .dec-save:hover{background:#d97706}'
    '.slide.dec-slide .inner h2{font-size:22px;margin:0 0 6px;padding-bottom:5px}'
    '.slide.dec-slide .inner h3{font-size:12px;margin:2px 0 1px}'
    '.slide.dec-slide .inner blockquote{margin:1px 0 4px;padding:3px 8px;font-size:11px}'
    '.slide.dec-slide .inner p{margin:1px 0}'
)

def decision_widget_html(pairs):
    """Build a per-question response widget for a Decision slide.

    Each pair is {question, response}; we render a labeled textarea for each
    question so the facilitator can type the team's answer during the live
    presentation.
    """
    if not pairs:
        return ''
    q_parts = []
    for i, p in enumerate(pairs or []):
        q = _html.escape(str(p.get('question') or ''), quote=True)
        q_parts.append(
            '<div class="dec-q">'
            '<div class="dec-q-label">Q%d. %s</div>'
            '<textarea class="dec-q-ta" rows="2" data-q="%d" '
            'placeholder="Team response for Q%d..." '
            'autocomplete="off" spellcheck="false"></textarea>'
            '</div>' % (i + 1, q, i, i + 1)
        )
    return (
        '<div class="dec-widget" data-decision="1">'
        '<div class="dec-note">\u26A0\uFE0F Record the team\u2019s response to each question below.</div>'
        '<div class="dec-questions">' + ''.join(q_parts) + '</div>'
        '<button class="dec-save">Save responses \u2192</button>'
        '</div>'
    )

INJECT_LOG_HTML = '<div class="inj-log"></div>'


def role_picker_html(roles):
    """Checkbox grid letting the team select which roles participate."""
    opts = "\n".join(
        '<label class="role-opt"><input type="checkbox" value="%s">'
        '<span>%s<span class="ro-owner">%s</span></span></label>'
        % (_html.escape(str(r.get("role") or ""), quote=True),
           _html.escape(str(r.get("role") or "")),
           _html.escape(str(r.get("owner") or "")))
        for r in (roles or [])
    )
    return (
        '<div class="role-pick">'
        '<div class="inj-note">Select the roles participating in this exercise, then confirm.</div>'
        '<div class="role-opts">' + opts + '</div>'
        '<button class="role-confirm">Confirm participating roles \u2192</button>'
        '<div class="inj-saved" hidden></div>'
        '</div>'
    )


INJECT_JS = r"""
<script>
(function () {
  var responses = {};
  var decResponses = {};
  var slides = Array.prototype.slice.call(document.querySelectorAll('.slide'));
  var injectIdx = [];
  slides.forEach(function (s, i) { if (s.querySelector('.inj-widget')) injectIdx.push(i); });
  var injectLast = injectIdx.length ? injectIdx[injectIdx.length - 1] : -1;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"''\u2018\u2019]/g, function (c) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&rsquo;',"\u2018":'&lsquo;',"\u2019":'&rsquo;'}[c] || c;
    });
  }

  function initDecisionWidget(slide, idx) {
    // Textareas are pre-rendered in HTML by decision_widget_html().
    // This function is now a no-op — we only mark the widget as initialized.
    var widget = slide.querySelector('.dec-widget');
    if (!widget || widget.dataset.init) return;
    widget.dataset.init = '1';
  }

  function renderSlide(idx) {
    var slide = slides[idx];
    if (!slide) return;
    var widget = slide.querySelector('.inj-widget');
    if (widget) {
      var ta = widget.querySelector('.inj-ta');
      var saved = widget.querySelector('.inj-saved');
      var btn = widget.querySelector('.inj-next');
      if (responses[idx] != null) {
        if (ta) ta.style.display = 'none';
        if (saved) { saved.hidden = false; saved.textContent = responses[idx]; }
        if (btn) btn.textContent = 'Next inject \u2192';
      } else {
        if (ta) ta.style.display = '';
        if (saved) saved.hidden = true;
        if (btn) btn.textContent = (idx === injectLast) ? 'Finish exercise \u2192' : 'Save & next inject \u2192';
      }
    }
    var dw = slide.querySelector('.dec-widget');
    if (dw) {
      initDecisionWidget(slide, idx);
      var tas = dw.querySelectorAll('.dec-q-ta');
      var savedBox = dw.querySelector('.inj-saved');
      var dBtn = dw.querySelector('.dec-save');
      var existing = decResponses[idx];
      if (existing) {
        tas.forEach(function (t) { t.style.display = 'none'; });
        if (dBtn) dBtn.style.display = 'none';
        var summary = '';
        tas.forEach(function (t) {
          var qi = +t.dataset.q;
          var ans = existing[qi] || 'No response';
          summary += 'Q' + (qi + 1) + ': ' + ans + '\n\n';
        });
        if (!savedBox) {
          savedBox = document.createElement('div');
          savedBox.className = 'inj-saved';
          dw.appendChild(savedBox);
        }
        savedBox.hidden = false;
        savedBox.textContent = summary.trim();
      } else {
        tas.forEach(function (t) { t.style.display = ''; });
        if (dBtn) dBtn.style.display = '';
        if (savedBox) savedBox.hidden = true;
      }
    }
    var pick = slide.querySelector('.role-pick');
    if (pick) {
      var opts = pick.querySelector('.role-opts');
      var conf = pick.querySelector('.role-confirm');
      var saved2 = pick.querySelector('.inj-saved');
      if (responses[idx] != null) {
        if (opts) opts.style.display = 'none';
        if (conf) conf.style.display = 'none';
        if (saved2) { saved2.hidden = false; saved2.textContent = responses[idx]; }
      } else {
        if (opts) opts.style.display = '';
        if (conf) conf.style.display = '';
        if (saved2) saved2.hidden = true;
      }
    }
    var log = slide.querySelector('.inj-log');
    if (log) {
      var allKeys = Object.keys(responses);
      var decKeys = Object.keys(decResponses);
      if (!allKeys.length && !decKeys.length) {
        log.innerHTML = '<div class="inj-log-empty">No team responses recorded yet \u2014 walk the injects and record the team\u2019s decision at each point.</div>';
      } else {
        log.innerHTML = '<h4>Recorded team responses</h4>';
        allKeys.forEach(function (k) {
          var s = slides[+k];
          var title = s ? (s.getAttribute('data-name') || ('Inject ' + (+k + 1))) : ('Inject ' + (+k + 1));
          log.innerHTML += '<div class="inj-log-item"><b>' + esc(title) + '</b><span class="r">' + esc(responses[k]) + '</span></div>';
        });
        decKeys.forEach(function (k) {
          var s = slides[+k];
          var title = s ? (s.getAttribute('data-name') || ('Decision ' + (+k + 1))) : ('Decision ' + (+k + 1));
          var ans = decResponses[k];
          var text = Object.keys(ans).sort().map(function (qi) {
            return 'Q' + (+qi + 1) + ': ' + ans[qi];
          }).join('\n\n');
          log.innerHTML += '<div class="inj-log-item"><b>' + esc(title) + '</b><span class="r">' + esc(text) + '</span></div>';
        });
      }
    }
  }

  document.addEventListener('click', function (e) {
    var conf = e.target.closest('.role-confirm');
    if (conf) {
      var slide = conf.closest('.slide');
      var idx = slides.indexOf(slide);
      var picked = Array.prototype.slice.call(slide.querySelectorAll('.role-opt input:checked'))
        .map(function (i) { return i.value; });
      responses[idx] = picked.length ? ('Participating roles: ' + picked.join(', ')) : 'No roles selected.';
      renderSlide(idx);
      return;
    }
    var dBtn = e.target.closest('.dec-save');
    if (dBtn) {
      var dSlide = dBtn.closest('.slide');
      var dIdx = slides.indexOf(dSlide);
      var tas = dSlide.querySelectorAll('.dec-q-ta');
      var ans = {};
      var hasAny = false;
      tas.forEach(function (t) {
        var v = t.value.trim();
        ans[+t.dataset.q] = v || 'No response';
        if (v) hasAny = true;
      });
      if (!hasAny) { return; }
      decResponses[dIdx] = ans;
      renderSlide(dIdx);
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
      return;
    }
    var btn = e.target.closest('.inj-next');
    if (!btn) return;
    var slide = btn.closest('.slide');
    var idx = slides.indexOf(slide);
    var ta = slide.querySelector('.inj-ta');
    responses[idx] = (ta && ta.value.trim()) ? ta.value.trim() : 'No response recorded.';
    renderSlide(idx);
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
  });

  document.addEventListener('keydown', function (e) {
    var t = e.target;
    if (t && (t.tagName === 'TEXTAREA' || t.tagName === 'INPUT' || t.contentEditable === 'true')) {
      e.stopImmediatePropagation();
      e.stopPropagation();
    }
  }, true);

  var mo = new MutationObserver(function () {
    var active = document.querySelector('.slide.active');
    if (active) renderSlide(slides.indexOf(active));
  });
  slides.forEach(function (s) { mo.observe(s, { attributes: true, attributeFilter: ['class'] }); });
  var stage = document.getElementById('stage');
  if (stage) mo.observe(stage, { childList: true });
  renderSlide(slides.indexOf(document.querySelector('.slide.active')));
})();
</script>
"""




def build_presentation(name, slides, injects=None, meta=None):
    parts = []
    has_inject_ui = False
    for i, s in enumerate(slides or []):
        layout = (s.get("layout") or "content").strip().lower()
        if layout not in LAYOUTS:
            layout = "content"
        sname = _html.escape(str(s.get("name") or "Slide %d" % (i + 1)).strip(), quote=True)
        slide_html = _render_slide_html(s)
        sname_raw = str(s.get("name") or "")
        if sname_raw.startswith("Inject #"):
            slide_html += INJECT_WIDGET_HTML
            has_inject_ui = True
        elif sname_raw.startswith("Decision"):
            pairs = ((s.get("data") or {}).get("pairs") or [])
            slide_html += decision_widget_html(pairs)
            has_inject_ui = True
        elif sname_raw == "Roles":
            slide_html += role_picker_html((s.get("data") or {}).get("roles"))
            has_inject_ui = True
        elif sname_raw == "Hotwash" or sname_raw.startswith("After Action Executive"):
            slide_html += INJECT_LOG_HTML
            has_inject_ui = True
        extra = ' roles' if sname_raw == 'Roles' else ''
        if sname_raw.startswith('Decision'):
            extra += ' dec-slide'
        data_h = ''
        if sname_raw.startswith('After Action Executive'):
            extra += ' aar-slide'
            data_h = ' data-h="940"'
        parts.append('<section class="slide %s%s" data-name="%s"%s><div class="inner">%s</div></section>'
                     % (layout, extra, sname, data_h, slide_html))
    body = "\n".join(parts) or '<div class="empty-deck">This presentation has no slides yet.</div>'
    ex_css = ex_js = ""
    if has_inject_ui or injects:
        ex_css = INJECT_CSS + DECISION_CSS
        ex_js = INJECT_JS
    return (PRESENT_PAGE.replace("%%TITLE%%", _html.escape(name))
                        .replace("%%SLIDES%%", body)
                        .replace("%%INJECT_CSS%%", ex_css)
                        .replace("%%INJECT_HTML%%", "")
                        .replace("%%INJECT_JS%%", ex_js))


def build_afteraction(name, slides):
    """Word-ready After Action Executive Summary built from the deck's summary
    slide data, following the standard executive-summary template:
    title block + control framework line, meta table, executive summary with
    callout, readiness score, highlights, capability assessment, lessons,
    framework alignment, recommendations, CAPA action plan, roadmap, evidence
    pack, KPIs, and executive decisions requested. Sections with no data are
    skipped so older decks still export cleanly.

    Returns (html, None) on success or (None, error_message).
    """
    summary = next((s for s in (slides or []) if (s.get("name") or "").startswith("After Action Executive")), None)
    if summary is None:
        return None, "This deck has no After Action Executive Summary slide."
    data = (summary.get("data") or {}) or {}

    def rows(key):
        v = data.get(key) or []
        return v if isinstance(v, list) else []

    def esc(v):
        return _html.escape("" if v is None else str(v))

    def table(headers, keys, rws):
        if not rws:
            return ""
        out = ["<table><tr>"]
        out += ["<th>%s</th>" % esc(h) for h in headers]
        out.append("</tr>")
        for r in rws:
            cells = [(r.get(k) if isinstance(r, dict) else "") for k in keys]
            out.append("<tr>" + "".join("<td>%s</td>" % esc(c) for c in cells) + "</tr>")
        out.append("</table>")
        return "".join(out)

    def bullets(items):
        return "<ul>" + "".join("<li>%s</li>" % esc(i) for i in items) + "</ul>" if items else ""

    def numbered(items):
        return "<ol>" + "".join("<li>%s</li>" % esc(i) for i in items) + "</ol>" if items else ""

    def section(title, inner):
        return '<div class="aar-section"><h2>%s</h2>%s</div>' % (esc(title), inner)

    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    exercise = data.get("exercise") if isinstance(data.get("exercise"), dict) else {}
    ex_name = str(exercise.get("name") or name)
    ex_date = str(exercise.get("date") or "")

    head = ["<div class='report-head'><h1>Executive Summary</h1>"]
    head.append("<p>%s%s</p>" % (esc(ex_name), (" &middot; " + esc(ex_date)) if ex_date else ""))
    if meta.get("framework"):
        head.append("<div class='framework'>%s</div>" % esc(meta["framework"]))
    head.append("</div>")

    parts = []

    if meta:
        meta_rows = ""
        for k, label in (("prepared_for", "Prepared for"), ("prepared_date", "Prepared date"),
                         ("source_document", "Source document"), ("status", "Status")):
            if meta.get(k):
                meta_rows += "<tr><td class='k'>%s</td><td>%s</td></tr>" % (esc(label), esc(meta[k]))
        if meta_rows:
            parts.append("<table class='aar-meta'>%s</table>" % meta_rows)

    story = str(data.get("story") or "").strip()
    callout = str(data.get("executive_assessment") or "").strip()
    exec_inner = ""
    if story:
        exec_inner += "<p>%s</p>" % esc(story)
    if callout:
        exec_inner += "<div class='aar-callout'><b>Executive assessment:</b> %s</div>" % esc(callout)
    if exec_inner:
        parts.append(section("Executive Summary", exec_inner))

    score = data.get("score") if isinstance(data.get("score"), dict) else {}
    if any(score.get(k) for k in ("score", "rating", "risk", "priority")):
        parts.append(section(
            "Readiness Score",
            table(("Revised Score", "Readiness Rating", "Business Risk", "Executive Priority"),
                  ("score", "rating", "risk", "priority"), [score])
            + "<p class='aar-note'>Scoring is an internal executive readiness assessment derived from the "
              "exercise transcript; it is not a certification opinion.</p>"))

    if rows("highlights"):
        parts.append(section("Exercise Highlights", bullets(rows("highlights"))))

    if rows("capability"):
        parts.append(section("Executive Capability Assessment",
                             table(("Capability Domain", "Score", "Executive Assessment"),
                                   ("domain", "score", "assessment"), rows("capability"))))

    if rows("lessons"):
        parts.append(section("Key Lessons Learned", bullets(rows("lessons"))))

    if rows("framework_alignment"):
        parts.append(section(
            "Framework Alignment Summary",
            table(("Control Theme", "SOC 2 Focus", "TISAX AL3 / VDA ISA Focus", "ISO 27001/27002 Focus"),
                  ("theme", "soc2", "tisax", "iso"), rows("framework_alignment"))
            + "<p class='aar-note'>The mapping is intended for remediation planning and evidence collection; "
              "final applicability should be validated against the organization's audit scope and Statement of "
              "Applicability.</p>"))

    if rows("recommendations"):
        parts.append(section("Priority Recommendations", numbered(rows("recommendations"))))

    capa = rows("capa")
    if capa:
        if any(isinstance(r, dict) and r.get("target") for r in capa):
            capa_html = table(("Action", "Target", "Owner", "Framework Focus", "Evidence / Success Metric"),
                              ("item", "target", "owner", "framework_focus", "evidence"), capa)
        else:
            capa_html = table(("Action", "Type", "Owner", "Due"),
                              ("item", "type", "owner", "due"), capa)
        parts.append(section("Executive Action Plan (CAPA)", capa_html))

    if rows("roadmap"):
        parts.append(section("Roadmap View",
                             table(("Period", "Executive Milestones"),
                                   ("period", "milestones"), rows("roadmap"))))

    if rows("evidence"):
        parts.append(section("Audit-Ready Evidence Pack", bullets(rows("evidence"))))

    if rows("kpis"):
        parts.append(section("Recommended Executive KPIs",
                             table(("KPI", "Target"), ("kpi", "target"), rows("kpis"))))

    if rows("decisions"):
        parts.append(section("Executive Decisions Requested", bullets(rows("decisions"))))

    footer = ""
    if meta.get("reference"):
        footer = "<p class='aar-note'>Framework Reference Basis: %s</p>" % esc(meta["reference"])

    stamp = time.strftime("%Y-%m-%d")
    full = ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>Executive Summary — %s</title>"
            "<style>%s%s</style></head><body>%s%s%s</body></html>"
            ) % (esc(ex_name), DOC_STYLE, AFTERACTION_CSS, "".join(head), "".join(parts), footer)
    return full, None


def build_handout(name, slides):
    parts = []
    for i, s in enumerate(slides or []):
        sname = _html.escape(str(s.get("name") or "Slide %d" % (i + 1)).strip())
        parts.append('<section class="handout-slide"><div class="handout-label">%s</div>%s</section>'
                     % (sname, _render_slide_html(s)))
    body = "\n".join(parts) or "<p class='muted'>No slides yet.</p>"
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>%s</title>"
            "<style>%s%s</style></head><body>%s</body></html>"
            ) % (_html.escape(name), DOC_STYLE, HANDOUT_CSS, body)


class Handler(BaseHTTPRequestHandler):
    server_version = "DeckForge/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[DeckForge] %s\n" % (fmt % args))

    # -- helpers ------------------------------------------------------------

    def _send(self, code, body, ctype="application/json; charset=utf-8", headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # security hardening headers (harmless locally, useful when deployed)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
        except ValueError:
            n = 0
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    # -- auth helpers ---------------------------------------------------------

    def _session_token(self):
        raw = self.headers.get("Cookie", "")
        if not raw:
            return None
        c = _cookies.SimpleCookie()
        c.load(raw)
        m = c.get("df_session")
        return m.value if m else None

    def _new_session(self):
        tok = secrets.token_urlsafe(32)
        with _SESS_LOCK:
            _SESSIONS[tok] = time.time() + AUTH_TTL
        return tok

    def _valid_session(self):
        if not AUTH_PASSWORD:
            return True
        tok = self._session_token()
        if not tok:
            return False
        with _SESS_LOCK:
            exp = _SESSIONS.get(tok)
            if exp is None:
                return False
            if exp < time.time():
                _SESSIONS.pop(tok, None)
                return False
            _SESSIONS[tok] = time.time() + AUTH_TTL  # sliding expiry
            return True

    def _clear_session(self):
        tok = self._session_token()
        if tok:
            with _SESS_LOCK:
                _SESSIONS.pop(tok, None)

    def _login_blocked(self, ip):
        now = time.time()
        with _SESS_LOCK:
            stamps = [t for t in _LOGIN_ATTEMPTS.get(ip, []) if now - t < 300]
            if len(stamps) >= 10:
                _LOGIN_ATTEMPTS[ip] = stamps
                return True
            stamps.append(now)
            _LOGIN_ATTEMPTS[ip] = stamps
            return False

    def _auth_cookie(self, tok):
        return "df_session=%s; HttpOnly; SameSite=Lax; Path=/; Max-Age=%d" % (tok, AUTH_TTL)

    def _static(self, name):
        safe = os.path.basename(name)
        full = os.path.join(STATIC, safe)
        if not os.path.isfile(full):
            self._json(404, {"error": "not found"})
            return
        ext = os.path.splitext(safe)[1].lower()
        ctype = MIME.get(ext, "application/octet-stream")
        with open(full, "rb") as f:
            self._send(200, f.read(), ctype, {"Cache-Control": "no-cache"})

    # -- routes -------------------------------------------------------------

    def do_GET(self):
        path = urlsplit(self.path).path
        if AUTH_PASSWORD:
            if path == "/logout":
                self._clear_session()
                self._send(302, "", "text/html; charset=utf-8", {"Location": "/login"})
                return
            if path == "/login":
                if self._valid_session():
                    self._send(302, "", "text/html; charset=utf-8", {"Location": "/"})
                    return
                self._send(200, LOGIN_PAGE, "text/html; charset=utf-8")
                return
            if not self._valid_session():
                if not path.startswith("/api/"):
                    self._send(302, "", "text/html; charset=utf-8", {"Location": "/login"})
                    return
                self._json(401, {"error": "authentication required"})
                return
        if path in ("/", "/index.html"):
            self._static("index.html")
        elif path.startswith("/api/"):
            if path == "/api/decks":
                self._json(200, store.list_decks())
            elif path.startswith("/api/decks/"):
                did = path.rsplit("/", 1)[-1]
                d = store.get_deck(did)
                if d:
                    self._json(200, d)
                else:
                    self._json(404, {"error": "deck not found"})
            else:
                self._json(404, {"error": "unknown endpoint"})
        else:
            name = path.lstrip("/")
            if name and "/" not in name and os.path.exists(os.path.join(STATIC, name)):
                self._static(name)
            else:
                self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/api/login":
            if not AUTH_PASSWORD:
                self._json(404, {"error": "auth not enabled"})
                return
            if self._login_blocked(self.client_address[0]):
                self._json(429, {"error": "too many attempts — try again later"})
                return
            b = self._body()
            given = (b.get("password") or "").encode("utf-8")
            if not given or not hmac.compare_digest(given, AUTH_PASSWORD.encode("utf-8")):
                self._json(401, {"error": "invalid password"})
                return
            tok = self._new_session()
            self._send(200, json.dumps({"ok": True}), headers={"Set-Cookie": self._auth_cookie(tok)})
            return
        if AUTH_PASSWORD and not self._valid_session():
            self._json(401, {"error": "authentication required"})
            return
        if path == "/api/decks":
            b = self._body()
            name = (b.get("name") or "Untitled presentation").strip() or "Untitled presentation"
            slides = b.get("slides")
            if not isinstance(slides, list):
                slides = []
            d = store.create_deck(name, slides, b.get("injects"), b.get("meta"))
            self._json(201, d)
        elif path == "/api/render":
            b = self._body()
            try:
                h = renderer.render(b.get("body", ""), b.get("data", {}), html_mode=True,
                                    fill=bool(b.get("fill")))
                t = renderer.render(b.get("body", ""), b.get("data", {}), html_mode=False)
                errors, seen = [], set()
                for e in h["errors"] + t["errors"]:
                    if e not in seen:
                        seen.add(e)
                        errors.append(e)
                self._json(200, {
                    "html": h["html"], "text": t["text"],
                    "variables": h["variables"],
                    "form_variables": h["form_variables"],
                    "loop_variables": h["loop_variables"],
                    "errors": errors,
                })
            except Exception as exc:  # noqa: BLE001 - surface any renderer bug to the UI
                self._json(500, {"error": str(exc)})
        elif path == "/api/export":
            b = self._body()
            fmt = (b.get("format") or "presentation").lower()
            name = (b.get("name") or "presentation").strip() or "presentation"
            slides = b.get("slides")
            if not isinstance(slides, list):
                slides = []
            slug = re.sub(r"[^\w\- ]+", "", name).strip().replace(" ", "-") or "presentation"
            if fmt == "afteraction":
                full, err = build_afteraction(name, slides)
                if err:
                    self._json(400, {"error": err})
                    return
                ctype, ext = "application/msword", "doc"
            elif fmt == "handout":
                full, ctype, ext = build_handout(name, slides), "application/msword", "doc"
            else:
                full, ctype, ext = build_presentation(name, slides, b.get("injects"), b.get("meta")), "text/html; charset=utf-8", "html"
            self._send(200, full, ctype, {
                "Content-Disposition": "attachment; filename*=UTF-8''%s.%s" % (slug, ext)
            })
        else:
            self._json(404, {"error": "unknown endpoint"})

    def do_PUT(self):
        path = urlsplit(self.path).path
        if AUTH_PASSWORD and not self._valid_session():
            self._json(401, {"error": "authentication required"})
            return
        m = re.match(r"^/api/decks/([^/]+)$", path)
        if not m:
            self._json(404, {"error": "unknown endpoint"})
            return
        b = self._body()
        d = store.update_deck(m.group(1), name=b.get("name"), slides=b.get("slides"),
                              injects=b.get("injects"), meta=b.get("meta"))
        if d:
            self._json(200, d)
        else:
            self._json(404, {"error": "deck not found"})

    def do_DELETE(self):
        path = urlsplit(self.path).path
        if AUTH_PASSWORD and not self._valid_session():
            self._json(401, {"error": "authentication required"})
            return
        m = re.match(r"^/api/decks/([^/]+)$", path)
        if not m:
            self._json(404, {"error": "unknown endpoint"})
            return
        if store.delete_deck(m.group(1)):
            self._json(200, {"ok": True})
        else:
            self._json(404, {"error": "deck not found"})


def main():
    ap = argparse.ArgumentParser(description="DeckForge presentation builder")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8420)))
    ap.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    args = ap.parse_args()
    try:
        httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as exc:
        print("Could not bind to %s:%s — %s" % (args.host, args.port, exc))
        print("Try a different port:  python server.py --port 9000")
        sys.exit(1)
    print("=" * 56)
    print("  DeckForge - presentation builder")
    print("  Open:   http://%s:%s" % (args.host, args.port))
    print("  Press Ctrl+C to stop.")
    print("=" * 56)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DeckForge.")


if __name__ == "__main__":
    main()
