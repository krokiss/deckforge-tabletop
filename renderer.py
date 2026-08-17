"""DocForge template engine — a small mustache-style renderer (Python stdlib only).

Syntax:
    {{variable}}                    interpolate (HTML-escaped in HTML mode)
    {{{variable}}}                  interpolate raw
    {{&variable}}                   interpolate raw
    {{variable | filter}}           apply filters (chain with |)
    {{#if path}} ... {{else}} ... {{/if}}
    {{#unless path}} ... {{/if}}
    {{#each list}} ... {{/each}}    inside: {{this}} {{@index}} {{@number}}
                                    {{@first}} {{@last}} {{@length}}
    {{! comment }}

Dotted paths are supported: {{client.address.city}}.
Inside an {{#each}} loop, paths resolve against the current item first,
then fall back to the outer scope.
"""

import html as _html
import json
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Tokenizing & parsing
# ---------------------------------------------------------------------------

TOKEN_RE = re.compile(r"\{\{\{(.*?)\}\}\}|\{\{(.*?)\}\}")


def tokenize(body):
    tokens = []
    pos = 0
    for m in TOKEN_RE.finditer(body):
        if m.start() > pos:
            tokens.append(("text", body[pos:m.start()]))
        raw, normal = m.group(1), m.group(2)
        if raw is not None:
            tokens.append(("tag", "&" + raw))
        else:
            tokens.append(("tag", normal))
        pos = m.end()
    if pos < len(body):
        tokens.append(("text", body[pos:]))
    return tokens


def _is_comment(c):
    return c.startswith("!")


def parse(tokens):
    root = {"type": "root", "body": []}
    stack = [root]
    errors = []
    for kind, content in tokens:
        if kind == "text":
            stack[-1]["body"].append({"type": "text", "text": content})
            continue
        c = content.strip()
        if not c or _is_comment(c):
            continue
        if c.startswith("#if "):
            node = {"type": "if", "cond": c[4:].strip(), "invert": False, "body": [], "else": None}
            stack[-1]["body"].append(node)
            stack.append(node)
        elif c.startswith("#unless "):
            node = {"type": "if", "cond": c[8:].strip(), "invert": True, "body": [], "else": None}
            stack[-1]["body"].append(node)
            stack.append(node)
        elif c.startswith("#each "):
            node = {"type": "each", "expr": c[6:].strip(), "body": []}
            stack[-1]["body"].append(node)
            stack.append(node)
        elif c == "else":
            if len(stack) < 2:
                errors.append("{{else}} found outside of a block")
                continue
            top = stack.pop()
            if top["type"] != "if":
                errors.append("{{else}} must follow an {{#if}} block")
                stack.append(top)
                continue
            top["else"] = []
            stack.append({"type": "_else", "body": top["else"], "close": "if"})
        elif c.startswith("/"):
            close = c[1:].strip()
            if len(stack) < 2:
                errors.append("Unexpected {{/%s}}" % close)
                continue
            top = stack.pop()
            expected = top.get("close", top["type"])
            if close and close != expected:
                errors.append("{{/%s}} does not close {{#%s}}" % (close, expected))
        else:
            stack[-1]["body"].append({"type": "expr", "raw": c})
    if len(stack) > 1:
        top = stack[-1]
        if top["type"] == "if":
            what = "#if %s" % (top.get("cond") or "?")
        elif top["type"] == "each":
            what = "#each %s" % (top.get("expr") or "?")
        else:
            what = top.get("close") or "?"
        errors.append("Unclosed block: {{%s}}" % what)
    return root, errors


# ---------------------------------------------------------------------------
# Values, filters, resolution
# ---------------------------------------------------------------------------

def _truthy(v):
    if v is None or v is False:
        return False
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v.strip().lower() not in ("", "0", "false", "no", "none", "null", "undefined", "nil")
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return bool(v)


def _to_number(v):
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        try:
            return float(v.replace(",", "").replace("$", "").strip())
        except ValueError:
            return None
    return None


def _f_upper(v, a): return str(v).upper()


def _f_lower(v, a): return str(v).lower()


def _f_title(v, a): return str(v).title()


def _f_capitalize(v, a):
    s = str(v)
    return s[:1].upper() + s[1:] if s else s


def _f_trim(v, a): return str(v).strip()


def _f_length(v, a):
    try:
        return len(v)
    except TypeError:
        return len(str(v))


def _f_default(v, a):
    if v is None or v == "" or v == [] or v == {} or v is False:
        return a
    return v


def _f_number(v, a):
    n = _to_number(v)
    if n is None:
        return v
    if n == int(n):
        return f"{int(n):,}"
    return f"{n:,.2f}".rstrip("0").rstrip(".")


def _f_money(v, a):
    n = _to_number(v)
    if n is None:
        return v
    sym = a if a else "$"
    return f"{sym}{n:,.2f}"


def _f_date(v, a):
    if not isinstance(v, str) or not v:
        return v
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return v
    if a:
        try:
            return dt.strftime(a)
        except ValueError:
            return v
    return dt.strftime("%Y-%m-%d")


def _f_join(v, a):
    if isinstance(v, list):
        sep = a if a else ", "
        return sep.join(str(x) for x in v)
    return v


def _f_json(v, a):
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, indent=2)
    return v


def _f_sum(v, a):
    if not isinstance(v, list):
        return v
    total = 0.0
    for item in v:
        if a:
            n = item.get(a) if isinstance(item, dict) else None
            n = _to_number(n)
            if n is not None:
                total += n
        else:
            n = _to_number(item)
            if n is not None:
                total += n
    return int(total) if total == int(total) else total


def _f_raw(v, a): return v


FILTERS = {
    "upper": _f_upper, "lower": _f_lower, "title": _f_title,
    "capitalize": _f_capitalize, "trim": _f_trim, "length": _f_length,
    "default": _f_default, "number": _f_number, "money": _f_money,
    "currency": _f_money, "date": _f_date, "join": _f_join,
    "json": _f_json, "sum": _f_sum, "raw": _f_raw,
}


def _resolve(path, scopes, ctx, meta):
    """Resolve a dotted path. Returns (value, resolved_path).

    `scopes` is the scope stack (innermost last); `ctx` holds the matching
    data path prefix for each scope (e.g. ('items', '2') inside the third
    iteration of {{#each items}}). The resolved path lets the fill-in preview
    write values back to the exact location they came from — even when a name
    falls through to an outer scope.
    """
    path = path.strip()
    if not path:
        return "", None
    if path == "this":
        return scopes[-1] if scopes else None, (ctx[-1] if ctx else ())
    if path.startswith("@"):
        if meta and path[1:] in meta:
            return meta[path[1:]], None
        return None, None
    segs = [s for s in path.split(".") if s]
    if not segs:
        return None, None
    first = segs[0]
    if first == "this":
        cur = scopes[-1] if scopes else None
        p = list(ctx[-1]) if ctx else []
        for s in segs[1:]:
            if isinstance(cur, dict) and s in cur:
                cur = cur[s]
                p.append(s)
            elif isinstance(cur, list) and s.lstrip("-").isdigit():
                i = int(s)
                if 0 <= i < len(cur):
                    cur = cur[i]
                    p.append(s)
                else:
                    cur = None
                    break
            else:
                cur = None
                break
        return cur, tuple(p)
    best = None
    for idx in range(len(scopes) - 1, -1, -1):
        scope = scopes[idx]
        if isinstance(scope, dict) and first in scope:
            cur = scope[first]
            p = list(ctx[idx]) + segs
            ok = True
            for s in segs[1:]:
                if isinstance(cur, dict) and s in cur:
                    cur = cur[s]
                elif isinstance(cur, list) and s.lstrip("-").isdigit():
                    i = int(s)
                    if 0 <= i < len(cur):
                        cur = cur[i]
                    else:
                        ok = False
                        break
                else:
                    ok = False
                    break
            if ok:
                return cur, tuple(p)
            if best is None:
                best = (None, tuple(p))
    return best if best is not None else (None, None)


def _lexical_path(head, ctx):
    """Best-guess path for a variable that couldn't be resolved (e.g. no data
    yet) — the current loop context + the written path segments."""
    segs = [s for s in head.split(".") if s and s != "this" and not s.startswith("@")]
    if not segs:
        return None
    return (tuple(ctx[-1]) + tuple(segs)) if ctx else tuple(segs)


MD_SPECIALS = "*_`[]()~"


def _plain(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        v = "true" if v else "false"
    elif isinstance(v, float) and v.is_integer():
        v = int(v)
    elif isinstance(v, (dict, list)):
        v = json.dumps(v, ensure_ascii=False)
    return str(v)


def _shield(v):
    """HTML-escape a value and make every markdown-special character
    invisible to the inline rules (see _stringify)."""
    s = _html.escape(_plain(v), quote=False)
    for i, ch in enumerate(MD_SPECIALS):
        s = s.replace(ch, "\x02%d\x03" % i)
    return s


def _stringify(v, html_mode, raw):
    if not html_mode:
        return _plain(v)
    if raw:
        return _html.escape(_plain(v), quote=False)
    return "\ue000" + _shield(v) + "\ue001"


FILL_SEP = "\x1f"


def _fill_marker(path, value):
    """Marker for an editable blank: carries the data path so the fill-in
    preview can write the typed value back to the right location. The path
    itself is shielded too — variable names may contain markdown-special
    characters (e.g. action_items) that would otherwise be mangled by the
    inline rules."""
    shielded_path = path
    for i, ch in enumerate(MD_SPECIALS):
        shielded_path = shielded_path.replace(ch, "\x02%d\x03" % i)
    return "\ue000" + shielded_path + FILL_SEP + _shield(value) + "\ue001"


def _item_del_marker(path, idx):
    """Marker for a per-item delete button in the fill-in preview. Emitted
    right after each {{#each}} item so the ✕ lands inside the rendered item
    (e.g. inside its <li>); _restore_value turns it into a real button."""
    shielded_path = path
    for i, ch in enumerate(MD_SPECIALS):
        shielded_path = shielded_path.replace(ch, "\x02%d\x03" % i)
    return "\ue000" + "itemdel" + FILL_SEP + shielded_path + FILL_SEP + str(idx) + "\ue001"


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render_list(nodes, scopes, ctx, meta, html_mode, out, fill):
    for node in nodes:
        t = node["type"]
        if t == "text":
            out.append(node["text"])
        elif t == "expr":
            parts = [p.strip() for p in node["raw"].split("|")]
            head = parts[0]
            raw_flag = head.startswith("&")
            if raw_flag:
                head = head[1:].strip()
            val, rpath = _resolve(head, scopes, ctx, meta)
            has_filters = len(parts) > 1
            for fpart in parts[1:]:
                if not fpart:
                    continue
                fname, _, farg = fpart.partition(":")
                fname = fname.strip()
                farg = farg.strip()
                if len(farg) >= 2 and farg[0] == farg[-1] == '"':
                    farg = farg[1:-1]
                if fname in FILTERS:
                    val = FILTERS[fname](val, farg)
            if fill and html_mode and not raw_flag and not has_filters:
                # plain variable -> an editable blank in the fill-in preview
                if rpath is None:
                    rpath = _lexical_path(head, ctx)
                if rpath is None or isinstance(val, (dict, list)):
                    out.append(_stringify(val, html_mode, raw_flag))
                else:
                    out.append(_fill_marker(".".join(rpath), val))
            else:
                s = _stringify(val, html_mode, raw_flag)
                if fill and html_mode:
                    # computed values (filters / raw) are shown read-only
                    out.append('<span class="tpl-computed" title="Auto-computed from other fields">' + s + "</span>")
                else:
                    out.append(s)
        elif t == "if":
            v = _truthy(_resolve(node["cond"], scopes, ctx, meta)[0])
            if node.get("invert"):
                v = not v
            if v:
                _render_list(node["body"], scopes, ctx, meta, html_mode, out, fill)
            elif node.get("else"):
                _render_list(node["else"], scopes, ctx, meta, html_mode, out, fill)
        elif t == "each":
            items, epath = _resolve(node["expr"], scopes, ctx, meta)
            if epath is None:
                epath = _lexical_path(node["expr"], ctx)
            if not isinstance(items, list):
                items = []
            total = len(items)
            for i, item in enumerate(items):
                m = dict(meta or {})
                m.update({"index": i, "number": i + 1, "first": i == 0,
                          "last": i == total - 1, "length": total})
                _render_list(node["body"], scopes + [item],
                             ctx + [tuple(epath) + (str(i),)],
                             m, html_mode, out, fill)
                if fill and html_mode and epath:
                    marker = _item_del_marker(".".join(epath), i)
                    if out:
                        tail = out[-1]
                        if tail.endswith("|\n"):
                            # table row: drop the ✕ inside the last cell
                            out[-1] = tail[:-2] + marker + "|\n"
                        elif tail.endswith("\n"):
                            # list item / paragraph: keep it on the item's line
                            out[-1] = tail[:-1] + marker + "\n"
                        else:
                            out.append(marker)
                    else:
                        out.append(marker)
            if fill and html_mode and epath:
                e = _html.escape(".".join(epath), quote=True)
                out.append('\n<div class="tpl-loop-tools" data-loop="%s">'
                           '<span class="tpl-loop-label">%s</span>'
                           '<button type="button" class="tpl-add" data-loop="%s">+ Add item</button>'
                           '<button type="button" class="tpl-del" data-loop="%s">- Last</button>'
                           "</div>" % (e, e, e, e))


# ---------------------------------------------------------------------------
# Variable extraction (for auto-generated data forms)
# ---------------------------------------------------------------------------

def _walk_list(nodes, fn, depth):
    for node in nodes:
        _walk(node, fn, depth)


def _walk(node, fn, depth):
    fn(node, depth)
    if node["type"] in ("if", "each"):
        child_depth = depth + (1 if node["type"] == "each" else 0)
        _walk_list(node["body"], fn, child_depth)
        if node.get("else"):
            _walk_list(node["else"], fn, depth)


def extract_variables(root):
    """All referenced paths (for the insert-variable menu)."""
    out, seen = [], set()

    def visit(node, depth):
        def add(path):
            path = (path or "").strip()
            if not path or path == "this" or path.startswith("@"):
                return
            if path not in seen:
                seen.add(path)
                out.append(path)

        if node["type"] == "expr":
            head = node["raw"].split("|")[0].strip()
            if head.startswith("&"):
                head = head[1:].strip()
            add(head)
        elif node["type"] in ("if", "each"):
            add(node.get("cond") or node.get("expr") or "")

    _walk_list(root["body"], visit, 0)
    return out


def extract_loop_variables(root):
    """Paths used as the argument of an {{#each}} block."""
    out, seen = [], set()

    def visit(node, depth):
        if node["type"] == "each":
            path = (node.get("expr") or "").strip()
            if path and path not in seen:
                seen.add(path)
                out.append(path)

    _walk_list(root["body"], visit, 0)
    return out


def extract_form_variables(root):
    """Top-level paths only — excludes fields referenced solely inside
    {{#each}} loops (those belong to the loop's own data, edited as JSON)."""
    outside, anywhere = [], []
    seen_o, seen_a = set(), set()

    def visit(node, depth):
        def add(path, to):
            path = (path or "").strip()
            if not path or path == "this" or path.startswith("@"):
                return
            if path not in seen_a:
                seen_a.add(path)
                anywhere.append(path)
            if depth == 0 and path not in seen_o:
                seen_o.add(path)
                outside.append(path)

        if node["type"] == "expr":
            head = node["raw"].split("|")[0].strip()
            if head.startswith("&"):
                head = head[1:].strip()
            add(head, outside)
        elif node["type"] in ("if", "each"):
            add(node.get("cond") or node.get("expr") or "", outside)

    _walk_list(root["body"], visit, 0)
    return outside


# ---------------------------------------------------------------------------
# Markdown -> HTML (applied to the whole rendered doc in HTML mode)
# ---------------------------------------------------------------------------

_INLINE_RE = [
    (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)"), r"<em>\1</em>"),
    (re.compile(r"(?<!_)_([^_]+)_(?!_)"), r"<em>\1</em>"),
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)"), r'<a href="\2">\1</a>'),
    (re.compile(r"~~(.+?)~~"), r"<del>\1</del>"),
]


def _inline(s):
    for rx, rep in _INLINE_RE:
        s = rx.sub(rep, s)
    return s


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_RE = re.compile(r"^([-*+])\s+(.*)$")
_OLIST_RE = re.compile(r"^\d+\.\s+(.*)$")
_SEP_RE = re.compile(r"^\|?\s*:?-{3,}\s*(\|\s*:?-{3,}\s*)+\|?$")


def _is_ul(s):
    return bool(_LIST_RE.match(s))


def _is_ol(s):
    return bool(_OLIST_RE.match(s))


def _md_to_html(text):
    lines = text.split("\n")
    out = []
    in_list = None

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</%s>" % in_list)
            in_list = None

    def next_nonblank(j):
        while j < len(lines) and not lines[j].strip():
            j += 1
        return j

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            # blank line inside a list: keep the list open if the next
            # non-blank line continues it (CommonMark loose-list behaviour).
            if in_list:
                j = next_nonblank(i + 1)
                nxt = lines[j].strip() if j < len(lines) else ""
                if (in_list == "ul" and _is_ul(nxt)) or (in_list == "ol" and _is_ol(nxt)):
                    i += 1
                    continue
                close_list()
            out.append("")
            i += 1
            continue
        # table
        if "|" in stripped and i + 1 < len(lines) and _SEP_RE.match(lines[i + 1].strip()):
            headers = [h.strip() for h in stripped.strip("|").split("|")]
            i += 2
            rows = []
            # blank lines between rows are fine — {{#each}} loops naturally
            # leave gaps, and the rows belong to the same table
            while i < len(lines):
                row_line = lines[i].strip()
                if not row_line:
                    i += 1
                    continue
                if "|" not in row_line:
                    break
                rows.append([c.strip() for c in row_line.strip("|").split("|")])
                i += 1
            close_list()
            t = ["<table><thead><tr>"]
            t += ["<th>%s</th>" % _inline(h) for h in headers]
            t += ["</tr></thead><tbody>"]
            for r in rows:
                t.append("<tr>")
                t += ["<td>%s</td>" % _inline(c) for c in r]
                t.append("</tr>")
            t.append("</tbody></table>")
            out.append("".join(t))
            continue
        # code fence
        if stripped.startswith("```"):
            close_list()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            out.append("<pre><code>%s</code></pre>" % _html.escape("\n".join(buf)))
            i += 1
            continue
        m = _HEADER_RE.match(stripped)
        if m:
            close_list()
            out.append("<h%d>%s</h%d>" % (len(m.group(1)), _inline(m.group(2)), len(m.group(1))))
            i += 1
            continue
        if stripped in ("---", "***", "___"):
            close_list()
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith("> "):
            close_list()
            out.append("<blockquote>%s</blockquote>" % _inline(stripped[2:]))
            i += 1
            continue
        if stripped.startswith("<"):
            # raw HTML line — pass through untouched
            close_list()
            out.append(line)
            i += 1
            continue
        m = _LIST_RE.match(stripped)
        if m:
            if in_list != "ul":
                close_list()
                out.append("<ul>")
                in_list = "ul"
            out.append("<li>%s</li>" % _inline(m.group(2)))
            i += 1
            continue
        m = _OLIST_RE.match(stripped)
        if m:
            if in_list != "ol":
                close_list()
                out.append("<ol>")
                in_list = "ol"
            out.append("<li>%s</li>" % _inline(m.group(1)))
            i += 1
            continue
        if in_list:
            # a non-list, non-blank line closes the current list
            close_list()
        close_list()
        out.append("<p>%s</p>" % _inline(stripped))
        i += 1
    close_list()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

VALUE_MARK_RE = re.compile("\ue000(.*?)\ue001", re.S)


def _unshield(s):
    for i, ch in enumerate(MD_SPECIALS):
        s = s.replace("\x02%d\x03" % i, ch)
    return s


def _restore_value(match, fill=False):
    content = match.group(1)
    if content.startswith("itemdel" + FILL_SEP):
        _, path, idx = content.split(FILL_SEP, 2)
        path = _unshield(path)
        path_esc = _html.escape(path, quote=True)
        return ('<button type="button" class="tpl-item-del" data-loop="%s" data-idx="%s" '
                'title="Delete this item">\u2715</button>' % (path_esc, idx))
    if FILL_SEP in content:
        path, shielded = content.split(FILL_SEP, 1)
        path = _unshield(path)
        value = _unshield(shielded)
        if not fill:
            return value
        path_esc = _html.escape(path, quote=True)
        ph = _html.escape(path.rsplit(".", 1)[-1], quote=True)
        # the value is already &<>-escaped by _shield (quote=False left
        # quotes untouched) — only escape quotes for the attribute, or values
        # like "a & b" would be double-escaped to "a &amp;amp; b"
        val_esc = value.replace('"', '&quot;')
        if "\n" in value or len(value) > 60:
            # long values (narrative paragraphs) edit as a textarea
            if path == "story":
                # the executive summary's narrative is the centerpiece of the
                # AAR slide — render it as a large, clearly editable box
                return ('<textarea class="tpl-fill story-edit" rows="7" data-path="%s" '
                        'placeholder="Type the executive summary here…" '
                        'autocomplete="off" spellcheck="false">%s</textarea>'
                        % (path_esc, val_esc))
            return ('<textarea class="tpl-fill" rows="4" data-path="%s" '
                    'placeholder="%s" autocomplete="off" spellcheck="false">%s</textarea>'
                    % (path_esc, ph, val_esc))
        return ('<input class="tpl-fill" type="text" data-path="%s" value="%s" '
                'placeholder="%s" autocomplete="off" spellcheck="false">'
                % (path_esc, val_esc, ph))
    return _unshield(content)


def render(template, data, html_mode=True, fill=False):
    """Render a template against a data object.

    Returns a dict with the rendered output ('html' or 'text' depending on
    html_mode), a list of 'variables', and a list of 'errors'.

    With fill=True (HTML mode), every plain variable becomes an editable
    <input class="tpl-fill" data-path="..."> blank and each {{#each}} loop
    gains an add/remove control bar — the fill-in-the-blank preview.
    """
    tokens = tokenize(template or "")
    root, errors = parse(tokens)
    scopes = [data if isinstance(data, dict) else {}]
    ctx = [()]
    out = []
    _render_list(root["body"], scopes, ctx, None, html_mode, out, fill)
    result = "".join(out)
    if html_mode:
        result = VALUE_MARK_RE.sub(lambda m: _restore_value(m, fill), _md_to_html(result))
    return {
        "html" if html_mode else "text": result,
        "variables": extract_variables(root),
        "form_variables": extract_form_variables(root),
        "loop_variables": extract_loop_variables(root),
        "errors": errors,
    }
