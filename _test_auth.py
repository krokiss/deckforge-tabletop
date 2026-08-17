import json, os, subprocess, sys, time, urllib.request, urllib.error

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None

OPENER = urllib.request.build_opener(NoRedirect)

def req(port, path, method="GET", body=None, cookie=None, follow=True):
    url = "http://127.0.0.1:%d%s" % (port, path)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if cookie:
        r.add_header("Cookie", cookie)
    try:
        if follow:
            resp = urllib.request.urlopen(r, timeout=10)
        else:
            resp = OPENER.open(r, timeout=10)
        return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()

def start(port, env_extra=None):
    env = dict(os.environ); env["PORT"] = str(port); env["HOST"] = "127.0.0.1"
    if env_extra:
        env.update(env_extra)
    p = subprocess.Popen([sys.executable, "server.py"], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        try:
            c, _, _ = req(port, "/api/decks")
            if c:
                return p
        except Exception:
            pass
        time.sleep(0.25)
    p.kill()
    raise RuntimeError("server did not start on port %d" % port)

fails = []

def check(label, got, want):
    ok = got == want
    print(("PASS " if ok else "FAIL ") + label + " -> got %r, want %r" % (got, want))
    if not ok:
        fails.append(label)

# --- open mode (AUTH_PASSWORD unset) ---
p1 = start(9111)
try:
    c, h, _ = req(9111, "/api/decks")
    check("open mode /api/decks", c, 200)
    check("open mode nosniff header", h.get("X-Content-Type-Options"), "nosniff")
finally:
    p1.terminate(); p1.wait(timeout=5)

# --- auth mode ---
p2 = start(9112, {"AUTH_PASSWORD": "secret123"})
try:
    c, h, _ = req(9112, "/", follow=False)
    check("GET / no cookie", (c, h.get("Location")), (302, "/login"))
    c, _, _ = req(9112, "/api/decks")
    check("GET /api/decks no cookie", c, 401)
    c, _, _ = req(9112, "/api/login", "POST", {"password": "wrong"})
    check("login wrong password", c, 401)
    c, h, _ = req(9112, "/api/login", "POST", {"password": "secret123"})
    check("login correct", c, 200)
    cookie = h.get("Set-Cookie", "").split(";")[0]
    check("cookie issued", cookie.startswith("df_session="), True)
    c, _, raw = req(9112, "/api/decks", cookie=cookie)
    check("GET /api/decks with cookie", (c, len(json.loads(raw))), (200, 13))
    c, _, _ = req(9112, "/", cookie=cookie)
    check("GET / with cookie", c, 200)
    c, h, _ = req(9112, "/logout", cookie=cookie, follow=False)
    check("GET /logout", (c, h.get("Location")), (302, "/login"))
    c, _, _ = req(9112, "/api/decks", cookie=cookie)
    check("GET /api/decks after logout", c, 401)
    c, h, _ = req(9112, "/api/login", "POST", {"password": "secret123"})
    fresh = h.get("Set-Cookie", "").split(";")[0]
    c, h, _ = req(9112, "/login", cookie=fresh, follow=False)
    check("GET /login with valid cookie", (c, h.get("Location")), (302, "/"))
    c, h, _ = req(9112, "/api/decks")
    check("headers on 401", h.get("X-Content-Type-Options"), "nosniff")
    # rate limit: 10 allowed, 11th blocked
    blocked = None
    for i in range(11):
        c, _, _ = req(9112, "/api/login", "POST", {"password": "nope%d" % i})
        blocked = c
    check("login rate-limited after 11 attempts", blocked, 429)
finally:
    p2.terminate(); p2.wait(timeout=5)

print("\n%s" % ("ALL TESTS PASSED" if not fails else "FAILURES: %s" % fails))
sys.exit(1 if fails else 0)
