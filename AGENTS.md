# AGENTS.md — project rules for AI agents

> Two identical copies of this file are maintained on purpose: here at the
> workspace root (so every session finds it first) and at
> `Project Doc Builder/.freebuff/AGENTS.md` (committed to git). If the rule
> changes, update **both** so they stay identical.

## Standing rule: always commit, push, and back up

After **any** change or update in this project — code, docs, data, config —
complete all of the following before reporting the work done:

1. **Commit** the change to git with a clear, one-topic message.
   The git repository root is `Project Doc Builder/.freebuff/`.
2. **Push** to `origin/main` (remote: github.com/krokiss/deckforge-tabletop).
   Every push triggers the Render auto-deploy (~10 minutes on the free
   tier); mention the deploy in the report.
3. **Update both backups** from the repo root:

   ```
   python sync.py backup
   ```

   This mirrors the files to
   `E:\Project-Doc-Builder-Backup\Project Doc Builder\.freebuff` and
   fast-forwards that backup clone to origin/main.
4. **Verify all three locations agree** before finishing:

   ```
   git rev-parse HEAD                                            # local
   git ls-remote origin refs/heads/main                          # GitHub (authoritative)
   git -C "E:\Project-Doc-Builder-Backup\Project Doc Builder\.freebuff" rev-parse HEAD
   ```

   All three SHAs must be identical, `git status --porcelain` must be
   empty **both** locally and in the backup clone, and
   `python sync.py status` must show "ahead 0, behind 0" plus backup
   "up to date with local".

Do not report a change as finished while anything is uncommitted,
unpushed, or missing from the backups.

## Push gate — do not bypass

`python sync.py push` runs `node --check static/app.js` before staging
anything. A JavaScript syntax error blocks the push (exit 1) before a
single file is staged; fix the error — never weaken or skip the check
just to get a push through. If node is not installed the check prints
SKIPPED (warning) and the push proceeds.

## Environment notes

- Node.js (v26.12.1, latest release; npm 11.20.0 — upgraded from v24
  LTS on 2026-10-28) is installed user-locally at
  `%LOCALAPPDATA%\Programs\nodejs` and on the user PATH; `sync.py`
  falls back to that location when PATH does not resolve node.
- The workspace's physical path lives under
  `E:\Project-Doc-Builder-Backup\`. Absolute paths that appear in tool
  output showing that tree ARE the real project — not a stray copy.
- `sync.py` commands (`status`, `pull`, `backup`, `zip`, `push`, `sync`)
  are documented in its module docstring at the repo root.
