"""Persistent storage for DeckForge presentations (JSON file, thread-safe).

A deck is {id, name, slides: [{id, name, layout, body, data}], created, updated}.
"""

import json
import os
import re
import threading
import time
import uuid

from samples import SAMPLE_DECKS

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
FILE = os.path.join(DATA_DIR, "decks.json")
HISTORY_DIR = os.path.join(DATA_DIR, "history")

_lock = threading.Lock()


def _load():
    try:
        with open(FILE, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or not isinstance(doc.get("decks"), list):
        return None
    return doc


def _save(doc):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE)


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _slug(text, limit=40):
    """Filename-safe fragment for a completed run (ASCII, dash-separated)."""
    s = re.sub(r"[^A-Za-z0-9]+", "-", text or "").strip("-").lower()
    return s[:limit].strip("-") or "exercise"


def _history_filename(entry):
    date = str(entry.get("completed_date") or entry.get("completed_at") or _now())[:10]
    return "%s_%s_%s.json" % (
        date,
        _slug(entry.get("name") or entry.get("deck_name") or ""),
        entry.get("id") or uuid.uuid4().hex[:12],
    )


def _write_history(entry):
    """Persist one completed run as its own file under data/history/."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = os.path.join(HISTORY_DIR, _history_filename(entry))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)
    return path


def _read_history():
    """Every completed run on disk, newest first (by date, then record time)."""
    entries = []
    try:
        names = os.listdir(HISTORY_DIR)
    except OSError:
        return entries
    for name in names:
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(HISTORY_DIR, name), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and data.get("id"):
            entries.append(data)
    entries.sort(key=lambda e: (str(e.get("completed_date") or ""),
                                str(e.get("completed_at") or ""),
                                str(e.get("id") or "")), reverse=True)
    return entries


class Store:
    def __init__(self):
        doc = _load()
        if doc is None:
            # Back up a corrupt/legacy file before reseeding. The old DocForge
            # used data/templates.json; keep it around as a .bak.
            for legacy in (FILE, os.path.join(DATA_DIR, "templates.json")):
                if os.path.exists(legacy):
                    try:
                        os.replace(legacy, legacy + ".bak")
                    except OSError:
                        pass
            doc = {"decks": []}
            for d in SAMPLE_DECKS:
                doc["decks"].append(self._record(d["name"], d.get("slides")))
            _save(doc)
        self.doc = doc
        self._migrate_legacy_history()

    def _migrate_legacy_history(self):
        """Move history older versions kept inside decks.json into data/history/."""
        legacy = self.doc.get("completed_exercises")
        if not legacy:
            return
        for entry in legacy:
            if not isinstance(entry, dict):
                continue
            entry.setdefault("id", uuid.uuid4().hex[:12])
            entry.setdefault("completed_at", _now())
            _write_history(entry)
        self.doc["completed_exercises"] = []
        _save(self.doc)

    @staticmethod
    def _record(name, slides, injects=None, meta=None):
        return {
            "id": uuid.uuid4().hex[:12],
            "name": name,
            "slides": slides or [],
            "injects": injects or [],
            "meta": meta or {},
            "created": _now(),
            "updated": _now(),
        }

    def list_decks(self):
        with _lock:
            return [{"id": d["id"], "name": d["name"], "updated": d["updated"],
                     "slide_count": len(d["slides"])} for d in self.doc["decks"]]

    def get_deck(self, did):
        with _lock:
            for d in self.doc["decks"]:
                if d["id"] == did:
                    return dict(d)
            return None

    def create_deck(self, name, slides=None, injects=None, meta=None):
        with _lock:
            d = self._record(name, slides, injects, meta)
            self.doc["decks"].append(d)
            _save(self.doc)
            return dict(d)

    def update_deck(self, did, name=None, slides=None, injects=None, meta=None):
        with _lock:
            for d in self.doc["decks"]:
                if d["id"] == did:
                    if name is not None:
                        d["name"] = name
                    if slides is not None:
                        d["slides"] = slides
                    if injects is not None:
                        d["injects"] = injects
                    if meta is not None:
                        d["meta"] = meta
                    d["updated"] = _now()
                    _save(self.doc)
                    return dict(d)
            return None

    def delete_deck(self, did):
        with _lock:
            before = len(self.doc["decks"])
            self.doc["decks"] = [d for d in self.doc["decks"] if d["id"] != did]
            if len(self.doc["decks"]) != before:
                _save(self.doc)
                return True
            return False

    # Completed exercises -- one JSON file per run in data/history/ (never in
    # decks.json, so history does not bloat the deck file or its deploys).
    def list_completed_exercises(self):
        with _lock:
            return _read_history()

    def add_completed_exercise(self, exercise_data):
        with _lock:
            entry = dict(exercise_data)
            entry["completed_at"] = _now()
            entry["id"] = uuid.uuid4().hex[:12]
            _write_history(entry)
            return entry

    def get_completed_exercise(self, exercise_id):
        with _lock:
            for ex in _read_history():
                if ex.get("id") == exercise_id:
                    return dict(ex)
            return None
