#!/usr/bin/env python3
"""weekly.py — DeckForge weekly maintenance (stdlib only).

Runs four steps in order, logging every line to data/weekly.log:

  pull     fetch and fast-forward the checkout to origin/main
  archive  copy completed runs from the live site into data/history/
           (history never goes into git - this folder is local + backup only)
  deploy   push local commits so the Render container redeploys
  package  refresh the backup mirror and rebuild the transfer zip

The live-site password is read from DECKFORGE_LIVE_PASSWORD or the first
line of data/.live_password (gitignored, never printed). Without it the
archive step is skipped and everything else still runs.

Usage
-----
  python weekly.py               # full pass
  python weekly.py --dry-run     # say what would happen, change nothing
  python weekly.py --no-deploy   # skip the push/Render step
  python weekly.py --no-pull     # skip the git fast-forward

Scheduling (Windows, weekly on Sunday 09:00)
--------------------------------------------
  schtasks /Create /TN "DeckForge weekly" /SC WEEKLY /D SUN /ST 09:00 ^
           /TR "\"%CD%\\weekly.cmd\"" /F

The live site is https://deckforge-tabletop.onrender.com by default; override
with DECKFORGE_SITE (for example http://127.0.0.1:8420).
"""

import argparse
import datetime
import http.cookiejar
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.environ.get("DECKFORGE_SITE", "https://deckforge-tabletop.onrender.com").rstrip("/")
PASSWORD_FILE = os.path.join(ROOT, "data", ".live_password")
LOG = os.path.join(ROOT, "data", "weekly.log")


def log(msg):
    line = "%s  %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
    except OSError:
        pass


def run(cmd):
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, str(exc)
    return p.returncode, (p.stdout + p.stderr).strip()


def node_binary():
    found = shutil.which("node")
    if found:
        return found
    fallback = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs", "node.exe")
    return fallback if os.path.isfile(fallback) else ""


def live_password():
    pw = os.environ.get("DECKFORGE_LIVE_PASSWORD", "").strip()
    if pw:
        return pw
    try:
        with open(PASSWORD_FILE, encoding="utf-8") as f:
            return f.readline().strip()
    except OSError:
        return ""


# -- steps ------------------------------------------------------------------
def step_pull(dry):
    rc, out = run(["git", "fetch", "origin", "main"])
    if rc:
        return log("pull: fetch failed - %s" % out.splitlines()[-1])
    rc, out = run(["git", "rev-list", "--count", "HEAD..origin/main"])
    behind = int(out) if rc == 0 and out.isdigit() else 0
    if not behind:
        return log("pull: already up to date")
    if dry:
        return log("pull: would fast-forward %d commit(s)" % behind)
    rc, out = run(["git", "pull", "--ff-only"])
    if rc:
        return log("pull: fast-forward FAILED - %s" % out.splitlines()[-1])
    log("pull: fast-forwarded %d commit(s)" % behind)


def fetch_live_runs(password):
    """Completed runs currently held by the live site (logs in when needed)."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    if password:
        body = json.dumps({"password": password}).encode("utf-8")
        req = urllib.request.Request(SITE + "/api/login", data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            opener.open(req, timeout=60).read()
        except urllib.error.HTTPError as exc:
            if exc.code != 404:  # 404 = auth not enabled (local instance)
                raise
    raw = opener.open(SITE + "/api/history/export", timeout=120).read()
    payload = json.loads(raw.decode("utf-8"))
    runs = payload.get("completed_exercises") if isinstance(payload, dict) else None
    return [r for r in (runs or []) if isinstance(r, dict) and r.get("id")]


def step_archive(dry):
    password = live_password()
    try:
        runs = fetch_live_runs(password)
    except urllib.error.HTTPError as exc:
        if exc.code == 401 and not password:
            return log("archive: the live site needs a password (set DECKFORGE_LIVE_PASSWORD "
                       "or data/.live_password) - skipped")
        return log("archive: live site answered HTTP %s - skipped" % exc.code)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return log("archive: could not reach %s (%s) - skipped" % (SITE, exc))

    import store

    known = {str(e.get("id")) for e in store._read_history()}
    new = [r for r in runs if str(r.get("id")) not in known]
    if not new:
        return log("archive: %d run(s) on the live site, nothing new" % len(runs))
    if dry:
        return log("archive: would import %d new run(s) from %s" % (len(new), SITE))
    added = 0
    for entry in new:
        try:
            store._write_history(entry)
            added += 1
        except OSError as exc:
            log("archive: could not save a run (%s)" % exc)
    log("archive: imported %d new run(s) into data/history" % added)


def step_deploy(dry):
    rc, out = run(["git", "rev-list", "--count", "origin/main..HEAD"])
    ahead = int(out) if rc == 0 and out.isdigit() else 0
    if not ahead:
        return log("deploy: nothing ahead of origin/main - Render already current")
    if dry:
        return log("deploy: would push %d commit(s) and trigger a Render deploy" % ahead)
    node = node_binary()
    if node:
        rc, out = run([node, "--check", os.path.join(ROOT, "static", "app.js")])
        if rc:
            return log("deploy: js check FAILED - push blocked")
        log("deploy: js check PASS")
    else:
        log("deploy: node not found - js check skipped")
    rc, out = run(["git", "push", "origin", "main"])
    if rc:
        return log("deploy: push FAILED - %s" % out.splitlines()[-1])
    log("deploy: pushed %d commit(s) - Render auto-deploys, ~10 min" % ahead)


def step_package(dry):
    for name in ("backup", "zip"):
        if dry:
            log("package: would run sync.py %s" % name)
            continue
        rc, out = run([sys.executable, os.path.join(ROOT, "sync.py"), name])
        last = out.splitlines()[-1] if out else ""
        log("package: sync.py %s %s%s" % (name, "ok" if rc == 0 else "FAILED", "" if rc == 0 else " - " + last))


def main(argv=None):
    ap = argparse.ArgumentParser(description="DeckForge weekly maintenance pass.")
    ap.add_argument("--dry-run", action="store_true", help="report only, change nothing")
    ap.add_argument("--no-pull", action="store_true", help="skip the git fast-forward")
    ap.add_argument("--no-archive", action="store_true", help="skip the live history pull")
    ap.add_argument("--no-deploy", action="store_true", help="skip the push/Render deploy")
    ap.add_argument("--no-package", action="store_true", help="skip backup + zip")
    args = ap.parse_args(argv)

    log("weekly: start%s" % (" (dry run)" if args.dry_run else ""))
    if not args.no_pull:
        step_pull(args.dry_run)
    if not args.no_archive:
        step_archive(args.dry_run)
    if not args.no_deploy:
        step_deploy(args.dry_run)
    if not args.no_package:
        step_package(args.dry_run)
    log("weekly: done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
