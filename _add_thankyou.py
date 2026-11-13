"""One-off: insert a Thank You closing slide right after the Post-Exercise
Discussion & Next Steps slide, in the deck generator (exercises.py) and in the
decks the running app has already persisted (data/decks.json). Idempotent."""

import io
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

WRAP_UP = [
    "Every response and decision recorded today is carried into the After-Action "
    "Report and Executive Summary.",
    "Corrective actions are tracked with an owner and a target date until they are closed.",
    "The final report is distributed to participants for review and kept for the audit trail.",
]


def thank_you_slide():
    return {
        "name": "Thank You",
        "layout": "content",
        "body": ("## Thank you for participating\n\n"
                 "This was a facilitated discussion, not a test \u2014 the value is in the "
                 "decisions taken under time pressure and the gaps they exposed.\n\n"
                 "{{#each wrap_up}}\n- {{this}}\n{{/each}}\n\n"
                 "**Exercise closed.** Please raise anything you want captured with the "
                 "facilitator before you leave."),
        "data": {"wrap_up": list(WRAP_UP)},
    }


def patch_exercises():
    path = os.path.join(ROOT, "exercises.py")
    src = io.open(path, encoding="utf-8", newline="").read()
    orig = src

    ref = "# _add_standard_slides() adds all three to every exercise deck (idempotent).  #"
    if ref in src:
        bullet = "#   \u2022 Thank You \u2014 final slide, shown right after the discussion slide."
        bullet = bullet.ljust(len(ref) - 1) + "#"
        src = src.replace(ref, bullet + "\n" + ref.replace("all three", "all four "))

    anchor = ('        "data": {"discussion": list(_POST_EXERCISE_DISCUSSION),\n'
              '                 "next_steps": list(_NEXT_STEPS)},\n'
              '    }\n')
    if "_WRAP_UP = [" not in src:
        add = '''
_WRAP_UP = [
    "Every response and decision recorded today is carried into the After-Action "
    "Report and Executive Summary.",
    "Corrective actions are tracked with an owner and a target date until they are closed.",
    "The final report is distributed to participants for review and kept for the audit trail.",
]


def _thank_you_slide():
    """Final slide: thanks the team and closes the exercise."""
    return {
        "name": "Thank You",
        "layout": "content",
        "body": ("## Thank you for participating\\n\\n"
                 "This was a facilitated discussion, not a test \\u2014 the value is in the "
                 "decisions taken under time pressure and the gaps they exposed.\\n\\n"
                 "{{#each wrap_up}}\\n- {{this}}\\n{{/each}}\\n\\n"
                 "**Exercise closed.** Please raise anything you want captured with the "
                 "facilitator before you leave."),
        "data": {"wrap_up": list(_WRAP_UP)},
    }
'''
        assert src.count(anchor) == 1, "closing slide anchor not unique"
        src = src.replace(anchor, anchor + add)

    old_doc = ('    """Insert the Rules of Engagement slide after the title, the SEC-POL-033\n'
               '    policy guidance slide right after it, and the Post-Exercise Discussion &\n'
               '    Next Steps closing slide just before the After Action Executive Summary\n'
               '    slide. Idempotent; leaves other slides, injects and meta untouched."""')
    new_doc = ('    """Insert the Rules of Engagement slide after the title, the SEC-POL-033\n'
               '    policy guidance slide right after it, the Post-Exercise Discussion &\n'
               '    Next Steps slide just before the After Action Executive Summary slide,\n'
               '    and the Thank You closing slide right after it. Idempotent; leaves\n'
               '    other slides, injects and meta untouched."""')
    if old_doc in src:
        src = src.replace(old_doc, new_doc)

    anchor2 = ('    if "Post-Exercise Discussion & Next Steps" not in names:\n'
               '        pos = next((i for i, s in enumerate(slides)\n'
               '                    if (s.get("name") or "").startswith("After Action Executive")),\n'
               '                   len(slides))\n'
               '        slides.insert(pos, _closing_slide())\n')
    add2 = '''
    names = [s.get("name", "") for s in slides]
    if "Thank You" not in names:
        pos = next((i for i, s in enumerate(slides)
                    if s.get("name") == "Post-Exercise Discussion & Next Steps"), None)
        if pos is not None:
            slides.insert(pos + 1, _thank_you_slide())
'''
    if "_thank_you_slide()" not in src.split("def _add_standard_slides")[1]:
        assert src.count(anchor2) == 1, "discussion insert anchor not unique"
        src = src.replace(anchor2, anchor2 + add2)

    if src != orig:
        io.open(path, "w", encoding="utf-8", newline="").write(src)
    return src != orig


def patch_decks():
    path = os.path.join(ROOT, "data", "decks.json")
    raw = io.open(path, encoding="utf-8", newline="").read()
    crlf = "\r\n" in raw
    doc = json.loads(raw)
    inserted = 0
    for dk in doc.get("decks") or []:
        slides = dk.get("slides") or []
        if any(s.get("name") == "Thank You" for s in slides):
            continue
        pos = next((i for i, s in enumerate(slides)
                    if s.get("name") == "Post-Exercise Discussion & Next Steps"), None)
        if pos is None:
            continue
        slides.insert(pos + 1, thank_you_slide())
        dk["slides"] = slides
        inserted += 1
    if inserted:
        out = json.dumps(doc, ensure_ascii=False, indent=2)
        if crlf:
            out = out.replace("\n", "\r\n")
        io.open(path, "w", encoding="utf-8", newline="").write(out)
    return inserted


if __name__ == "__main__":
    print("exercises.py patched:", patch_exercises())
    print("decks migrated:", patch_decks())
