"""Seed presentations shown the first time DeckForge runs.

Each deck is {name, slides: [{name, layout, body, data}]}.
Layouts: title | content | section | blank.
"""

from exercises import EXERCISE_DECKS

ROADMAP_SLIDES = [
    {
        "name": "Title",
        "layout": "title",
        "body": "# {{company}}\n\n## {{quarter}} Product Roadmap",
        "data": {"company": "Acme Studio", "quarter": "Q3 2026"},
    },
    {
        "name": "Vision",
        "layout": "section",
        "body": "# Build software people love",
        "data": {},
    },
    {
        "name": "Goals",
        "layout": "content",
        "body": "## Goals\n\n{{#each goals}}\n- {{this}}\n{{/each}}",
        "data": {
            "goals": [
                "Ship mobile app v2.1",
                "Reach 10k monthly active users",
                "Launch the partner API",
            ],
        },
    },
    {
        "name": "Timeline",
        "layout": "content",
        "body": "## Timeline\n\n| Phase | When | Owner |\n|-------|------|-------|\n{{#each timeline}}\n| {{phase}} | {{when}} | {{owner}} |\n{{/each}}",
        "data": {
            "timeline": [
                {"phase": "Discovery", "when": "Weeks 1–2", "owner": "Maya"},
                {"phase": "Build", "when": "Weeks 3–6", "owner": "Diego"},
                {"phase": "Launch", "when": "Week 8", "owner": "Priya"},
            ],
        },
    },
    {
        "name": "Risks",
        "layout": "content",
        "body": "## Risks\n\n{{#each risks}}\n- **{{name}}** — {{mitigation}}\n{{/each}}",
        "data": {
            "risks": [
                {"name": "Content delays", "mitigation": "Weekly checkpoints with the team"},
                {"name": "Third-party API changes", "mitigation": "Contractual freeze window"},
            ],
        },
    },
    {
        "name": "Next steps",
        "layout": "content",
        "body": "## Next steps\n\n1. {{step_1}}\n2. {{step_2}}\n3. {{step_3}}",
        "data": {
            "step_1": "Approve scope by Friday",
            "step_2": "Kickoff call on Monday",
            "step_3": "Freeze scope by September 1",
        },
    },
]

PITCH_SLIDES = [
    {
        "name": "Title",
        "layout": "title",
        "body": "# {{product}}\n\n{{tagline}}",
        "data": {"product": "Acme Cloud", "tagline": "Infrastructure that scales with you"},
    },
    {
        "name": "The problem",
        "layout": "content",
        "body": "## The problem\n\n{{problem}}\n\n{{#if pain_points}}\n{{#each pain_points}}\n- {{this}}\n{{/each}}\n{{/if}}",
        "data": {
            "problem": "Teams waste weeks managing infrastructure instead of shipping product.",
            "pain_points": [
                "Long deployment cycles",
                "Unexpected cloud bills",
                "Fragile on-call rotations",
            ],
        },
    },
    {
        "name": "The solution",
        "layout": "content",
        "body": "## The solution\n\n{{solution | default:\"Describe how the product fixes the problem.\"}}\n\n{{#each features}}\n- **{{name}}** — {{detail}}\n{{/each}}",
        "data": {
            "solution": "Acme Cloud automates the boring parts of infrastructure.",
            "features": [
                {"name": "One-click deploys", "detail": "Ship in minutes, not days"},
                {"name": "Cost guardrails", "detail": "Set budgets, get alerts"},
                {"name": "Managed backups", "detail": "Restore in seconds"},
            ],
        },
    },
    {
        "name": "Pricing",
        "layout": "content",
        "body": "## Pricing\n\n| Plan | Price | Best for |\n|------|-------|----------|\n{{#each plans}}\n| {{name}} | {{price}} | {{audience}} |\n{{/each}}",
        "data": {
            "plans": [
                {"name": "Starter", "price": "$49/mo", "audience": "Side projects"},
                {"name": "Growth", "price": "$199/mo", "audience": "Growing teams"},
                {"name": "Enterprise", "price": "Custom", "audience": "Large orgs"},
            ],
        },
    },
    {
        "name": "Thank you",
        "layout": "section",
        "body": "# Thank you\n\n{{contact | default:\"Contact us for a demo\"}}",
        "data": {"contact": ""},
    },
]

LESSON_SLIDES = [
    {
        "name": "Title",
        "layout": "title",
        "body": "# {{lesson.title}}\n\n{{lesson.subtitle}}",
        "data": {"lesson": {"title": "The Solar System", "subtitle": "Science · Grade 5"}},
    },
    {
        "name": "Quick facts",
        "layout": "content",
        "body": "## Quick facts\n\nThe {{planet}} is the {{ordinal}} planet from the Sun.\n\nIt takes about {{year_length}} days to orbit the Sun, and it has {{moon_count}} moon(s).",
        "data": {"planet": "Earth", "ordinal": "third", "year_length": 365, "moon_count": 1},
    },
    {
        "name": "Exercise",
        "layout": "content",
        "body": "## {{heading}}\n\n{{prompt}}\n\n1. {{answer_1}}\n2. {{answer_2}}",
        "data": {
            "heading": "Pop quiz",
            "prompt": "Fill in the blanks below — toggle “Fill in” on the Preview tab to type straight into the slide.",
            "answer_1": "The closest planet to the Sun is ______",
            "answer_2": "The largest planet in the Solar System is ______",
        },
    },
    {
        "name": "Discussion",
        "layout": "section",
        "body": "# Discussion\n\nWhat would happen if Earth lost its Moon?",
        "data": {},
    },
]

SAMPLE_DECKS = [
    {"name": "Q3 Product Roadmap", "slides": ROADMAP_SLIDES},
    {"name": "Acme Sales Pitch", "slides": PITCH_SLIDES},
    {"name": "Lesson: The Solar System", "slides": LESSON_SLIDES},
] + EXERCISE_DECKS
