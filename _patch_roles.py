"""One-off migration: make every role-like value in data/decks.json come only
from each deck's Roles slide.

For every persisted exercise deck it:
  * combines the paired role entries into one (Care Operations Leads +
    Team Leaders, Customer Care Manager & Director + Client Delivery /
    Account Manager) and keeps an HR and a WFM role in every selection,
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


# Paired roles combined into a single Roles-slide entry. Each list carries
# both the original pair members and any earlier merged name, so decks that
# were already merged in a previous run get renamed too (the first entry
# whose target name is present wins — the others fall through as no-ops).
# Old names keep resolving through _OWNER_ALIASES in scenarios.py.
ROLE_MERGES = [
    (["Care Operations Leads", "Team Leaders"],
     "Care Operations Leads & Team Leaders",
     "Care operations & floor teams",
     "Queue prioritisation, answer times, agent status, escalation "
     "and caller experience (A.5.29, A.5.20)"),
    (["Customer Care Manager & Director", "Client Delivery / Account Manager",
      "Customer Care Manager & Director / Client Delivery / Account Manager"],
     "Customer Care & Client Delivery",
     "Care delivery & client relationship",
     "Continuity decisions, care capacity, staffing, SLA reporting, "
     "notifications and service credits (A.5.29, A.8.6, A.5.20)"),
]

HR_ROW = {"role": "Human Resources", "owner": "HR",
          "concern": "Employee policies & violations (A.6.1, A.6.3)"}
WFM_ROW = {"role": "Workforce Management", "owner": "WFM",
           "concern": "Forecasting, scheduling, attendance (A.8.6, A.6.1)"}


def _merge_roles(roles):
    """Combine paired role entries into one and make sure the selection always
    offers an HR and a WFM role. Returns (roles, changed)."""
    changed = False
    rows = [dict(r) for r in roles if isinstance(r, dict)]
    for members, name, owner, concern in ROLE_MERGES:
        names = {str(r.get("role") or "").strip() for r in rows}
        if name in names:
            continue                                  # already merged
        hits = [i for i, r in enumerate(rows)
                if str(r.get("role") or "").strip() in members]
        if not hits:
            continue
        for i in reversed(hits):
            del rows[i]
        rows.insert(hits[0], {"role": name, "owner": owner,
                              "concern": concern})
        changed = True

    def _has(keys):
        return any(str(r.get("role") or "").strip().lower() in keys
                   for r in rows)

    if not _has({"human resources", "hr"}):
        rows.append(dict(HR_ROW))
        changed = True
    if not _has({"workforce management", "wfm"}):
        at = next((i for i, r in enumerate(rows)
                   if str(r.get("role") or "").strip().lower()
                   == "human resources"), len(rows) - 1)
        rows.insert(at + 1, dict(WFM_ROW))
        changed = True
    return rows, changed


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
        changed = False
        # 1) Combine the paired roles into one entry and keep HR + WFM in the
        #    selection, before anything else derives from the Roles slide.
        for s in slides:
            if (s.get("name") or "") != "Roles":
                continue
            sd0 = s.get("data") or {}
            merged, rc = _merge_roles(sd0.get("roles") or [])
            if rc:
                s["data"] = dict(sd0, roles=merged)
                changed = True
            break
        listed = roles_of(d)
        if not listed:
            new_decks.append(d)
            continue
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
