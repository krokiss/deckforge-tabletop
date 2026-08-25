"""Persistent storage for DeckForge presentations (JSON file, thread-safe).

A deck is {id, name, slides: [{id, name, layout, body, data}], created, updated}.
"""

import json
import os
import threading
import time
import uuid

from samples import SAMPLE_DECKS

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
FILE = os.path.join(DATA_DIR, "decks.json")

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

    # Completed exercises
    def list_completed_exercises(self):
        with _lock:
            return self.doc.get("completed_exercises", [])

    def add_completed_exercise(self, exercise_data):
        with _lock:
            if "completed_exercises" not in self.doc:
                self.doc["completed_exercises"] = []
            exercise_data["completed_at"] = _now()
            exercise_data["id"] = uuid.uuid4().hex[:12]
            self.doc["completed_exercises"].insert(0, exercise_data)  # newest first
            _save(self.doc)
            return exercise_data

    def get_completed_exercise(self, exercise_id):
        with _lock:
            for ex in self.doc.get("completed_exercises", []):
                if ex.get("id") == exercise_id:
                    return dict(ex)
            return None
