# Publishing DeckForge

DeckForge is a Python-stdlib-only web app: one server, no dependencies, no
build step. It runs anywhere Python 3.8+ exists. Choose the path that fits:

| Where | Audience | URL | Effort |
|---|---|---|---|
| **Replit** | anyone with the link | `https://replit.com/@you/deckforge` | ~5 min |
| **Koyeb (free)** | anyone with the link | `https://<name>.koyeb.app` | ~10 min (needs GitHub) |
| **Render (free)** | anyone with the link | `https://<name>.onrender.com` | ~10 min (needs GitHub) |
| **GitHub Pages** | anyone with the link | `https://<you>.github.io/<repo>/` | ~5 min |
| **Portable zip** | colleagues who run it locally | no URL | ~1 min |
| **Export .html** | one-off distribution | any static host / email | ~1 min |

The server already honors the `PORT` / `HOST` environment variables, so no
code changes are needed for any cloud host.

---

## Option A — Replit (fastest public URL)

The app originally lived on Replit, and that is still the quickest way to get
a public URL.

1. Go to <https://replit.com> → **Create Repl** → choose **Python**.
2. Upload `DeckForge-publish.zip` into the repl (drag it onto the Files
   panel, or use the upload icon) and unzip it there — or copy the files
   into the workspace so `server.py` sits at the repl root.
3. The included `.replit` file already sets the run command
   (`python server.py --host 0.0.0.0`). If it doesn't take effect, click the
   **Run** button once — Replit will offer the command.
4. Press **Run**. The webview opens the app; the URL under the run button
   (e.g. `https://deckforge.yourname.repl.co`) is shareable.

Notes:
- Decks persist in `data/decks.json` inside the repl — they survive as long
  as the repl exists.
- Free Replit repls sleep after a while; waking them just means clicking
  Run again (or opening the URL).

## Option B — Render (persistent free URL)

Render's free tier gives a public URL that stays up (it spins down after
~15 min idle and wakes on the first visit).

1. Push this folder (with the `Dockerfile`) to a GitHub repo.
2. On <https://render.com> → **New → Web Service** → connect the repo.
3. Render auto-detects the Dockerfile. No build command, no start command.
4. Deploy. Your URL is `https://<name>.onrender.com`.
   (Render injects `PORT`; the server picks it up automatically.)

Railway, Fly.io, and any other container host work the same way — the
`Dockerfile` is all they need. (Note: Fly.io's free tier ended in 2025 and
Railway is trial-credit based, so for a genuinely free always-on URL prefer
Koyeb or Render.)

## Option B2 — Koyeb (free, longest sleep window)

Koyeb's free tier is the best free option in 2026: one web service (512 MB
RAM, 0.1 vCPU, 2 GB SSD), usually **no credit card** required, and it only
scales to zero after **1 hour** of no traffic (Render sleeps after 15 min).

1. Push this folder (with the `Dockerfile`) to a GitHub repo.
2. On <https://koyeb.com> → **Create App** → connect the GitHub repo.
3. Koyeb auto-detects the Dockerfile. Deploy; your URL is
   `https://<name>.koyeb.app`.

## Option E — GitHub Pages (free forever, static)

GitHub Pages is free, permanent, never sleeps, and needs no card — but it
can only host **static files**, not a Python server. Two ways to use it:

1. **Exported presentations**: every deck exports a self-contained `.html`
   (Export ▸ Presentation) that runs the full exercise with no server. Push
   those files to a repo → Settings ▸ Pages ▸ deploy from branch → each deck
   is a permanent link.
2. **The app itself**: not possible on Pages — the editor/dashboard needs
   the API. Use Koyeb/Replit for that.

## Important: data persistence on free hosts

Free-tier instances (Koyeb, Render, Replit free) have **ephemeral storage**
— edits made on the hosted copy (slide fill-ins, team responses, role picks)
are kept while the instance is up, but are **reset to the shipped snapshot**
when the instance sleeps and wakes (Koyeb: after 1 h idle) or redeploys.

- Keep the local copy as the **source of truth**; treat the hosted instance
  as a live demo/session host.
- For durable hosted data you'd need a paid instance with a persistent
  volume, or export each session's After-Action report (.doc) before the
  instance sleeps.
- Exported `.html` presentations keep their state in the browser for the
  session — fine for running a live exercise.

## Option C — Portable zip (no internet, for facilitators)

1. Unzip `DeckForge-publish.zip` on any Windows PC with Python 3.8+.
2. Double-click `start.bat` (starts the server and opens the browser), or run
   `python server.py` and open http://127.0.0.1:8420.
3. Share the folder with colleagues; each person runs their own local copy
   (each keeps its own exercise data).

## Option D — Exported presentations (static files)

Every deck exports a **self-contained `.html`** (Export ▸ Presentation) that
runs the full interactive slideshow — injects, role picker, team responses —
with **no server at all**. Host those files on any static host (GitHub
Pages, Netlify, SharePoint, email attachment) for one-off distribution.

---

## What's inside the publish zip

```
server.py         HTTP server + API (stdlib only)
renderer.py       template engine + markdown
store.py          JSON persistence
samples.py        seed decks
exercises.py      BPO cyber exercises (ISO 27001/27002)
scenarios.py      INJECT scenario catalog + deck generator
static/           frontend (index.html, style.css, app.js)
data/decks.json   the live exercise decks (seeded on first run if absent)
start.bat         Windows launcher
README.md         full documentation
.replit, Dockerfile   deploy configs
```

**Note on data:** the zip ships with the current `data/decks.json` — all the
customized exercise decks. If you'd rather publish a clean slate, delete
`data/decks.json` from the zip; the app re-seeds the default decks on first
run.
