"""One-off migration: make every role-like value in data/decks.json come only
from each deck's Roles slide.

For every persisted exercise deck it:
  * rewrites the AAR slide's Participants line from the Roles slide,
  * maps every after-action/CAPA action owner to a listed role (map_owner),
  * regenerates the AAR recommendations and CAPA register from the sanitized
    actions (so the embedded "owner: X" text matches too),
  * fixes the one decision question that named an unlisted role
    ("HR and legal" -> "Human Resources and Compliance").

Idempotent. Writes LF line endings to keep the byte-level backup mirror in sync.

Run:  python _patch_roles.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scenarios import (capa_rows, map_owner, normalize_question_callouts,  # noqa: E402
                       recommendations_from_actions, roles_of, sanitize_actions)

ROOT = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(ROOT, "data", "decks.json")

TEXT_FIXES = [
    ("How do you preserve evidence for HR and legal? (A.5.28, A.8.15)",
     "How do you preserve evidence for Human Resources and Compliance? (A.5.28, A.8.15)"),
    # Policy-guidance slide: drop role names that are not on any Roles slide
    ("Executive Leadership reporting within 24 hours",
     "Executive governance reporting within 24 hours"),
    ("formal Information Security leadership review within 24 hours",
     "formal security-governance review within 24 hours"),
    ("to the CIO and the S.A.F.E. Audit & Risk Committee",
     "to executive governance and the S.A.F.E. Audit & Risk Committee"),
]


def _fix_text(obj):
    """Recursively apply TEXT_FIXES to every string in obj."""
    if isinstance(obj, str):
        for old, new in TEXT_FIXES:
            obj = obj.replace(old, new)
        return obj
    if isinstance(obj, list):
        return [_fix_text(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _fix_text(v) for k, v in obj.items()}
    return obj


def main():
    with open(FILE, encoding="utf-8") as f:
        doc = json.load(f)
    patched = 0
    new_decks = []
    for d in doc.get("decks", []):
        if not str(d.get("name") or "").startswith("Table Top Exercise"):
            new_decks.append(d)
            continue
        d = _fix_text(d)  # rebuilds nested containers, so fixes land in this copy
        slides = d.get("slides") or []
        listed = roles_of(d)
        if not listed:
            new_decks.append(d)
            continue
        changed = False
        # Decision-question role callouts ("WFM —", "Care Operations Lead —")
        # must match the Roles slide name exactly.
        for s in slides:
            if not str(s.get("name") or "").startswith("Decision"):
                continue
            sd = s.get("data") or {}
            touched = False
            if isinstance(sd.get("questions"), list):
                nq = normalize_question_callouts(sd["questions"], listed)
                if nq != sd["questions"]:
                    sd = dict(sd, questions=nq)
                    touched = True
            if isinstance(sd.get("pairs"), list):
                pairs = []
                for p in sd["pairs"]:
                    if isinstance(p, dict):
                        n = normalize_question_callouts([p.get("question") or ""], listed)[0]
                        if n != p.get("question"):
                            p = dict(p, question=n)
                            touched = True
                    pairs.append(p)
                if touched:
                    sd = dict(sd, pairs=pairs)
            if touched:
                s["data"] = sd
                changed = True
        aar = next((s for s in slides
                    if str(s.get("name") or "").startswith("After Action Executive")), None)
        review = next((s for s in slides
                       if str(s.get("name") or "") == "After-action review"), None)
        if review is None or aar is None:
            new_decks.append(d)
            continue
        rd = dict(review.get("data") or {})
        acts = sanitize_actions(rd.get("actions") or [], listed)
        if acts != (rd.get("actions") or []):
            rd["actions"] = acts
            review["data"] = rd
            changed = True
        ad = dict(aar.get("data") or {})
        want_p = ", ".join(listed)
        if ad.get("participants") != want_p:
            ad["participants"] = want_p
            changed = True
        if isinstance(ad.get("meta"), dict):
            if ad["meta"].get("prepared_for") != want_p:
                ad["meta"] = dict(ad["meta"], prepared_for=want_p)
                changed = True
        recs = recommendations_from_actions(acts)
        capa = capa_rows(acts)
        if ad.get("recommendations") != recs:
            ad["recommendations"] = recs
            changed = True
        if ad.get("capa") != capa:
            ad["capa"] = capa
            changed = True
        if changed:
            aar["data"] = ad
            patched += 1
        new_decks.append(d)
    doc["decks"] = new_decks
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FILE)
    print("roles constrained to the Roles slide in %d deck(s)" % patched)


if __name__ == "__main__":
    main()
