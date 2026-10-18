"""Replace INJECT_JS in server.py with the extended version that adds
interactive per-question response textareas to Decision slides."""

src = open('server.py', encoding='utf-8').read()

old_start = 'INJECT_JS = r"""'
old_end = '"""'

si = src.find(old_start)
ei = src.find(old_end, si + len(old_start))
if si < 0 or ei < 0:
    raise SystemExit('ERROR: could not find INJECT_JS boundaries')

# Build the new INJECT_JS using literal unicode chars (matching the file's convention)
NEW_INJECT_JS = (
'INJECT_JS = r"""\n'
'<script>\n'
'(function () {\n'
'  var responses = {};\n'
'  var decResponses = {};\n'
'  var slides = Array.prototype.slice.call(document.querySelectorAll(\'.slide\'));\n'
'  var injectIdx = [];\n'
"  slides.forEach(function (s, i) { if (s.querySelector('.inj-widget')) injectIdx.push(i); });\n"
'  var injectLast = injectIdx.length ? injectIdx[injectIdx.length - 1] : -1;\n'
'\n'
"  function esc(s) {\n"
"    return String(s == null ? '' : s).replace(/[&<>\"''\\u2018\\u2019]/g, function (c) {\n"
"      return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&rsquo;',\"\\u2018\":'&lsquo;',\"\\u2019\":'&rsquo;'}[c] || c;\n"
'    });\n'
'  }\n'
'\n'
'  function initDecisionWidget(slide, idx) {\n'
"    var widget = slide.querySelector('.dec-widget');\n"
"    if (!widget || widget.dataset.init) return;\n"
'    widget.dataset.init = \'1\';\n'
"    var questions = Array.prototype.slice.call(slide.querySelectorAll('h3'))\n"
'      .filter(function (h) { return /^Q\\d+/.test(h.textContent.trim()); });\n'
"    var taWrap = document.createElement('div');\n"
"    taWrap.className = 'dec-questions';\n"
'    questions.forEach(function (h, qi) {\n'
"      var label = document.createElement('div');\n"
"      label.className = 'dec-q-label';\n"
'      label.textContent = h.textContent.trim();\n'
"      var ta = document.createElement('textarea');\n"
"      ta.className = 'dec-q-ta';\n"
'      ta.rows = 4;\n'
"      ta.placeholder = 'Team response for Q' + (qi + 1) + '...';\n"
'      ta.dataset.q = qi;\n'
"      var qDiv = document.createElement('div');\n"
"      qDiv.className = 'dec-q';\n"
'      qDiv.appendChild(label);\n'
'      qDiv.appendChild(ta);\n'
'      taWrap.appendChild(qDiv);\n'
'    });\n'
"    var btn = widget.querySelector('.dec-save');\n"
'    widget.insertBefore(taWrap, btn);\n'
'  }\n'
'\n'
'  function renderSlide(idx) {\n'
'    var slide = slides[idx];\n'
'    if (!slide) return;\n'
"    var widget = slide.querySelector('.inj-widget');\n"
'    if (widget) {\n'
"      var ta = widget.querySelector('.inj-ta');\n"
"      var saved = widget.querySelector('.inj-saved');\n"
"      var btn = widget.querySelector('.inj-next');\n"
'      if (responses[idx] != null) {\n'
"        if (ta) ta.style.display = 'none';\n"
'        if (saved) { saved.hidden = false; saved.textContent = responses[idx]; }\n'
"        if (btn) btn.textContent = 'Next inject \\u2192';\n"
'      } else {\n'
"        if (ta) ta.style.display = '';\n"
'        if (saved) saved.hidden = true;\n'
"        if (btn) btn.textContent = (idx === injectLast) ? 'Finish exercise \\u2192' : 'Save & next inject \\u2192';\n"
'      }\n'
'    }\n'
"    var dw = slide.querySelector('.dec-widget');\n"
'    if (dw) {\n'
'      initDecisionWidget(slide, idx);\n'
"      var tas = dw.querySelectorAll('.dec-q-ta');\n"
"      var savedBox = dw.querySelector('.inj-saved');\n"
"      var dBtn = dw.querySelector('.dec-save');\n"
'      var existing = decResponses[idx];\n'
'      if (existing) {\n'
"        tas.forEach(function (t) { t.style.display = 'none'; });\n"
"        if (dBtn) dBtn.style.display = 'none';\n"
"        var summary = '';\n"
'        tas.forEach(function (t) {\n'
'          var qi = +t.dataset.q;\n'
"          var ans = existing[qi] || 'No response';\n"
"          summary += 'Q' + (qi + 1) + ': ' + ans + '\\n\\n';\n"
'        });\n'
"        if (!savedBox) {\n"
"          savedBox = document.createElement('div');\n"
"          savedBox.className = 'inj-saved';\n"
'          dw.appendChild(savedBox);\n'
'        }\n'
'        savedBox.hidden = false;\n'
'        savedBox.textContent = summary.trim();\n'
'      } else {\n'
"        tas.forEach(function (t) { t.style.display = ''; });\n"
"        if (dBtn) dBtn.style.display = '';\n"
'        if (savedBox) savedBox.hidden = true;\n'
'      }\n'
'    }\n'
"    var pick = slide.querySelector('.role-pick');\n"
'    if (pick) {\n'
"      var opts = pick.querySelector('.role-opts');\n"
"      var conf = pick.querySelector('.role-confirm');\n"
"      var saved2 = pick.querySelector('.inj-saved');\n"
'      if (responses[idx] != null) {\n'
"        if (opts) opts.style.display = 'none';\n"
"        if (conf) conf.style.display = 'none';\n"
'        if (saved2) { saved2.hidden = false; saved2.textContent = responses[idx]; }\n'
'      } else {\n'
"        if (opts) opts.style.display = '';\n"
"        if (conf) conf.style.display = '';\n"
'        if (saved2) saved2.hidden = true;\n'
'      }\n'
'    }\n'
"    var log = slide.querySelector('.inj-log');\n"
'    if (log) {\n'
'      var allKeys = Object.keys(responses);\n'
'      var decKeys = Object.keys(decResponses);\n'
'      if (!allKeys.length && !decKeys.length) {\n'
"        log.innerHTML = '<div class=\"inj-log-empty\">No team responses recorded yet \\u2014 walk the injects and record the team\\u2019s decision at each point.</div>';\n"
'      } else {\n'
"        log.innerHTML = '<h4>Recorded team responses</h4>';\n"
'        allKeys.forEach(function (k) {\n'
'          var s = slides[+k];\n'
"          var title = s ? (s.getAttribute('data-name') || ('Inject ' + (+k + 1))) : ('Inject ' + (+k + 1));\n"
"          log.innerHTML += '<div class=\"inj-log-item\"><b>' + esc(title) + '</b><span class=\"r\">' + esc(responses[k]) + '</span></div>';\n"
'        });\n'
'        decKeys.forEach(function (k) {\n'
'          var s = slides[+k];\n'
"          var title = s ? (s.getAttribute('data-name') || ('Decision ' + (+k + 1))) : ('Decision ' + (+k + 1));\n"
'          var ans = decResponses[k];\n'
'          var text = Object.keys(ans).sort().map(function (qi) {\n'
"            return 'Q' + (+qi + 1) + ': ' + ans[qi];\n"
"          }).join('\\n\\n');\n"
"          log.innerHTML += '<div class=\"inj-log-item\"><b>' + esc(title) + '</b><span class=\"r\">' + esc(text) + '</span></div>';\n"
'        });\n'
'      }\n'
'    }\n'
'  }\n'
'\n'
'  document.addEventListener(\'click\', function (e) {\n'
"    var conf = e.target.closest('.role-confirm');\n"
'    if (conf) {\n'
'      var slide = conf.closest(\'.slide\');\n'
'      var idx = slides.indexOf(slide);\n'
"      var picked = Array.prototype.slice.call(slide.querySelectorAll('.role-opt input:checked'))\n"
'        .map(function (i) { return i.value; });\n'
"      responses[idx] = picked.length ? ('Participating roles: ' + picked.join(', ')) : 'No roles selected.';\n"
'      renderSlide(idx);\n'
'      return;\n'
'    }\n'
"    var dBtn = e.target.closest('.dec-save');\n"
'    if (dBtn) {\n'
'      var dSlide = dBtn.closest(\'.slide\');\n'
'      var dIdx = slides.indexOf(dSlide);\n'
"      var tas = dSlide.querySelectorAll('.dec-q-ta');\n"
'      var ans = {};\n'
'      var hasAny = false;\n'
'      tas.forEach(function (t) {\n'
'        var v = t.value.trim();\n'
"        ans[+t.dataset.q] = v || 'No response';\n"
'        if (v) hasAny = true;\n'
'      });\n'
'      if (!hasAny) { return; }\n'
'      decResponses[dIdx] = ans;\n'
'      renderSlide(dIdx);\n'
"      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));\n"
'      return;\n'
'    }\n'
"    var btn = e.target.closest('.inj-next');\n"
'    if (!btn) return;\n'
'    var slide = btn.closest(\'.slide\');\n'
'    var idx = slides.indexOf(slide);\n'
"    var ta = slide.querySelector('.inj-ta');\n"
"    responses[idx] = (ta && ta.value.trim()) ? ta.value.trim() : 'No response recorded.';\n"
'    renderSlide(idx);\n'
"    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));\n"
'  });\n'
'\n'
'  document.addEventListener(\'keydown\', function (e) {\n'
"    if (e.target && (e.target.tagName === 'TEXTAREA' || e.target.classList.contains('dec-q-ta'))) {\n"
"      if (['Enter', ' ', 'PageDown', 'PageUp', 'ArrowRight', 'ArrowLeft'].indexOf(e.key) > -1) {\n"
'        e.stopPropagation();\n'
'      }\n'
'    }\n'
'  }, true);\n'
'\n'
'  var mo = new MutationObserver(function () {\n'
"    var active = document.querySelector('.slide.active');\n"
'    if (active) renderSlide(slides.indexOf(active));\n'
'  });\n'
"  slides.forEach(function (s) { mo.observe(s, { attributes: true, attributeFilter: ['class'] }); });\n"
"  var stage = document.getElementById('stage');\n"
'  if (stage) mo.observe(stage, { childList: true });\n'
"  renderSlide(slides.indexOf(document.querySelector('.slide.active')));\n"
'});\n'
'</script>\n'
'"""\n'
)

src2 = src[:si] + NEW_INJECT_JS + src[ei + len(old_end):]
open('server.py', 'w', encoding='utf-8').write(src2)
print('INJECT_JS replaced successfully (%d -> %d chars)' % (ei - si, len(NEW_INJECT_JS)))
