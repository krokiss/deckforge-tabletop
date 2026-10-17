#!/usr/bin/env python3
"""sync.py — DeckForge sync operation (stdlib only, Windows/macOS/Linux).

Keeps four targets in step:

  local    this checkout (the git repo rooted at this folder)
  backup   the portable copy on another drive (default: E:\\Project-Doc-Builder-Backup\\...)
  git      origin/main on github.com/krokiss/deckforge-tabletop
  render   auto-deploys whenever origin/main advances (Render detects the Dockerfile)

Commands
--------
  status     show drift across local / backup / git   (read-only, default)
  pull       git pull --ff-only, then mirror local -> backup
  backup     mirror local source files -> backup
  zip        rebuild the dated transfer zip in the backup folder
  push       commit local changes and push to origin (this is what deploys
             Render), then align the backup's git history
  sync       pull + backup + push — the full upstream/downstream pass

Flags
-----
  --dry-run       list what would change; change nothing
  --backup PATH   override the backup dir (or set DECKFORGE_BACKUP)
  -m MSG          commit message for `push`

Typical use
-----------
  python sync.py                # what is out of sync?  (safe, read-only)
  python sync.py sync --dry-run # preview a full pass
  python sync.py sync           # do the full pass (commit + push + Render deploy)
"""

import argparse
import datetime
import hashlib
import os
import subprocess
import sys
import time
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))

DEFAULT_BACKUP = os.path.join(
    r"E:\Project-Doc-Builder-Backup", "Project Doc Builder", ".freebuff")

# Never mirrored (runtime state, caches, logs, git internals — .git is kept
# in step with real git commands instead of a file copy).
SKIP_DIRS = {"__pycache__", ".git", ".freebuff"}
SKIP_SUFFIX = (".pyc", ".pyo", ".log", ".log.err", ".tmp")
SKIP_PREFIX = ("preview-",)
SKIP_FILES = {"desktop-v2.db", "desktop-v2.db-shm", "desktop-v2.db-wal"}

# How old (seconds) a file pair must be before we trust mtime comparison.
SKEW = 2.0


def backup_root(args):
    path = args.backup or os.environ.get("DECKFORGE_BACKUP") or DEFAULT_BACKUP
    return os.path.abspath(path)


def is_skipped(name):
    if name in SKIP_FILES:
        return True
    if name.startswith(SKIP_PREFIX):
        return True
    return name.endswith(SKIP_SUFFIX)


def iter_source(root):
    """Yield (relpath, abspath) for every mirrorable file under root."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not is_skipped(name):
                yield os.path.relpath(os.path.join(dirpath, name), root), \
                      os.path.join(dirpath, name)


def file_state(path):
    st = os.stat(path)
    return st.st_size, st.st_mtime


def differs(src, dst):
    try:
        s_size, s_mtime = file_state(src)
        d_size, d_mtime = file_state(dst)
    except OSError:
        return True
    if s_size != d_size:
        return True
    if abs(s_mtime - d_mtime) > SKEW:
        # same size but different mtime — hash to avoid false positives
        return digest(src) != digest(dst)
    return False


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def git(args_list, cwd=ROOT, check=True):
    proc = subprocess.run(["git"] + args_list, cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if check and proc.returncode != 0:
        raise RuntimeError("git %s failed:\n%s%s" % (
            " ".join(args_list), proc.stdout, proc.stderr))
    return proc


def copy_file(src, dst, dry_run):
    if dry_run:
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    import shutil
    shutil.copy2(src, dst)
    return True


def mirror(root_src, root_dst, dry_run):
    """Copy changed/new files root_src -> root_dst. Returns (copied, skipped)."""
    copied, same = [], 0
    if not os.path.isdir(root_dst):
        raise RuntimeError("backup not found: %s\n"
                           "Use --backup PATH or DECKFORGE_BACKUP." % root_dst)
    for rel, src in iter_source(root_src):
        dst = os.path.join(root_dst, rel)
        if differs(src, dst):
            copy_file(src, dst, dry_run)
            copied.append(rel)
        else:
            same += 1
    return copied, same


def cmd_status(args):
    bkp = backup_root(args)
    print("== local (git) ==")
    try:
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        dirty = git(["status", "--porcelain"]).stdout.splitlines()
        print("  branch: %s" % branch)
        print("  changes: %s" % ("%d file(s)" % len(dirty) if dirty else "clean"))
        for line in dirty[:10]:
            print("    %s" % line)
        if len(dirty) > 10:
            print("    ... %d more" % (len(dirty) - 10))
        fetched = git(["fetch", "--quiet"], check=False)
        if fetched.returncode == 0:
            ab = git(["rev-list", "--left-right", "--count",
                      "origin/main...main"]).stdout.strip()
            behind, ahead = ab.split()
            print("  vs origin/main: ahead %s, behind %s" % (ahead, behind))
        else:
            print("  vs origin/main: (fetch failed — offline?)")
    except RuntimeError as exc:
        print("  %s" % exc)

    print("== backup ==")
    print("  path: %s" % bkp)
    if not os.path.isdir(bkp):
        print("  MISSING — nothing to sync")
        return 0
    changed = []
    for rel, src in iter_source(ROOT):
        if differs(src, os.path.join(bkp, rel)):
            changed.append(rel)
    if changed:
        print("  %d file(s) differ:" % len(changed))
        for rel in changed[:15]:
            print("    %s" % rel)
        if len(changed) > 15:
            print("    ... %d more" % (len(changed) - 15))
    else:
        print("  up to date with local")
    return 0


def align_backup_git(bkp, dry_run):
    """Fetch in the backup clone and fast-forward it only when it is safe.

    A `reset --hard` in the backup rewrites its working tree, so it may only
    run when the local working tree is clean — i.e. every mirrored file is
    byte-identical to HEAD anyway and nothing of value can be clobbered.
    When local has uncommitted changes (the mirror just copied them), the
    reset would silently revert them, so we only fetch and report.
    """
    if not os.path.isdir(os.path.join(bkp, ".git")):
        return "backup has no git history (skipped)"
    fetch = git(["fetch", "--quiet", "origin"], cwd=bkp, check=False)
    if fetch.returncode != 0:
        return "backup fetch failed (offline?) — skipped"
    local_dirty = git(["status", "--porcelain"]).stdout.strip()
    if local_dirty:
        return ("local has uncommitted changes — backup working tree keeps the "
                "mirrored copies; run `python sync.py push` to advance git")
    b_remote = git(["rev-parse", "origin/main"], cwd=bkp, check=False)
    l_head = git(["rev-parse", "HEAD"], check=False)
    if b_remote.returncode != 0 or l_head.returncode != 0:
        return "could not compare revisions — skipped"
    if b_remote.stdout.strip() != l_head.stdout.strip():
        return ("backup git is behind local HEAD — run `python sync.py push` "
                "first, then re-run backup")
    if dry_run:
        return "backup git already aligned (would reset --hard origin/main)"
    git(["reset", "--hard", "origin/main"], cwd=bkp)
    return "backup git aligned to origin/main"


def cmd_pull(args):
    bkp = backup_root(args)
    print("== pull (downstream: git -> local) ==")
    res = git(["pull", "--ff-only"], check=False)
    if res.returncode != 0:
        print("pull refused (history diverged?) — resolve manually:\n"
              "%s%s" % (res.stdout, res.stderr))
        return 1
    print(res.stdout.strip() or "already up to date")
    print("== backup (downstream: local -> backup) ==")
    copied, same = mirror(ROOT, bkp, args.dry_run)
    for rel in copied:
        print("  copy  %s" % rel)
    print("  %d copied, %d unchanged%s" % (
        len(copied), same, " (dry-run)" if args.dry_run else ""))
    return 0


def cmd_backup(args):
    bkp = backup_root(args)
    print("== backup (downstream: local -> backup) ==")
    copied, same = mirror(ROOT, bkp, args.dry_run)
    for rel in copied:
        print("  copy  %s" % rel)
    print("  %d copied, %d unchanged%s" % (
        len(copied), same, " (dry-run)" if args.dry_run else ""))
    if not args.dry_run:
        print("  %s" % align_backup_git(bkp, args.dry_run))
    return 0


def cmd_push(args):
    bkp = backup_root(args)
    print("== push (upstream: local -> git -> Render) ==")
    dirty = git(["status", "--porcelain"]).stdout.splitlines()
    if not dirty:
        print("  nothing to commit — local already clean")
    elif args.dry_run:
        print("  would commit %d change(s):" % len(dirty))
        for line in dirty[:15]:
            print("    %s" % line)
    else:
        git(["add", "-A"])
        msg = args.message or ("Sync: %d file(s) updated (%s)" % (
            len(dirty), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        git(["commit", "-m", msg])
        print("  committed: %s" % msg)
    res = git(["push", "origin", "main"], check=False) if not args.dry_run \
        else None
    if args.dry_run:
        print("  would push origin/main (commit first, then Render auto-deploys; "
              "Dockerfile detected, ~10 min on free tier)")
        return 0
    if res.returncode != 0:
        print("  push failed:\n%s%s" % (res.stdout, res.stderr))
        return 1
    print("  pushed origin/main — Render now auto-deploys "
          "(Dockerfile detected; ~10 min on free tier)")
    if not args.dry_run:
        print("  %s" % align_backup_git(bkp, args.dry_run))
    return 0


def cmd_zip(args):
    bkp = backup_root(args)
    if not os.path.isdir(bkp):
        print("backup not found: %s" % bkp)
        return 1
    # zip folder = two levels up when backup is "<top>/Project Doc Builder/.freebuff"
    top = os.path.dirname(os.path.dirname(bkp)) \
        if os.path.basename(bkp) == ".freebuff" else os.path.dirname(bkp)
    today = datetime.date.today().isoformat()
    out = os.path.join(top, "DeckForge-Backup-%s.zip" % today)
    print("== zip (transfer copy) ==")
    if args.dry_run:
        print("  would write %s" % out)
        return 0
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in filenames:
                if name.startswith("DeckForge-Backup-") and name.endswith(".zip"):
                    continue  # never zip a zip
                if is_skipped(name):
                    continue
                full = os.path.join(dirpath, name)
                z.write(full, os.path.relpath(full, top))
                n += 1
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        entries = len(z.namelist())
    if bad:
        print("  FAILED integrity check at %s" % bad)
        return 1
    # retire older dated zips so only the current one remains
    for name in os.listdir(top):
        if name.startswith("DeckForge-Backup-") and name.endswith(".zip") \
                and name != os.path.basename(out):
            try:
                os.remove(os.path.join(top, name))
                print("  removed stale %s" % name)
            except OSError:
                pass
    print("  wrote %s — %d entries, integrity OK" % (out, entries))
    return 0


def cmd_sync(args):
    rc = cmd_pull(args)
    if rc:
        return rc
    rc = cmd_push(args)
    if rc:
        return rc
    return cmd_zip(args)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sync.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="status",
                    choices=["status", "pull", "backup", "zip", "push", "sync"])
    ap.add_argument("--dry-run", action="store_true",
                    help="list what would change; change nothing")
    ap.add_argument("--backup", help="backup directory "
                    "(default: %s, or $DECKFORGE_BACKUP)" % DEFAULT_BACKUP)
    ap.add_argument("-m", "--message", help="commit message for push")
    args = ap.parse_args(argv)

    started = time.time()
    handler = {"status": cmd_status, "pull": cmd_pull, "backup": cmd_backup,
               "zip": cmd_zip, "push": cmd_push, "sync": cmd_sync}[args.command]
    try:
        rc = handler(args)
    except RuntimeError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1
    print("done in %.1fs" % (time.time() - started))
    return rc


if __name__ == "__main__":
    sys.exit(main())
