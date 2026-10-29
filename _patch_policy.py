"""One-off migration: insert the SEC-POL-033 policy guidance slide into every
exercise deck persisted in data/decks.json.

The source decks receive the slide from exercises._add_standard_slides(), but
data/decks.json was seeded before that change, so the running app needs it
patched in here too. Idempotent: existing policy slides are refreshed in
place, missing ones are inserted right after Rules of Engagement.

Run:  python _patch_policy.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from exercises import policy_guidance_slide  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(ROOT, "data", "decks.json")
NAME = "Policy Guidance — SEC-POL-033"


def main():
    with open(FILE, encoding="utf-8") as f:
        doc = json.load(f)
    added, refreshed, skipped = 0, 0, 0
    for d in doc.get("decks", []):
        if not str(d.get("name") or "").startswith("Table Top Exercise"):
            skipped += 1
            continue
        slides = d.get("slides") or []
        names = [s.get("name") or "" for s in slides]
        fresh = policy_guidance_slide()
        if NAME in names:
            for i, s in enumerate(slides):
                if (s.get("name") or "") == NAME:
                    if (s.get("body"), s.get("data"), s.get("layout")) != (
                            fresh["body"], fresh["data"], fresh["layout"]):
                        slides[i] = dict(fresh)
                        refreshed += 1
                    break
            continue
        if "Rules of Engagement" in names:
            idx = names.index("Rules of Engagement") + 1
        else:
            idx = 1 if slides and (slides[0].get("name") == "Title") else 0
        slides.insert(idx, dict(fresh))
        d["slides"] = slides
        added += 1
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE)
    print("policy slide -> inserted: %d, refreshed: %d, skipped decks: %d"
          % (added, refreshed, skipped))


if __name__ == "__main__":
    main()
