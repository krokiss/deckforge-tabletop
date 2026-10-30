"""Scenario catalog matching the INJECT Simulation Deck, and a generator that
builds each scenario into a full Table Top Exercise deck (ISO/IEC 27001:2022
Annex A controls + ISO/IEC 27002:2022 guidance).

Each scenario is a dict; the generator expands it into the standard 11-slide
exercise arc shared by the hand-written decks in exercises.py.
"""

import re

IT = "INFORMATION TECHNOLOGY"
BO = "BUSINESS OPERATIONS"

# --------------------------------------------------------------------------- #
# After Action Executive Summary template data (audit-readiness layer).       #
# These follow the standard executive-summary template: framework alignment,  #
# KPIs, evidence pack, roadmap and executive decisions are the same across   #
# exercises; score, capability and assessment are exercise-specific.          #
# --------------------------------------------------------------------------- #
AAR_FRAMEWORK_ALIGNMENT = [
    {"theme": "Governance, roles, escalation, secure communications",
     "soc2": "CC1, CC2, CC5, CC7",
     "tisax": "ISMS governance, incident management, AL3 interview/evidence readiness",
     "iso": "Clauses 5, 6, 7, 8; 5.2, 5.24, 5.25, 5.26, 5.27, 5.37"},
    {"theme": "Identity, privileged access, rogue account disablement, remote access",
     "soc2": "CC6.1\u2013CC6.8, CC7.2\u2013CC7.4",
     "tisax": "Identity and access management, privileged access, remote access control",
     "iso": "5.15, 5.16, 5.17, 5.18, 8.2, 8.3, 8.5"},
    {"theme": "Monitoring, logging, detection, threat hunting, C2 blocking",
     "soc2": "CC3, CC4, CC6, CC7",
     "tisax": "IT operations and network security; monitoring and event handling",
     "iso": "5.7, 8.15, 8.16, 8.20, 8.21, 8.22"},
    {"theme": "Malware, persistence, unusual services, vulnerability analysis",
     "soc2": "CC7.2, CC7.3, CC7.4, CC8",
     "tisax": "Secure operations, endpoint protection, vulnerability management",
     "iso": "8.7, 8.8, 8.9, 8.19, 8.32"},
    {"theme": "Data exfiltration, staging files, provider engagement, legal review",
     "soc2": "C1, P criteria if personal data in scope; CC7",
     "tisax": "Information classification, protection of confidential information, incident handling",
     "iso": "5.12, 5.13, 5.14, 5.31, 5.33, 5.34"},
    {"theme": "Forensic snapshots, evidence preservation, insider investigation",
     "soc2": "CC7.4, CC7.5, CC9",
     "tisax": "Incident evidence and AL3 verification artifacts",
     "iso": "5.24, 5.26, 5.28, 5.30"},
    {"theme": "Recovery validation, lessons learned, CAPA tracking, future tabletop testing",
     "soc2": "CC4, CC7.5, A1.2/A1.3",
     "tisax": "Business continuity and continual improvement",
     "iso": "5.27, 5.29, 5.30, 8.13, Clause 9, Clause 10"},
]

AAR_KPIS = [
    {"kpi": "Mean time to triage high-severity identity incident", "target": "< 15 minutes"},
    {"kpi": "Time to revoke all active remote sessions for compromised scope", "target": "< 15 minutes after declaration"},
    {"kpi": "Time to disable confirmed rogue or suspicious privileged accounts", "target": "< 30 minutes"},
    {"kpi": "Time to complete privileged credential rotation plan", "target": "< 24 hours for highest-risk credentials"},
    {"kpi": "Coverage of critical AD/VPN logs into SIEM", "target": "\u2265 95% of in-scope assets"},
    {"kpi": "Percentage of privileged accounts under MFA/PAM/JIT control", "target": "\u2265 98%"},
    {"kpi": "Time to complete initial data-exfiltration impact assessment", "target": "< 24 hours"},
    {"kpi": "CAPA closure by committed date", "target": "\u2265 90% on time"},
    {"kpi": "Follow-up tabletop exercise score", "target": "\u2265 22/25"},
]

AAR_DECISIONS_REQUESTED = [
    "Approve a funded remediation program for identity containment, privileged access hardening, exfiltration monitoring, and forensic readiness.",
    "Designate a single executive owner for CAPA governance and monthly reporting until all high-priority items are closed and validated.",
    "Direct Corporate Security, Legal, HR, Compliance, and IT to finalize breach-notification and insider-threat decision matrices within 30 days.",
    "Require a follow-up tabletop exercise within 180 days using the same scoring model and evidence pack requirements.",
]

AAR_EVIDENCE_PACK = [
    "Incident declaration, severity classification, commander assignment, scribe notes, and time-stamped decision log.",
    "Isolation, session revocation, account disablement, privileged access review, and credential rotation evidence.",
    "SIEM/EDR queries, IOC lists, block rules, firewall approvals, threat-hunting notes, malware analysis, and eradication evidence.",
    "Impact assessment, data classification, DLP/CASB alerts, provider notes, legal/privacy decision logs, and notification determinations.",
    "Forensic and insider evidence: device recall, images, storage snapshots, chain of custody, HR/legal coordination, and closure rationale.",
    "Recovery and improvement evidence: clean-reconnect approvals, backup/restore validation, persistence re-scan, RCA, CAPA closure, and management review.",
]

AAR_ROADMAP = [
    {"period": "0\u201330 days",
     "milestones": "Assign owners; publish war-room RACI; approve containment thresholds; update legal/privacy notification matrix; complete privileged-account inventory; implement priority SIEM alerts."},
    {"period": "30\u201390 days",
     "milestones": "Deploy or tune PAM/JIT controls; complete detection engineering; exercise exfiltration response; execute forensic evidence tabletop."},
    {"period": "90\u2013180 days",
     "milestones": "Validate recovery gates and restore drills; run follow-up tabletop; close CAPA evidence; update control narratives and evidence repository."},
]

AAR_CAPABILITY_DEFAULT = [
    {"domain": "Detection and Triage", "score": "To be scored",
     "assessment": "Record initial recognition, severity classification, incident commander, scribe and time-stamped decision log from the exercise transcript."},
    {"domain": "Containment and Eradication", "score": "To be scored",
     "assessment": "Assess isolation, session revocation, account disablement, blocking and persistence removal from the exercise transcript."},
    {"domain": "Investigation and Forensics", "score": "To be scored",
     "assessment": "Assess threat hunting, evidence preservation and chain of custody from the exercise transcript."},
    {"domain": "Communication and Coordination", "score": "To be scored",
     "assessment": "Assess stakeholder cadence, legal notification thresholds and service-desk scripts from the exercise transcript."},
    {"domain": "Recovery and Lessons Learned", "score": "To be scored",
     "assessment": "Assess recovery validation, credential rotation completion and lessons-learned closure from the exercise transcript."},
]

AAR_SCORE_DEFAULT = {"score": "To be scored", "rating": "To be rated",
                     "risk": "High until CAPA closure", "priority": "To be confirmed after scoring"}

AAR_ASSESSMENT_DEFAULT = (
    "The team should complete scoring from the exercise transcript. Expected strengths to verify: "
    "containment, escalation, evidence preservation and coordination. Expected gaps to verify: "
    "credential-rotation decisiveness, formal evidence handling, notification criteria, "
    "recovery validation and audit-ready documentation."
)

AAR_META_DEFAULT = {
    "prepared_for": "Executive Leadership, Corporate Security, IT Operations, Compliance",
    "prepared_date": "2026-08-17",
    "source_document": "",
    "status": "Executive summary and audit-readiness control alignment; not a certification opinion",
    "framework": "SOC 2 Trust Services Criteria | TISAX AL3 / VDA ISA | ISO/IEC 27001:2022 and ISO/IEC 27002:2022",
    "reference": "AICPA 2017 Trust Services Criteria with revised points of focus (2022); ENX/VDA TISAX "
                 "Participant Handbook v2.8 and ISA 6.0.3; ISO/IEC 27001:2022; ISO/IEC 27002:2022.",
}

# --------------------------------------------------------------------------- #
# BPO / Business Operations variants of the executive-summary layer.          #
# Same template shape as the AAR_* constants above, but framed for            #
# customer care operations: care continuity, care capacity, the workforce     #
# answering customers and client SLAs rather than cyber/technology controls.  #
# Used by _build_deck() for BO-category decks.                                #
# --------------------------------------------------------------------------- #
BPO_FRAMEWORK_ALIGNMENT = [
    {"theme": "Care continuity governance, roles, escalation, customer communication",
     "soc2": "CC1, CC2, CC5, A1.1\u2013A1.3",
     "tisax": "Business continuity management, operational responsibility",
     "iso": "Clauses 5, 6, 7; 5.24, 5.29, 5.30, 5.20"},
    {"theme": "Care workforce availability, scheduling, attendance and wellbeing",
     "soc2": "CC1, A1.2",
     "tisax": "Personnel security and operational availability",
     "iso": "6.1, 6.2, 6.3, 6.7"},
    {"theme": "Care capacity: inbound answer times, queue prioritisation, unanswered-call backlog recovery",
     "soc2": "A1.2, A1.3, CC7",
     "tisax": "Operational capacity and service continuity",
     "iso": "8.6, 8.14, 5.29"},
    {"theme": "Customer SLAs, notifications, service credits and reporting",
     "soc2": "CC9, CC2",
     "tisax": "Customer requirements and communication",
     "iso": "5.20, 5.21, 5.31"},
    {"theme": "Alternate care arrangements, remote work and queue redistribution",
     "soc2": "A1.1, A1.2",
     "tisax": "Continuity arrangements for critical operations",
     "iso": "5.29, 5.30, 6.7"},
    {"theme": "Decision logging, customer-impact evidence, exercise records",
     "soc2": "CC7, CC4",
     "tisax": "Operational incident evidence and readiness",
     "iso": "5.24, 5.26, 5.28"},
    {"theme": "Lessons learned, CAPA closure, follow-up exercising",
     "soc2": "CC4, A1.3",
     "tisax": "Business continuity and continual improvement",
     "iso": "5.27, 5.29, Clause 9, Clause 10"},
]

BPO_KPIS = [
    {"kpi": "Time to activate the continuity plan after a care-service disruption", "target": "< 15 minutes"},
    {"kpi": "Priority care queues kept live (emergency and complaint lines)", "target": "\u2265 90% of priority queues"},
    {"kpi": "Calls answered within the agreed service level during the disruption", "target": "\u2265 90% of contracted target"},
    {"kpi": "Unanswered inbound calls cleared from the disruption backlog", "target": "within 48 hours of recovery"},
    {"kpi": "Customer notifications issued within the agreed window", "target": "100% of triggered cases"},
    {"kpi": "Staffing coverage against minimum viable care staffing", "target": "\u2265 95% of plan"},
    {"kpi": "Customer SLA adherence during and after the disruption", "target": "\u2265 95% of contracted targets"},
    {"kpi": "Service credits paid vs SLA exposure", "target": "\u2264 agreed tolerance"},
    {"kpi": "CAPA closure by committed date", "target": "\u2265 90% on time"},
    {"kpi": "Follow-up customer-care continuity exercise score", "target": "\u2265 22/25"},
]

BPO_DECISIONS_REQUESTED = [
    "Approve a funded continuity programme covering alternate care-delivery arrangements, staffing capacity and remote-work readiness for the customer care operation.",
    "Designate a single executive owner for customer-care continuity CAPA governance and monthly reporting until all high-priority items are closed and validated.",
    "Direct Care Operations, Workforce Management, HR and Client Delivery to finalise minimum-viable-staffing and customer-notification matrices within 30 days.",
    "Require a follow-up customer-care continuity tabletop within 180 days using the same scoring model and evidence-pack requirements.",
]

BPO_EVIDENCE_PACK = [
    "Care continuity plan versions, trigger records and the time-stamped decision log.",
    "Customer notification log: who was told, when, by whom and against which SLA clause.",
    "Care workforce evidence: attendance records, rosters, redeployment decisions and shift changes.",
    "Care capacity evidence: inbound call and chat volumes, answer times, abandonment and unanswered-call backlog tracking.",
    "Continuity-drill records: alternate care arrangements, remote work, results and gaps.",
    "Recovery and improvement evidence: SLA reconciliation, customer reporting, RCA, CAPA closure and management review.",
]

BPO_ROADMAP = [
    {"period": "0\u201330 days",
     "milestones": "Assign care continuity owners; publish the customer-notification matrix; define minimum viable staffing per care queue; confirm alternate care arrangements and remote capacity."},
    {"period": "30\u201390 days",
     "milestones": "Run care continuity and remote-work drills; test inbound backlog-recovery playbooks; cross-train teams on priority inbound queues; agree SLA relief protocols with key clients."},
    {"period": "90\u2013180 days",
     "milestones": "Run the follow-up customer-care continuity tabletop; close CAPA evidence; embed continuity tests in the operating rhythm; update control narratives and evidence repository."},
]

BPO_CAPABILITY_DEFAULT = [
    {"domain": "Care Continuity Activation & Triage", "score": "To be scored",
     "assessment": "Record who declared the continuity event, how priority care queues were chosen, and the decision log from the exercise transcript."},
    {"domain": "Customer Communication & SLA Management", "score": "To be scored",
     "assessment": "Assess customer notification timing, ownership and SLA/credit handling from the exercise transcript."},
    {"domain": "Care Workforce & Capacity Management", "score": "To be scored",
     "assessment": "Assess staffing decisions, redeployment, shift changes and care-queue prioritisation from the exercise transcript."},
    {"domain": "Service Recovery & Resumption", "score": "To be scored",
     "assessment": "Assess queue resumption order, unanswered-call backlog clearance and verification before returning to normal service from the exercise transcript."},
    {"domain": "Governance, Lessons Learned & CAPA", "score": "To be scored",
     "assessment": "Assess follow-up ownership, evidence capture and CAPA closure discipline from the exercise transcript."},
]

BPO_ASSESSMENT_DEFAULT = (
    "The team should complete scoring from the exercise transcript. Expected strengths to verify: "
    "customer communication, care-queue prioritisation and team coordination. Expected gaps to verify: "
    "minimum-viable-staffing decisions, unanswered-call and backlog recovery speed, alternate care arrangements, "
    "SLA/credit handling and audit-ready continuity documentation."
)

BPO_META_DEFAULT = {
    "prepared_for": "Operations Director, Customer Care Managers, Team Leaders, Client Delivery, Workforce Management",
    "prepared_date": "2026-08-17",
    "source_document": "",
    "status": "Executive summary and customer-care continuity-readiness control alignment; not a certification opinion",
    "framework": "SOC 2 (Availability criteria) | ISO 22301-aligned continuity practices | ISO/IEC 27001:2022 and ISO/IEC 27002:2022",
    "reference": "AICPA 2017 Trust Services Criteria; ISO 22301 business continuity guidance; ISO/IEC 27001:2022 "
                 "and ISO/IEC 27002:2022 continuity and operational controls (A.5.24, A.5.29, A.5.30, A.8.6).",
}

_BPO_AAR = {
    # "participants" is derived per deck from its Roles slide in _build_deck.
    "meta": BPO_META_DEFAULT,
    "assessment": BPO_ASSESSMENT_DEFAULT,
    "score": AAR_SCORE_DEFAULT,
    "capability": BPO_CAPABILITY_DEFAULT,
    "framework": BPO_FRAMEWORK_ALIGNMENT,
    "kpis": BPO_KPIS,
    "decisions": BPO_DECISIONS_REQUESTED,
    "evidence": BPO_EVIDENCE_PACK,
    "roadmap": BPO_ROADMAP,
}

_IT_AAR = {
    # "participants" is derived per deck from its Roles slide in _build_deck.
    "meta": AAR_META_DEFAULT,
    "assessment": AAR_ASSESSMENT_DEFAULT,
    "score": AAR_SCORE_DEFAULT,
    "capability": AAR_CAPABILITY_DEFAULT,
    "framework": AAR_FRAMEWORK_ALIGNMENT,
    "kpis": AAR_KPIS,
    "decisions": AAR_DECISIONS_REQUESTED,
    "evidence": AAR_EVIDENCE_PACK,
    "roadmap": AAR_ROADMAP,
}


def _aar(cat):
    return _BPO_AAR if cat == BO else _IT_AAR


_GROUND_RULES = ("Stay in role. No wrong answers — this is a discussion, not a test. "
                 "Call out what you don't know. Every decision gets an Annex A control.")

_DEFAULT_OBJECTIVES = {
    IT: [
        "Test detection and response when client data is at stake",
        "Map every decision to an ISO/IEC 27001:2022 Annex A control",
        "Expose gaps in monitoring, access and segmentation",
        "Leave with an after-action list with owners and dates",
    ],
    BO: [
        "Test decision-making when customer care continuity is at stake",
        "Map every decision to ISO/IEC 27001:2022 continuity and operational controls",
        "Expose gaps in care capacity, customer communication and recovery",
        "Leave with an after-action list with owners and dates",
    ],
}

_DEFAULT_ROLES = {
    IT: [
        {"role": "Corporate Security", "owner": "Security", "concern": "Information & privacy security (A.5.x, A.8.2)"},
        {"role": "IT Server & System Team", "owner": "Infrastructure", "concern": "Servers, systems, recovery (A.8.13)"},
        {"role": "IT Desktop Team", "owner": "End-user computing", "concern": "Endpoints, patching, user access (A.8.7, A.8.8)"},
        {"role": "IT Network Team", "owner": "Networking", "concern": "Connectivity, segmentation, VPN (A.8.20, A.8.31)"},
        {"role": "Compliance", "owner": "Legal & Compliance", "concern": "Legal & compliance concerns (A.5.20, A.5.34)"},
        {"role": "Human Resources", "owner": "HR", "concern": "Employee policies & violations (A.6.1, A.6.3)"},
        {"role": "Workforce Management", "owner": "WFM", "concern": "Forecasting, scheduling, attendance (A.8.6, A.6.1)"},
        {"role": "Marketing", "owner": "Corporate communications", "concern": "Official corporate press statements (A.5.20)"},
        {"role": "Executive Leadership", "owner": "C-suite", "concern": "Executive decision-making (A.5.24)"},
    ],
    BO: [
        {"role": "Customer Care & Client Delivery", "owner": "Care delivery & client relationship", "concern": "Continuity decisions, care capacity, staffing, SLA reporting, notifications and service credits (A.5.29, A.8.6, A.5.20)"},
        {"role": "Care Operations Leads & Team Leaders", "owner": "Care operations & floor teams", "concern": "Queue prioritisation, answer times, agent status, escalation and caller experience (A.5.29, A.5.20)"},
        {"role": "Workforce Management", "owner": "WFM", "concern": "Forecasting, scheduling, attendance (A.8.6, A.6.1)"},
        {"role": "Quality & Training", "owner": "QA", "concern": "Call quality, script adherence, retraining (A.6.3, A.8.16)"},
        {"role": "Human Resources", "owner": "HR", "concern": "Absence, wellbeing, redeployment (A.6.1, A.6.7)"},
        {"role": "Executive Sponsor", "owner": "C-suite", "concern": "Continuity funding & governance (A.5.24)"},
    ],
}

_CLAUSE_NOTE = ("ISO/IEC 27002:2022 is the code of practice that guides implementation "
                "of the Annex A controls referenced above.")

# After Action Executive Summary slide template — carries the narrative
# recap, highlights, lessons learned, recommendations and CAPA register.
AAR_BODY = (
    "## After Action Executive Summary\n\n"
    "**Exercise:** {{exercise.name}}\n"
    "**Date:** {{exercise.date | default:\"—\"}}\n"
    "**Participants:** {{participants | default:\"—\"}}\n\n"
    "### Summary\n{{story}}\n\n"
    "### Exercise highlights\n{{#each highlights}}\n- {{this}}\n{{/each}}\n\n"
    "### Discussion Summary\n{{#each discussion.injects}}\n**{{inject}}** ({{time}})\n> {{detail}}\n\n{{/each}}\n{{#each discussion.decisions}}\n**{{decision}}**\n{{#each responses}}\n- {{this}}\n{{/each}}\n\n{{/each}}\n\n"
    "### Lessons learned\n{{#each lessons}}\n- {{this}}\n{{/each}}\n\n"
    "### Recommendations\n{{#each recommendations}}\n- {{this}}\n{{/each}}\n\n"
    "### Corrective & Preventive Actions (CAPA)\n"
    "| Action | Type | Owner | Due |\n|---|---|---|---|\n"
    "{{#each capa}}\n| {{item}} | {{type}} | {{owner}} | {{due}} |\n{{/each}}"
)

_PREVENTIVE_WORDS = ("alert", "monitor", "review", "validate", "plan", "test", "schedule",
                     "audit", "training", "awareness", "prevent", "detect", "document",
                     "tune", "segment", "separate", "re-test", "retest", "assessment")


# --------------------------------------------------------------------------- #
# Role mapping: every role-like value (CAPA / after-action owners, action      #
# owners, participant strings) must resolve to a role listed on the deck's     #
# Roles slide. Aliases are the shorthand forms used in older decks; the        #
# fallback list covers aliases whose natural target is not listed on a deck    #
# (e.g. "Client delivery" on an IT deck).                                      #
# --------------------------------------------------------------------------- #
_OWNER_ALIASES = {
    "ciso": "Corporate Security",
    "infosec": "Corporate Security",
    "security operations": "Corporate Security",
    "security ops": "Corporate Security",
    "security": "Corporate Security",
    "iam": "Corporate Security",
    "it": "IT Server & System Team",
    "infra": "IT Server & System Team",
    "infrastructure": "IT Server & System Team",
    "cloud operations": "IT Server & System Team",
    "service desk": "IT Desktop Team",
    "communications": "Marketing",
    "marketing": "Marketing",
    "hr": "Human Resources",
    "human resources": "Human Resources",
    "procurement": "Compliance",
    "dpo": "Compliance",
    "legal": "Compliance",
    "compliance": "Compliance",
    "client delivery": "Customer Care & Client Delivery",
    "client delivery / account manager": "Customer Care & Client Delivery",
    "client delivery manager": "Customer Care & Client Delivery",
    "account manager": "Customer Care & Client Delivery",
    "customer care manager & director / client delivery / account manager": "Customer Care & Client Delivery",
    "operations": "Care Operations Leads & Team Leaders",
    "care operations lead": "Care Operations Leads & Team Leaders",
    "care operations leads": "Care Operations Leads & Team Leaders",
    "care operations": "Care Operations Leads & Team Leaders",
    "customer care manager": "Customer Care & Client Delivery",
    "customer care managers": "Customer Care & Client Delivery",
    "customer care manager & director": "Customer Care & Client Delivery",
    "operations director": "Customer Care & Client Delivery",
    "wfm": "Workforce Management",
    "workforce management": "Workforce Management",
    "team leader": "Care Operations Leads & Team Leaders",
    "team leaders": "Care Operations Leads & Team Leaders",
    "qa": "Quality & Training",
    "quality & training": "Quality & Training",
    "executive sponsor": "Executive Sponsor",
    "executive leadership": "Executive Leadership",
}

_OWNER_FALLBACK = {
    "client delivery": ["Compliance", "Marketing"],
    "operations": ["Customer Care & Client Delivery"],
    "it": ["Executive Sponsor", "Executive Leadership"],
}


def map_owner(owner, listed):
    """Resolve *owner* to a role that appears in *listed* (the deck's Roles
    slide). Returns the matched listed role verbatim, or the original value
    when nothing matches (so information is never silently dropped)."""
    o = str(owner or "").strip()
    listed = [str(l).strip() for l in (listed or []) if str(l).strip()]
    if not o or not listed:
        return o
    low = {l.lower(): l for l in listed}
    if o.lower() in low:
        return low[o.lower()]
    for l in listed:                       # substring match either way
        if l.lower() in o.lower() or o.lower() in l.lower():
            return l
    canon = _OWNER_ALIASES.get(o.lower())
    if canon:
        if canon.lower() in low:
            return low[canon.lower()]
        for alt in _OWNER_FALLBACK.get(o.lower(), []):
            if alt.lower() in low:
                return low[alt.lower()]
        kw = canon.split()[0].lower()      # first word of the canonical name
        for l in listed:
            if kw in l.lower():
                return l
    for word in re.split(r"\W+", o.lower()):   # last resort: keyword from owner
        if len(word) > 3:
            for l in listed:
                if word in l.lower():
                    return l
    return o


def normalize_question_callouts(questions, listed):
    """Decision questions often open with a short role callout
    ("WFM — …", "Care Operations Lead — …"). Rewrite any callout that
    resolves to a listed role so it matches the Roles slide name exactly.
    Non-role prefixes (ordinary question text) are left untouched."""
    out = []
    for q in questions or []:
        q = str(q)
        m = re.match(r"^([A-Za-z][A-Za-z &/]{0,80}?)\s+[\u2014\u2013-]\s+", q)
        if m:
            prefix = m.group(1).strip()
            resolved = map_owner(prefix, listed)
            if resolved and resolved != prefix and resolved in [str(l) for l in listed]:
                q = resolved + q[m.end(1):]
        out.append(q)
    return out


def sanitize_actions(actions, listed):
    """Return actions with every owner mapped to a listed role."""
    return [dict(a, owner=map_owner(a.get("owner"), listed))
            if isinstance(a, dict) else a
            for a in (actions or [])]


def roles_of(deck):
    """The deck's listed roles, read from its Roles slide."""
    for sl in deck.get("slides") or []:
        if (sl.get("name") or "") == "Roles":
            return [str((r or {}).get("role") or "").strip()
                    for r in ((sl.get("data") or {}).get("roles") or [])
                    if isinstance(r, dict) and str((r or {}).get("role") or "").strip()]
    return []


def capa_rows(actions):
    """Build a CAPA register from the deck's follow-up actions. Each row carries
    the slide-facing fields (item/type/owner/due) plus the report-facing fields
    (target/framework_focus/evidence) used by the executive-summary template."""
    rows = []
    for a in actions or []:
        item = str(a.get("item") or "").strip()
        low = item.lower()
        typ = "Preventive" if any(w in low for w in _PREVENTIVE_WORDS) else "Corrective"
        if "quarterly" in low:
            due, target = "Quarterly", "Quarterly / recurring"
        elif "working days" in low:
            due, target = "5 working days", "Immediate: 0\u201330 days"
        elif "days" in low:
            due, target = "30 days", "0\u201330 days"
        else:
            due, target = "30 days", "0\u201330 days"
        m = re.search(r"\(([A-Za-z0-9.\s,/\u2013\-]+)\)", item)
        focus = ("ISO/IEC 27001:2022 " + m.group(1).strip()
                 if m else "ISO/IEC 27001:2022; SOC 2 / TISAX AL3 alignment")
        evidence = ("Approved procedure, test evidence and review log; closure reviewed at management review."
                    if typ == "Preventive" else
                    "Implementation evidence, validation test result and owner sign-off.")
        rows.append({"item": item, "type": typ,
                     "owner": str(a.get("owner") or "—").strip(), "due": due,
                     "target": target, "framework_focus": focus, "evidence": evidence})
    return rows


def recommendations_from_actions(actions):
    """Turn the follow-up actions into forward-looking recommendations."""
    out = []
    for a in actions or []:
        item = str(a.get("item") or "").strip()
        owner = str(a.get("owner") or "—").strip()
        if item:
            out.append("Prioritise: %s — owner: %s." % (item, owner))
    return out or ["Carry every action item from the after-action review into the ISMS improvement plan."]


def story_summary(s):
    """Narrative recap of an exercise, synthesised from its spec."""
    bits = []
    setting = str(s.get("setting") or "").strip()
    if setting:
        bits.append(setting.rstrip(".") + ".")
    beats = []
    for inj in s.get("injects") or []:
        t = str(inj.get("time") or "").strip()
        title = str(inj.get("title") or "").strip()
        detail = str(inj.get("detail") or "").strip()
        if t and title:
            beats.append("At %s, %s — %s" % (t, title, detail))
    if beats:
        bits.append("The exercise unfolded through the following injects: " + " ".join(beats))
    hw = str(s.get("hotwash") or "").strip()
    if hw:
        bits.append("The hotwash closed on a single question: %s" % hw)
    bits.append("Every decision was mapped to an ISO/IEC 27001:2022 Annex A control, "
                "and the exercise ended with a set of owned follow-up actions.")
    return " ".join(bits)


def deck_story(deck):
    """Narrative recap synthesised from a built deck's own slides."""
    slides = deck.get("slides") or []

    def find(pred):
        return next((s for s in slides if pred(s.get("name", ""))), None)

    setting = ""
    bg = find(lambda n: n == "Scenario background")
    if bg:
        setting = str((bg.get("data") or {}).get("setting") or "").strip()
    injs = [s for s in slides if s.get("name", "").startswith("Inject #")]
    hw = ""
    hot = find(lambda n: n == "Hotwash")
    if hot:
        hw = str((hot.get("data") or {}).get("text") or "").strip()
    bits = []
    if setting:
        bits.append(setting.rstrip(".") + ".")
    beats = []
    for inj in injs:
        d = inj.get("data") or {}
        t, title, detail = d.get("time", ""), d.get("title", ""), d.get("detail", "")
        if t and title:
            beats.append("At %s, %s — %s" % (t, title, detail))
    if beats:
        bits.append("The exercise unfolded through the following injects: " + " ".join(beats))
    if hw:
        bits.append("The hotwash closed on a single question: %s" % hw)
    bits.append("Every decision was mapped to an ISO/IEC 27001:2022 Annex A control, "
                "and the exercise ended with a set of owned follow-up actions.")
    return " ".join(bits)


def _kicker(s):
    kind = ("Business Continuity Tabletop" if s["category"] == BO
            else "Cyber Incident Tabletop")
    return ("%s · ISO/IEC 27001:2022 & ISO/IEC 27002:2022 · %s · %s · "
            "90 minutes · Facilitated discussion"
            % (kind, s["category"].title(), s["difficulty"].title()))


def inject_slides(injs):
    """Build the SECTION slides for a deck's inject timeline.

    Each inject is {time, title, detail, prompt}; the deck carries the same
    list under its "injects" key so the interactive runner can replay them.
    Inject slides now include an observation field for participants to capture
    their initial reactions and observations.
    """
    out = []
    for i, inj in enumerate(injs or []):
        n = i + 1
        out.append({
            "name": "Inject #%d — %s" % (n, inj.get("title") or "Inject %d" % n),
            "layout": "section",
            "body": "# Inject #%d — {{title}}\n\n**{{time}}** — {{detail}}\n\n> {{prompt}}\n\n### Initial Observations\n{{observation}}" % n,
            "data": {
                "number": n,
                "time": inj.get("time", ""),
                "title": inj.get("title", "Inject %d" % n),
                "detail": inj.get("detail", ""),
                "prompt": inj.get("prompt", "Team Response — Critical decision point"),
                "observation": "",
            },
        })
    return out


def _build_deck(s):
    cat = s["category"]
    aar = _aar(cat)
    # Roles listed on this deck's Roles slide — the single source of truth for
    # participant names and action/CAPA owners in the AAR and executive report.
    listed = [str(r.get("role") or "").strip()
              for r in (s.get("roles") or _DEFAULT_ROLES[cat]) if isinstance(r, dict)]
    listed = [x for x in listed if x]
    actions = sanitize_actions(s.get("actions") or [], listed)
    da = s.get("decision_a_name", "Initial response")
    db = s.get("decision_b_name", "Impact")
    injs = inject_slides(s.get("injects"))
    if not injs:  # legacy specs without an injects list
        injs = [
            {"name": "Inject #1 — " + s.get("inject1_name", "Detection"), "layout": "section",
             "body": "# Inject #1 — %s\n\n{{text}}" % s.get("inject1_name", "Detection"),
             "data": {"text": s.get("inject1", "")}},
            {"name": "Inject #2 — " + s.get("inject2_name", "Escalation"), "layout": "section",
             "body": "# Inject #2 — %s\n\n{{text}}" % s.get("inject2_name", "Escalation"),
             "data": {"text": s.get("inject2", "")}},
        ]
    slides = [
        {
            "name": "Title", "layout": "title",
            "body": "# Table Top Exercise\n\n## {{scenario.title}}\n\n{{scenario.kicker}}",
            "data": {"scenario": {"title": s["title"], "kicker": _kicker(s)}},
        },
        {
            "name": "Objectives & ground rules", "layout": "content",
            "body": "## {{objectives.title}}\n\n{{#each objectives.items}}\n- {{this}}\n{{/each}}\n\n**Ground rules:** {{ground_rules}}",
            "data": {"objectives": {"title": "Objectives & ground rules",
                                    "items": s.get("objectives") or _DEFAULT_OBJECTIVES[cat]},
                     "ground_rules": _GROUND_RULES},
        },
        {
            "name": "Scenario background", "layout": "content",
            "body": "## Scenario background\n\n**Organisation:** {{company.profile}}\n\n**ISO/IEC 27001 scope:** {{iso_scope}}\n\n**Key systems:**\n{{#each systems}}\n- {{this}}\n{{/each}}\n\n**Setting:** {{setting}}",
            "data": {"company": {"profile": s["profile"]},
                     "iso_scope": s["iso_scope"], "systems": s["systems"], "setting": s["setting"]},
        },
        {
            "name": "Roles", "layout": "content",
            "body": "## Roles & responsibilities\n\n| Role | Owner | Key concerns |\n|------|-------|--------------|\n{{#each roles}}\n| {{role}} | {{owner}} | {{concern}} |\n{{/each}}",
            "data": {"roles": s.get("roles") or _DEFAULT_ROLES[cat]},
        },
    ]
    # Inject timeline: Inject #1 -> Decision A -> Inject #2 -> Inject #3 -> Decision B
    if injs:
        slides.append(injs[0])
    # Decision A with response fields (paired questions+responses)
    q1_pairs = [{"question": q, "response": ""}
                for q in normalize_question_callouts(s["q1"], listed)]
    slides.append({
        "name": "Decision A — " + da, "layout": "content",
        "body": "## Decision A — %s\n\n{{#each pairs}}\n### Q{{@number}}. {{question | raw}}\n\n> **Team Response:** {{response}}\n\n{{/each}}\n\n**Timebox:** {{timebox}}" % da,
        "data": {"pairs": q1_pairs, "timebox": "15 minutes"},
    })
    if len(injs) > 1:
        slides.append(injs[1])
    if len(injs) > 2:
        slides.append(injs[2])
    # Decision B with response fields (paired questions+responses)
    q2_pairs = [{"question": q, "response": ""}
                for q in normalize_question_callouts(s["q2"], listed)]
    slides.append({
        "name": "Decision B — " + db, "layout": "content",
        "body": "## Decision B — %s\n\n{{#each pairs}}\n### Q{{@number}}. {{question | raw}}\n\n> **Team Response:** {{response}}\n\n{{/each}}\n\n**Timebox:** {{timebox}}" % db,
        "data": {"pairs": q2_pairs, "timebox": "20 minutes"},
    })
    # Discussion Summary slide — aggregates all injects and decisions
    inject_summary = []
    for i, inj in enumerate(s.get("injects") or []):
        inject_summary.append({
            "inject": "Inject #%d — %s" % (i + 1, inj.get("title", "")),
            "time": inj.get("time", ""),
            "detail": inj.get("detail", ""),
        })
    # Extract responses from paired format
    decision_summary = [
        {"decision": "Decision A — " + da, "responses": [p.get("response", "") for p in q1_pairs]},
        {"decision": "Decision B — " + db, "responses": [p.get("response", "") for p in q2_pairs]},
    ]
    slides.append({
        "name": "Discussion Summary", "layout": "content",
        "body": "## Discussion Summary\n\n### Injects\n{{#each injects}}\n**{{inject}}** ({{time}})\n> {{detail}}\n\n{{/each}}\n\n### Decision Points\n{{#each decisions}}\n**{{decision}}**\n{{#each responses}}\n- {{this}}\n{{/each}}\n\n{{/each}}",
        "data": {"injects": inject_summary, "decisions": decision_summary},
    })
    slides += [
        {
            "name": "ISO/IEC 27001 clause map", "layout": "content",
            "body": "## Aligning decisions to ISO/IEC 27001\n\n| Decision | ISO/IEC 27001:2022 control | ISO/IEC 27002:2022 guidance |\n|----------|----------------------------|-----------------------------|\n{{#each clause_map}}\n| {{decision}} | {{control}} | {{guidance}} |\n{{/each}}\n\n*%s*" % _CLAUSE_NOTE,
            "data": {"clause_map": s["clause_map"]},
        },
        {
            "name": "Hotwash", "layout": "section",
            "body": "# Hotwash\n\n{{text}}",
            "data": {"text": s["hotwash"]},
        },
        {
            "name": "After Action Executive Summary", "layout": "content",
            "body": AAR_BODY,
            "data": {"exercise": {"name": s["title"], "date": ""},
                     "participants": ", ".join(listed),
                     "highlights": s["highlights"], "lessons": s["lessons"],
                     "story": story_summary(s),
                     "discussion": {"injects": [{"inject": "Inject #%d — %s" % (i+1, inj.get("title","")), "time": inj.get("time",""), "detail": inj.get("detail","")} for i, inj in enumerate(s.get("injects") or [])],
                                     "decisions": [{"decision": "Decision A — " + da, "responses": ["" for _ in s["q1"]]}, {"decision": "Decision B — " + db, "responses": ["" for _ in s["q2"]]}]},
                     "recommendations": recommendations_from_actions(actions),
                     "capa": capa_rows(actions),
                     "meta": dict(aar["meta"], prepared_for=", ".join(listed)),
                     "executive_assessment": aar["assessment"],
                     "score": dict(aar["score"]),
                     "capability": [dict(r) for r in aar["capability"]],
                     "framework_alignment": [dict(r) for r in aar["framework"]],
                     "kpis": [dict(r) for r in aar["kpis"]],
                     "decisions": list(aar["decisions"]),
                     "evidence": list(aar["evidence"]),
                     "roadmap": [dict(r) for r in aar["roadmap"]]},
        },
        {
            "name": "After-action review", "layout": "content",
            "body": "## After-action review\n\n{{#each actions}}\n- **{{item}}** — owner: {{owner}}\n{{/each}}\n\n**Next step:** {{next_step}}",
            "data": {"actions": actions, "next_step": s["next_step"]},
        },
    ]
    return {
        "name": "Table Top Exercise · " + s["title"],
        "slides": slides,
        "injects": s.get("injects") or [],
        "meta": {"title": s["title"], "desc": s["description"],
                 "cat": s["category"], "diff": s["difficulty"]},
    }


SCENARIOS = [
    # ------------------------- INFORMATION TECHNOLOGY ------------------------- #
    {
        "title": "Cyber-Intrusion", "category": IT, "difficulty": "INTERMEDIATE",
        "description": "Active Directory compromise via VPN with shadow admin accounts and disabled logging.",

        "profile": "ISO/IEC 27001-certified BPO providing finance & accounting services to 8 clients",
        "iso_scope": "Finance & accounting services delivered over client portals and a corporate VPN",
        "systems": ["VPN gateway", "Active Directory domain", "Client finance portals", "SIEM & PAM", "Email"],
        "setting": "Tuesday 08:30, with the quarterly finance close underway for two clients.",
        "injects": [
            {"time": "08:15", "title": "VPN anomaly detected", "detail": "VPN login anomaly detected from unusual IP address outside business hours."},
            {"time": "08:30", "title": "New admin accounts created", "detail": "New admin accounts created on domain controllers by unauthorized user."},
            {"time": "08:45", "title": "Logs disabled on DC", "detail": "Logs disabled on domain controller, forensic evidence at risk."},
        ],
        "inject1": "03:10 — the VPN gateway logs a login using a dormant service account. By 03:30 a shadow admin account was created in Active Directory, and logging was disabled on the domain controllers 20 minutes later.",
        "q1": [
            "Who leads the response, and what is the escalation trigger? (A.5.24)",
            "Do you isolate the VPN and revoke the shadow account now — what breaks? (A.8.2, A.8.3)",
            "How do you preserve evidence when logging was disabled? (A.8.15, A.5.28)",
            "Which clients are told today, and what does the contract require? (A.5.20)",
        ],
        "inject2": "09:15 — Forensics confirm lateral movement from the domain into two client finance portals. Two shadow accounts are live, and an attacker-held session is active during the finance close.",
        "q2": [
            "How do you isolate the client environments from each other? (A.8.31)",
            "Do you force password resets and terminate sessions across the fleet? (A.8.3, A.8.5)",
            "How do you restore logging and prove the timeline is trustworthy? (A.8.15, A.8.16)",
            "What breach-notification duties apply to the finance data? (A.5.24, compliance)",
        ],
        "clause_map": [
            {"decision": "Isolate VPN & domain", "control": "A.8.2 · Privileged access rights", "guidance": "Restrict and review admin access (27002 §8.2)"},
            {"decision": "Revoke shadow accounts", "control": "A.8.3 · Access restriction", "guidance": "Remove unauthorised access (27002 §8.3)"},
            {"decision": "Preserve evidence", "control": "A.5.28 · Evidence collection", "guidance": "Chain of custody despite disabled logs (27002 §5.28)"},
            {"decision": "Client notification", "control": "A.5.20 · Supplier agreements", "guidance": "Contractual notification terms (27002 §5.20)"},
            {"decision": "Restore logging & monitoring", "control": "A.8.15 / A.8.16 · Logging & monitoring", "guidance": "Rebuild a trustworthy audit trail (27002 §8.15–8.16)"},
            {"decision": "Lessons learned", "control": "A.5.27 / A.5.28 · Learning & evidence", "guidance": "Improve controls from the incident (27002 §5.27–5.28)"},
        ],
        "hotwash": "How fast could we detect a shadow admin? What would a clean AD baseline look like tomorrow?",
        "highlights": [
            "Shadow admin accounts were identified and revoked within the first hour",
            "Logging-disabled events were traced through vendor and domain logs",
            "Client finance portals were isolated from the domain before the close window",
        ],
        "lessons": [
            "Disabled-logging events need a dedicated alert, not a post-mortem finding",
            "Privileged access review should cover service accounts, not just people",
            "The finance-close window needs a pre-agreed isolation plan",
        ],
        "actions": [
            {"item": "Roll out PAM for all admin access (A.8.2)", "owner": "CISO"},
            {"item": "Alert on logging-disabled events (A.8.15)", "owner": "Security operations"},
            {"item": "Enforce MFA on the VPN (A.8.5)", "owner": "IT"},
            {"item": "Rebaseline AD accounts and configuration (A.8.9)", "owner": "IT"},
        ],
        "next_step": "Incident review within 5 working days; AD controls into the internal audit programme.",
    },
    {
        "title": "Data Loss", "category": IT, "difficulty": "INTERMEDIATE",
        "description": "Sensitive customer data exposed via misconfigured cloud storage permissions.",

        "profile": "ISO/IEC 27001-certified BPO providing payroll and HR administration to 12 clients",
        "iso_scope": "Payroll and HR administration services on behalf of client organisations",
        "systems": ["Cloud object storage (client PII)", "Client portals", "DLP tools", "SIEM", "Configuration management"],
        "setting": "A certification surveillance audit is scheduled for next week.",
        "injects": [
            {"time": "07:50", "title": "Public bucket link discovered", "detail": "A client reports finding a public link to payroll files — a cloud storage bucket appears to be world-readable."},
            {"time": "08:20", "title": "Exposure scope confirmed", "detail": "PII for two clients' employees has been exposed for six weeks; access logs show downloads from unknown IPs."},
            {"time": "09:10", "title": "Indexed by external scanner", "detail": "An external scan service has indexed the exposed data and download logs show repeated access over the window."},
        ],
        "inject1": "A client reports finding a public link to payroll files. A cloud storage bucket was world-readable; PII for two clients' employees has been exposed for six weeks.",
        "q1": [
            "Do you take the bucket offline and revoke the link immediately? (A.8.3, A.8.12)",
            "How do you determine what was actually exposed? (A.5.25)",
            "What evidence do you preserve before changing permissions? (A.8.15)",
            "Which clients are told, and what does the contract require? (A.5.20)",
        ],
        "inject2": "An external scan service has indexed the data; download logs show accesses from unknown IPs over the six-week window.",
        "q2": [
            "What are the notification duties — clients, regulators? (A.5.20, compliance)",
            "How do you restore a secure configuration baseline? (A.8.9, A.8.3)",
            "How do you prevent recurrence — DLP, monitoring? (A.8.12, A.8.16)",
            "What other storage and link configurations need review? (A.8.9)",
        ],
        "clause_map": [
            {"decision": "Take the bucket offline", "control": "A.8.3 · Access restriction", "guidance": "Restrict access to authorised users (27002 §8.3)"},
            {"decision": "Preserve evidence", "control": "A.8.15 · Logging", "guidance": "Capture access logs before changes (27002 §8.15)"},
            {"decision": "Fix configuration", "control": "A.8.9 · Configuration management", "guidance": "Secure baseline for storage (27002 §8.9)"},
            {"decision": "Client notification", "control": "A.5.20 · Supplier agreements", "guidance": "Contractual reporting duties (27002 §5.20)"},
            {"decision": "DLP & monitoring", "control": "A.8.12 / A.8.16 · Data leakage prevention & monitoring", "guidance": "Detect future exposure (27002 §8.12, §8.16)"},
            {"decision": "Lessons learned", "control": "A.5.27 · Learning from incidents", "guidance": "Feed findings into the ISMS (27002 §5.27)"},
        ],
        "hotwash": "How would we know a bucket was world-readable tomorrow? Who owns the cloud configuration baseline?",
        "highlights": [
            "The misconfigured bucket was identified and taken offline the same day",
            "Access logs were preserved before permissions were changed",
            "All clients with data in the bucket were notified with a scope statement",
        ],
        "lessons": [
            "Public-link and permission changes need automated alerting",
            "Storage configurations need a central baseline and clear ownership",
            "Notification templates must be ready before an exposure, not after",
        ],
        "actions": [
            {"item": "Add automated checks for public storage permissions (A.8.9)", "owner": "IT"},
            {"item": "Review and revoke external links quarterly (A.8.3)", "owner": "InfoSec"},
            {"item": "Enable DLP on storage and portals (A.8.12)", "owner": "Security operations"},
            {"item": "Alert on new public links and permission changes (A.8.16)", "owner": "Security operations"},
        ],
        "next_step": "Cloud security review within 10 working days; storage config checks into ISMS audits.",
    },
    {
        "title": "Ransomware", "category": IT, "difficulty": "ADVANCED",
        "description": "Mass encryption attack with backup integrity concerns and ransom demand.",

        "profile": "ISO/IEC 27001-certified BPO providing back-office and document processing for 7 clients",
        "iso_scope": "Back-office and document-processing services, including month-end invoicing",
        "systems": ["Document-processing environment", "File shares", "Email & Active Directory", "Backup platform (nightly, restore-tested quarterly)", "DLP"],
        "setting": "Wednesday 08:00, with month-end invoicing for two clients in progress.",
        "injects": [
            {"time": "08:10", "title": "Mass encryption detected", "detail": "Encryption detected across the document-processing environment and file shares. A ransom note demands $600,000."},
            {"time": "08:40", "title": "Backup integrity in doubt", "detail": "Early checks suggest the backup repository may also have been compromised during the attack."},
            {"time": "10:00", "title": "Last good backup is 14 days old", "detail": "Forensics confirm the attacker held admin access to the backup platform for nine days. The last known-good restore is 14 days old."},
        ],
        "inject1": "08:10 — mass encryption is detected across the document-processing environment and file shares. A ransom note demands $600,000. Early checks suggest the backup repository may also have been compromised during the attack.",
        "q1": [
            "Do you disconnect systems from the network now? (A.8.31)",
            "How do you verify backup integrity before trusting any restore? (A.8.13)",
            "Who decides about the ransom demand? (A.5.25)",
            "Which clients are affected, and what is the notification trigger? (A.5.20)",
        ],
        "inject2": "10:00 — forensics confirm the attackers held admin access to the backup platform for nine days before encryption. The last known-good backup is 14 days old. Two clients' month-end data is at risk.",
        "q2": [
            "Do you restore 14-day-old data and replay changes, or pay? What is the trade-off? (A.8.13, A.5.25)",
            "How do you rebuild the environment without reintroducing the attacker? (A.8.9, A.8.31)",
            "What do you tell clients about data-loss windows and SLA impact? (A.5.20)",
            "What regulatory duties apply to the encrypted client data? (A.5.24, compliance)",
        ],
        "clause_map": [
            {"decision": "Isolate & contain", "control": "A.8.31 · Separation of environments", "guidance": "Cut off the spread (27002 §8.31)"},
            {"decision": "Verify backups", "control": "A.8.13 · Information backup", "guidance": "Test and validate restore points (27002 §8.13)"},
            {"decision": "Ransom decision", "control": "A.5.25 · Incident assessment", "guidance": "Leadership decision and authority (27002 §5.25)"},
            {"decision": "Rebuild cleanly", "control": "A.8.9 / A.8.31 · Configuration & separation", "guidance": "Recovery without reintroducing the attacker (27002 §8.9, §8.31)"},
            {"decision": "Client communication", "control": "A.5.20 · Supplier agreements", "guidance": "Data-loss and SLA terms (27002 §5.20)"},
            {"decision": "Lessons learned", "control": "A.5.27 / A.5.28 · Learning & evidence", "guidance": "Evidence and improvement (27002 §5.27–5.28)"},
        ],
        "hotwash": "How protected is our backup platform from a compromised admin? Could we restore in a day?",
        "highlights": [
            "Systems were disconnected from the network before encryption could spread further",
            "Backup integrity was proven before any restore decision was made",
            "Leadership made an explicit no-pay decision with documented rationale",
        ],
        "lessons": [
            "The backup platform needs separate admin roles — a single admin is a single point of failure",
            "Restore-and-replay procedures should be tested with real month-end data",
            "Client data-loss windows should be agreed contractually, not discovered during a crisis",
        ],
        "actions": [
            {"item": "Harden the backup platform with separate admin roles (A.8.2)", "owner": "InfoSec"},
            {"item": "Move to immutable or offline backups (A.8.13)", "owner": "IT"},
            {"item": "Document and test a replay-and-restore procedure (A.8.13)", "owner": "IT"},
            {"item": "Segment file shares per client (A.8.31)", "owner": "InfoSec"},
        ],
        "next_step": "Backup-resilience review within 10 working days; full restore test this quarter.",
    },
    {
        "title": "Denial of Service", "category": IT, "difficulty": "INTERMEDIATE",
        "description": "DDoS attack targeting public-facing infrastructure causing service degradation.",

        "profile": "ISO/IEC 27001-certified BPO running public-facing client portals and a customer self-service platform",
        "iso_scope": "Customer self-service and client portal hosting",
        "systems": ["Public web portals", "Load balancers & CDN", "Internet edge (firewall, IPS)", "Client APIs", "DDoS mitigation service"],
        "setting": "Black Friday week — portal traffic is running at three times normal.",
        "injects": [
            {"time": "09:30", "title": "Traffic spikes 50x", "detail": "Portal traffic spikes 50x; load balancers saturate, the CDN is bypassed and portals begin timing out."},
            {"time": "10:05", "title": "Second wave hits APIs", "detail": "A second wave targets client APIs and the voice channel; mitigation reports a 40,000-device botnet."},
            {"time": "10:45", "title": "Two client portals down", "detail": "Two clients' portals are fully down. Priority decisions are needed on which services stay up."},
        ],
        "inject1": "09:30 — traffic to the client portals spikes 50x. The load balancers saturate, the CDN is bypassed, and portals begin timing out. It is a DDoS attack.",
        "q1": [
            "Do you engage the DDoS mitigation provider now — who decides? (A.5.24)",
            "What traffic threshold triggers blackholing? (A.8.6)",
            "How do you keep clients informed while portals degrade? (A.5.20)",
            "What evidence do you preserve for attribution? (A.8.15, A.5.28)",
        ],
        "inject2": "10:45 — a second wave targets client APIs and the voice channel. The mitigation provider reports a 40,000-device botnet. Two clients' portals are fully down.",
        "q2": [
            "How do you prioritise which portals and APIs stay up? (A.5.29)",
            "What capacity can the mitigation service absorb? (A.8.6)",
            "How do you communicate outage status and ETA? (A.5.20)",
            "When and how do you restore full service without re-exposing? (A.8.9)",
        ],
        "clause_map": [
            {"decision": "Engage mitigation", "control": "A.5.24 · Incident management planning", "guidance": "Pre-agreed response (27002 §5.24)"},
            {"decision": "Capacity & thresholds", "control": "A.8.6 · Capacity management", "guidance": "Sizing and limits (27002 §8.6)"},
            {"decision": "Preserve evidence", "control": "A.5.28 / A.8.15 · Evidence & logging", "guidance": "Logs for attribution (27002 §5.28, §8.15)"},
            {"decision": "Client communication", "control": "A.5.20 · Supplier agreements", "guidance": "Outage and SLA terms (27002 §5.20)"},
            {"decision": "Continuity of service", "control": "A.5.29 · Continuity planning", "guidance": "Keep priority services up (27002 §5.29)"},
            {"decision": "Lessons learned", "control": "A.5.27 · Learning from incidents", "guidance": "Harden the edge (27002 §5.27)"},
        ],
        "hotwash": "Could we absorb a 50x spike? What is our blackhole threshold — and who owns it?",
        "highlights": [
            "The DDoS mitigation provider was engaged within the first hour",
            "Priority portals and APIs were kept online through both waves",
            "Clients received a single status page instead of ad-hoc updates",
        ],
        "lessons": [
            "Blackhole thresholds and decision authority need to be pre-agreed",
            "The CDN-bypass scenario should be load-tested before peak season",
            "A 50x spike is survivable only with tested capacity and rate limits",
        ],
        "actions": [
            {"item": "Pre-arrange a DDoS mitigation retainer (A.5.24)", "owner": "InfoSec"},
            {"item": "Add rate-limiting and WAF rules for portals (A.8.9)", "owner": "IT"},
            {"item": "Load-test portals to 3x peak (A.8.6)", "owner": "IT"},
            {"item": "Stand up a client status page for incidents (A.5.20)", "owner": "Communications"},
        ],
        "next_step": "Edge-capacity review within 10 working days; DDoS tabletop next quarter.",
    },
    {
        "title": "Insider Threat", "category": IT, "difficulty": "ADVANCED",
        "description": "Disgruntled employee attempts to exfiltrate proprietary data and disrupt operations.",

        "profile": "ISO/IEC 27001-certified BPO providing contact-center and back-office services",
        "iso_scope": "Contact-center and back-office services with access to client databases",
        "systems": ["Contact-center platform", "Client databases", "File shares", "DLP tools", "SIEM", "HR systems"],
        "setting": "A senior agent is on a performance-improvement plan and faces termination on Friday.",
        "injects": [
            {"time": "20:30", "title": "Bulk download flagged", "detail": "SIEM flags a large client-database download to a USB drive and proprietary scripts emailed to a personal account."},
            {"time": "21:10", "title": "Exfiltration confirmed", "detail": "The agent's personal cloud account is found to contain client PII going back three months."},
            {"time": "08:00", "title": "Accomplice identified", "detail": "Monitoring identifies an accomplice on the same shift; the termination decision is now urgent."},
        ],
        "inject1": "20:30 Wednesday — the agent downloads a large client database to a USB drive and emails proprietary scripts to a personal account. SIEM flags both actions.",
        "q1": [
            "Do you confront the employee now, or continue monitoring? Who decides? (A.5.25, A.6.5)",
            "What do you disable — access, badge, sessions? (A.8.3)",
            "How do you preserve evidence for Human Resources and Compliance? (A.5.28, A.8.15)",
            "Which clients are affected, and what is the notification trigger? (A.5.20)",
        ],
        "inject2": "Thursday — the agent's personal cloud account is found to contain client PII going back three months, and an accomplice on the same shift is identified.",
        "q2": [
            "How wide is the investigation — the shift, the team, all clients? (A.5.25)",
            "How do you verify client data was not modified or sold? (A.8.15, A.8.16)",
            "What does this reveal about DLP coverage? (A.8.12)",
            "What people controls failed — screening, awareness, exit? (A.6.1, A.6.3, A.6.5)",
        ],
        "clause_map": [
            {"decision": "Disable access", "control": "A.8.3 / A.6.5 · Access restriction & termination", "guidance": "Cut access decisively (27002 §8.3, §6.5)"},
            {"decision": "Preserve evidence", "control": "A.5.28 · Evidence collection", "guidance": "HR & legal chain of custody (27002 §5.28)"},
            {"decision": "DLP coverage", "control": "A.8.12 · Data leakage prevention", "guidance": "Detect USB and web egress (27002 §8.12)"},
            {"decision": "Monitor activity", "control": "A.8.16 · Monitoring activities", "guidance": "Watch for accomplices (27002 §8.16)"},
            {"decision": "Client notification", "control": "A.5.20 · Supplier agreements", "guidance": "Contractual reporting (27002 §5.20)"},
            {"decision": "Screening & awareness", "control": "A.6.1 / A.6.3 · People controls", "guidance": "Screen and train the workforce (27002 §6.1, §6.3)"},
        ],
        "hotwash": "Would DLP catch a USB copy tomorrow? How do we spot a disgruntled insider earlier?",
        "highlights": [
            "The insider's access was disabled within the hour, before the shift ended",
            "Evidence was preserved with HR and legal chain of custody",
            "The accomplice was identified through monitoring, not luck",
        ],
        "lessons": [
            "DLP must cover USB egress, not just email and web",
            "Exit and disciplinary processes need a defined evidence flow",
            "Insider-threat detection needs behavioural baselines, not just rules",
        ],
        "actions": [
            {"item": "Enable USB and email DLP policies (A.8.12)", "owner": "InfoSec"},
            {"item": "Reinforce the exit and disciplinary process (A.6.5)", "owner": "HR"},
            {"item": "Add insider-threat analytics to SIEM (A.8.16)", "owner": "Security operations"},
            {"item": "Refresh screening for high-access roles (A.6.1)", "owner": "HR"},
        ],
        "next_step": "People-controls review within 10 working days; DLP gap list into the ISMS risk register.",
    },
    {
        "title": "Compromised Credentials", "category": IT, "difficulty": "INTERMEDIATE",
        "description": "Multiple user credentials leaked in dark web forum enabling lateral movement.",

        "profile": "ISO/IEC 27001-certified BPO providing finance & accounting services",
        "iso_scope": "Finance & accounting services with access to client payment data",
        "systems": ["Client finance portals", "Corporate SSO / Active Directory", "Email", "VPN", "SIEM & UEBA"],
        "setting": "Monday 07:00 — OSINT monitoring flags a dark-web forum post.",
        "injects": [
            {"time": "07:00", "title": "Credentials for sale", "detail": "OSINT finds 40 employee credentials for sale on a dark-web forum, including a finance analyst with payment-data access."},
            {"time": "07:45", "title": "Passwords match SSO", "detail": "Some listed passwords match corporate SSO. The hunt for active use begins."},
            {"time": "09:30", "title": "Lateral movement flagged", "detail": "UEBA flags lateral movement from a listed account into a client finance portal; a $50 test transfer was made and reversed."},
        ],
        "inject1": "07:00 — OSINT monitoring finds 40 employee credentials for sale on a dark-web forum, including a finance analyst with access to client payment data. Some passwords match corporate SSO.",
        "q1": [
            "Do you reset passwords first, or hunt for active use? (A.8.4, A.8.5)",
            "How do you determine whether the accounts were used? (A.8.15, A.8.16)",
            "Who is told, and what is the risk to clients? (A.5.20, A.5.25)",
            "Do you force MFA everywhere immediately? (A.8.5)",
        ],
        "inject2": "09:30 — UEBA flags lateral movement from one of the listed accounts into a client finance portal. A test transfer of $50 was made and reversed.",
        "q2": [
            "How do you contain the lateral movement now? (A.8.31, A.8.3)",
            "Do you treat this as an active intrusion and engage forensics? (A.5.24, A.5.28)",
            "How do you verify payment-data integrity? (A.8.15)",
            "What notification duties exist for the affected client? (A.5.20)",
        ],
        "clause_map": [
            {"decision": "Reset credentials", "control": "A.8.4 / A.8.5 · Secure authentication", "guidance": "Enforce MFA and password reset (27002 §8.4–8.5)"},
            {"decision": "Detect active use", "control": "A.8.16 · Monitoring activities", "guidance": "UEBA and session analysis (27002 §8.16)"},
            {"decision": "Contain lateral movement", "control": "A.8.31 · Separation of environments", "guidance": "Isolate compromised paths (27002 §8.31)"},
            {"decision": "Engage forensics", "control": "A.5.24 / A.5.28 · Incident response & evidence", "guidance": "Structured response and evidence (27002 §5.24, §5.28)"},
            {"decision": "Client notification", "control": "A.5.20 · Supplier agreements", "guidance": "Contractual reporting (27002 §5.20)"},
            {"decision": "Lessons learned", "control": "A.5.27 · Learning from incidents", "guidance": "Improve identity controls (27002 §5.27)"},
        ],
        "hotwash": "Would we notice a $50 test transfer? How fast could we reset 40 accounts?",
        "highlights": [
            "All 40 leaked accounts were reset and MFA enforced the same day",
            "UEBA flagged lateral movement within hours of the alert",
            "The test transfer was traced and reversed before any client impact",
        ],
        "lessons": [
            "Dark-web credential monitoring should be a standing service, not an incident trigger",
            "MFA must cover every external access path, including client portals",
            "Payment-integrity checks should be automated for finance portals",
        ],
        "actions": [
            {"item": "Enforce MFA on all external access (A.8.5)", "owner": "IT"},
            {"item": "Subscribe to credential-monitoring (dark web) service (A.5.24)", "owner": "InfoSec"},
            {"item": "Add UEBA alerts for finance portals (A.8.16)", "owner": "Security operations"},
            {"item": "Review password policy and SSO (A.8.4)", "owner": "IT"},
        ],
        "next_step": "Identity-controls review within 5 working days; MFA coverage audit this month.",
    },
    {
        "title": "Cyberattack on CRM System", "category": IT, "difficulty": "ADVANCED",
        "description": "CRM system used for client interactions is compromised, exposing sensitive customer data.",

        "profile": "ISO/IEC 27001-certified BPO managing CRM platforms for six clients (sales, support, retention)",
        "iso_scope": "CRM platform management and customer-interaction services",
        "systems": ["Hosted CRM platform (shared across clients)", "Client sales & support data", "API integrations", "SIEM", "DLP"],
        "setting": "Two clients have active campaign data in the shared CRM system.",
        "injects": [
            {"time": "06:30", "title": "Admin access gained", "detail": "An attacker exploits an unpatched CRM plugin and gains admin access to the shared platform."},
            {"time": "07:10", "title": "Client data exfiltrated", "detail": "Customer data — names, contacts, purchase history — is exfiltrated for one client before the breach is detected."},
            {"time": "09:00", "title": "Second client exposed", "detail": "The vendor confirms the plugin vulnerability is public; scans show movement between client data silos — a second client exposed."},
        ],
        "inject1": "06:30 — an attacker exploits an unpatched CRM plugin and gains admin access to the shared platform. Customer data — names, contacts, purchase history — is exfiltrated for one client before the breach is detected.",
        "q1": [
            "Do you take the CRM offline now? What is the impact on client interactions? (A.5.25)",
            "How do you confirm the scope — which clients' data was touched? (A.8.15)",
            "Who is told first — the affected client, or all six? (A.5.20)",
            "How do you preserve evidence on the shared platform? (A.5.28)",
        ],
        "inject2": "09:00 — the vendor confirms the plugin vulnerability is public. Scans show the attacker moved between client data silos within the shared CRM. A second client's campaign data is exposed.",
        "q2": [
            "How do you segregate the client data silos going forward? (A.8.31)",
            "Do you rebuild the CRM from a clean backup? (A.8.13, A.8.9)",
            "What notification duties apply to the exposed customer data? (A.5.20, compliance)",
            "How do you patch and validate the plugin ecosystem? (A.8.8)",
        ],
        "clause_map": [
            {"decision": "Isolate the CRM", "control": "A.8.31 · Separation of environments", "guidance": "Contain the shared platform (27002 §8.31)"},
            {"decision": "Determine scope", "control": "A.8.15 · Logging", "guidance": "Trace access across silos (27002 §8.15)"},
            {"decision": "Patch the vulnerability", "control": "A.8.8 · Vulnerability management", "guidance": "Remediate the plugin (27002 §8.8)"},
            {"decision": "Rebuild cleanly", "control": "A.8.13 / A.8.9 · Backup & configuration", "guidance": "Restore from known-good (27002 §8.13, §8.9)"},
            {"decision": "Client notification", "control": "A.5.20 · Supplier agreements", "guidance": "Data-exposure reporting (27002 §5.20)"},
            {"decision": "Lessons learned", "control": "A.5.27 · Learning from incidents", "guidance": "Improve platform controls (27002 §5.27)"},
        ],
        "hotwash": "Could we run six clients on one CRM safely? What would true multi-tenancy look like?",
        "highlights": [
            "The shared CRM was isolated before the attacker could move further between silos",
            "The vulnerable plugin was patched and validated with the vendor",
            "Both affected clients were notified with a verified data-exposure statement",
        ],
        "lessons": [
            "Shared platforms need enforced client data segregation, not trust",
            "Plugin vulnerability scanning needs a scheduled cadence",
            "A rebuild-from-clean-backup playbook should exist before it is needed",
        ],
        "actions": [
            {"item": "Enforce client data segregation in the CRM (A.8.31)", "owner": "InfoSec"},
            {"item": "Add a vulnerability-scan and patch cadence for plugins (A.8.8)", "owner": "IT"},
            {"item": "Rebuild the CRM from a clean backup with config review (A.8.13, A.8.9)", "owner": "IT"},
            {"item": "Create a data-exposure notification template (A.5.20)", "owner": "Client delivery"},
        ],
        "next_step": "CRM platform review within 10 working days; multi-tenancy assessment this quarter.",
    },
    {
        "title": "Backup & Recovery DR Test", "category": IT, "difficulty": "ADVANCED",
        "description": "A scheduled disaster-recovery test exposes a corrupt backup set, a silent backup gap, and a blown recovery-time objective.",

        "profile": "ISO/IEC 27001-certified BPO running finance & accounting services for 9 clients",
        "iso_scope": "Finance & accounting services with nightly backups, quarterly restore tests and a stated 4-hour RTO",
        "systems": ["Backup platform (Veeam, nightly full + incremental)", "Client finance portal DB", "File shares (client PII)", "Monitoring / alerting", "DR runbook & RTO targets"],
        "setting": "Wednesday 09:00 — the quarterly DR test is underway: restore the client finance portal to a test environment and validate it. The test is supposed to take 4 hours.",
        "injects": [
            {"time": "09:15", "title": "Restore fails at 62%", "detail": "The first restore attempt of the finance portal DB fails at 62% — the backup set is corrupt and the restore job aborts."},
            {"time": "09:40", "title": "Silent backup gap found", "detail": "Backup jobs for the finance portal silently failed for 6 days. No alert fired. The last known-good restore point is 14 days old."},
            {"time": "10:30", "title": "RTO blown, clients impacted", "detail": "Recovery time objective (4h) is exceeded. Two clients' month-end batches cannot be produced; a decision is needed on declaring a disaster and invoking the hot site."},
        ],
        "inject1": "09:15 — the first restore attempt of the finance portal DB fails at 62%: the backup set is corrupt and the restore job aborts. This is a scheduled DR test, not an outage — but the clock is running.",
        "q1": [
            "Is this still a test, or do you declare a real incident? Who makes that call? (A.5.24, A.5.25)",
            "Do you quarantine the corrupt backup set to stop it being reused? (A.8.13)",
            "What is your restore path from the last known-good point — and how do you prove it? (A.8.13, A.8.15)",
            "Who in the room knows what the client SLAs actually guarantee on RTO? (A.5.20)",
        ],
        "inject2": "09:40 — backup jobs for the finance portal silently failed for 6 days. No alert fired because success-only notifications were configured. The last known-good restore point is 14 days old.",
        "q2": [
            "Do you restore from the 14-day-old point, and what data do you lose? (A.8.13)",
            "How do you validate the restored environment is clean and complete? (A.8.15, A.8.9)",
            "Do you invoke the hot site / alternate facility for capacity? (A.8.14, A.5.30)",
            "Which clients are told — and does the contract require disclosure of the test failure? (A.5.20)",
        ],
        "clause_map": [
            {"decision": "Quarantine the corrupt set", "control": "A.8.13 · Information backup", "guidance": "Protect and verify backup integrity (27002 §8.13)"},
            {"decision": "Declare a real incident", "control": "A.5.24 / A.5.25 · Incident response", "guidance": "Escalate and assess the DR-test failure (27002 §5.24–5.25)"},
            {"decision": "Restore from last known-good", "control": "A.8.13 · Information backup", "guidance": "Restore to a clean environment, verify integrity (27002 §8.13)"},
            {"decision": "Invoke hot site / alternate facility", "control": "A.8.14 · Redundancy of processing facilities", "guidance": "Maintain redundant capacity for recovery (27002 §8.14)"},
            {"decision": "Fix backup alerting", "control": "A.8.16 · Monitoring activities", "guidance": "Alert on failures, not just successes (27002 §8.16)"},
            {"decision": "Validate capacity & RTO", "control": "A.5.30 · ICT readiness", "guidance": "Test continuity arrangements under load (27002 §5.30)"},
            {"decision": "Client notification", "control": "A.5.20 · Supplier agreements", "guidance": "Contractual disclosure of service impact (27002 §5.20)"},
            {"decision": "Lessons learned", "control": "A.5.27 · Learning from incidents", "guidance": "Feed DR-test findings into the ISMS (27002 §5.27)"},
        ],
        "hotwash": "Would we have noticed a silent backup failure tomorrow? How old may the last good restore point get before it becomes unacceptable?",
        "highlights": [
            "The corrupt backup was found during a scheduled test, not during a real outage",
            "The last known-good restore point was confirmed before any destructive action",
            "Clients were notified within the contractual window once the RTO was blown",
        ],
        "lessons": [
            "Backup monitoring fired on success only — failure alerting is now a requirement",
            "Restore tests must validate the restore step, not just the backup job",
            "The 4-hour RTO was never validated under realistic load",
        ],
        "actions": [
            {"item": "Alert on backup job failures, not just successes (A.8.16)", "owner": "IT"},
            {"item": "Schedule quarterly restore tests that run to completion (A.8.13)", "owner": "IT"},
            {"item": "Validate RTO under realistic load and document it (A.5.30)", "owner": "CISO"},
            {"item": "Review client SLAs for RTO/RPO disclosure duties (A.5.20)", "owner": "Client delivery"},
        ],
        "next_step": "Backup & DR remediation review within 5 working days; restore-test cadence into the ISMS audit programme.",
    },
    # ------------------------- BUSINESS OPERATIONS ------------------------- #
    # Each BO scenario focuses on ONE client program under BPO operations,
    # with the INBOUND customer-care process as the only business process in
    # scope: every inject, decision and hotwash concerns the inbound voice,
    # chat and case queues — callers, answer times and customer SLAs — and
    # every question is addressed to the customer-care/client-delivery
    # managers or the care-operations/team-leader roles running that program.
    {
        "title": "Network Outage Affecting Global Connectivity", "category": BO, "difficulty": "INTERMEDIATE",
        "description": "The dedicated link to the client drops mid-shift, isolating a single inbound customer-care program.",

        "profile": "ISO/IEC 27001-certified BPO operating a single client's Customer Care Program \u2014 a dedicated, 24/7 inbound voice and chat operation with 450 seats",
        "iso_scope": "Client Customer Care Program \u2014 inbound voice, chat and customer case handling under one client contract",
        "systems": ["Dedicated link & client VPN", "Customer care platform (voice & chat)", "Case management & knowledge base", "Workforce management & scheduling", "Customer SLA dashboard"],
        "setting": "Mid-shift Thursday. The inbound care program is live on all queues; two priority complaint escalations are open with the client.",
        "injects": [
            {"time": "14:20", "title": "Dedicated link down", "detail": "The dedicated link to the client's systems drops; agents can no longer see customer records and the care platform stops accepting new inbound chats."},
            {"time": "14:50", "title": "Backup path fails", "detail": "The 4G/5G backup fails to carry care traffic. Inbound chats time out, abandoned-call rates climb and open escalations start ageing."},
            {"time": "15:05", "title": "Regional outage confirmed", "detail": "The telco confirms a regional outage with no ETA. The client calls about its open escalations, just 5% of the case queue; hold times climb across the inbound care queues."},
        ],
        "inject1": "14:20 \u2014 the dedicated link to the client's systems drops. Agents cannot reach customer records; the care platform stops accepting new inbound chats.",
        "inject1_name": "Dedicated link down",
        "decision_a_name": "Continuity call",
        "q1": [
            "Customer Care Manager \u2014 who declares a continuity event for the care program, and who triggers the BCP? (A.5.24, A.5.29)",
            "Care Operations Lead \u2014 which care queues stay live at degraded service \u2014 emergency and complaint lines first \u2014 and which are paused? (A.5.29)",
            "Team Leader \u2014 what do agents tell callers right now, and how do you keep the floor productive while customers wait? (A.5.24, A.6.7)",
            "WFM \u2014 how do you re-forecast inbound call volumes when disappointed customers keep calling in? (A.8.6)",
        ],
        "inject2": "15:05 \u2014 the telco confirms a regional outage with no ETA. The client calls about its open escalations, just 5% of the case queue; unanswered inbound calls and chats are building across the care program.",
        "inject2_name": "Regional outage confirmed",
        "decision_b_name": "Recovery & prioritisation",
        "q2": [
            "Customer Care Manager \u2014 what is the inbound backlog-clearing plan \u2014 unanswered calls, queued chats, open cases \u2014 once the link returns, and in what queue order? (A.5.29, A.8.6)",
            "Care Operations Lead \u2014 what service-level relief or credits do we offer the client, and who authorises it? (A.5.20)",
            "Client Delivery Manager \u2014 what timeline do we commit to the client for restored answer times, and how is progress reported? (A.5.20)",
            "WFM \u2014 what staffing and shift changes cover the inbound backlog catch-up window? (A.5.29)",
        ],
        "clause_map": [
            {"decision": "Declare continuity event", "control": "A.5.29 \u00b7 Continuity planning", "guidance": "Trigger the tested BCP (27002 \u00a75.29)"},
            {"decision": "Prioritise care queues", "control": "A.8.6 \u00b7 Capacity management", "guidance": "Balance load across queues and shifts (27002 \u00a78.6)"},
            {"decision": "Customer communication", "control": "A.5.20 \u00b7 Supplier agreements", "guidance": "SLA and notification terms (27002 \u00a75.20)"},
            {"decision": "Fallback work modes", "control": "A.6.7 \u00b7 Remote working", "guidance": "Alternate work arrangements (27002 \u00a76.7)"},
            {"decision": "Continuity readiness", "control": "A.5.30 \u00b7 ICT readiness", "guidance": "Tested continuity arrangements (27002 \u00a75.30)"},
            {"decision": "Lessons learned", "control": "A.5.27 \u00b7 Learning from incidents", "guidance": "Improve the continuity plan (27002 \u00a75.27)"},
        ],
        "hotwash": "How long could the inbound care program run degraded? What did callers actually experience at the worst point?",
        "highlights": [
            "The continuity plan was triggered within 15 minutes of the link dropping",
            "Callers got clear hold messaging while customer records were unreachable",
            "The client received a single, consistent status message from Client Delivery",
        ],
        "lessons": [
            "A single dedicated link is a single point of failure for inbound customer care",
            "Call-handling scripts for degraded service need live testing, not desk checks",
            "Customer visibility must survive a connectivity outage",
        ],
        "actions": [
            {"item": "Diversify the WAN paths with the telco (A.5.30)", "owner": "Operations"},
            {"item": "Tabletop the care continuity playbook (A.5.29)", "owner": "Customer Care Manager"},
            {"item": "Add a customer-visible status update routine (A.5.20)", "owner": "Client Delivery"},
            {"item": "Rehearse degraded call-handling scripts on the floor (A.6.3)", "owner": "Team Leaders"},
        ],
        "next_step": "Continuity plan update within 10 working days; failover test scheduled next month.",
    },
    {
        "title": "Fire at Secondary Site During Peak Hours", "category": BO, "difficulty": "ADVANCED",
        "description": "Fire closes Site B mid-peak; the single client inbound customer-care program loses half its delivery floor.",

        "profile": "ISO/IEC 27001-certified BPO delivering a client Customer Care Program from two sites; Site B runs half the inbound care queues at 90% capacity",
        "iso_scope": "Client Customer Care Program \u2014 inbound voice, chat and customer case handling under one client contract",
        "systems": ["Customer care platform (voice & chat)", "Care queue routing & overflow", "Site A / Site B seating & telephony", "Workforce management & scheduling", "Customer SLA dashboard"],
        "setting": "Monday 10:00, peak inbound call season. Site B is dedicated to the client program and running at 90% capacity.",
        "injects": [
            {"time": "10:05", "title": "Fire alarm at Site B", "detail": "A fire alarm sounds in the Site B server room; suppression activates and the care floor evacuates. Calls to the Site B inbound queues go unanswered."},
            {"time": "10:20", "title": "Care queues unreachable", "detail": "Site A cannot see or answer the Site B inbound care queues. Answer times blow through the client's SLA and inbound chats pile up."},
            {"time": "12:30", "title": "Site loss confirmed", "detail": "The fire is contained but Site B is unusable for days. The unanswered-call and pending-case backlog is growing and the client asks for a recovery timeline."},
        ],
        "inject1": "10:05 \u2014 a fire alarm sounds in the Site B server room. Suppression activates, the care floor evacuates and calls to the Site B inbound queues go unanswered.",
        "inject1_name": "Fire alarm at Site B",
        "decision_a_name": "Safety & continuity",
        "q1": [
            "Customer Care Manager \u2014 who declares a site-loss continuity event for the care program, and what is their authority? (A.5.24, A.5.29)",
            "Care Operations Lead \u2014 which inbound care queues move to Site A today, and which are suspended? (A.5.29)",
            "Team Leader \u2014 how do you account for every evacuated care agent and redeploy the ones Site A can take? (A.5.29, A.6.7)",
            "Client Delivery Manager \u2014 what is the notification sequence to the client, and who owns each message? (A.5.20)",
        ],
        "inject2": "12:30 \u2014 Site B is unusable for days. The unanswered-call and pending-case backlog is growing through peak season and the client wants a recovery timeline today.",
        "inject2_name": "Site loss confirmed",
        "decision_b_name": "Recovery & backlog",
        "q2": [
            "Customer Care Manager \u2014 how is the unanswered-call and pending-chat backlog triaged and worked down across sites? (A.5.29, A.8.6)",
            "Care Operations Lead \u2014 how is Site A capacity allocated across the inbound queues \u2014 emergency and complaint lines first? (A.8.6)",
            "Client Delivery Manager \u2014 what turnaround and service-credit position do we give the client? (A.5.20)",
            "Customer Care Manager \u2014 what is the plan and timeline to resume the Site B care operation? (A.5.29, A.5.30)",
        ],
        "clause_map": [
            {"decision": "Declare site-loss event", "control": "A.5.29 \u00b7 Continuity planning", "guidance": "Trigger the site BCP (27002 \u00a75.29)"},
            {"decision": "Redistribute care queues", "control": "A.5.30 \u00b7 ICT readiness", "guidance": "Alternate-site arrangements (27002 \u00a75.30)"},
            {"decision": "Capacity reallocation", "control": "A.8.6 \u00b7 Capacity management", "guidance": "Absorb care load at Site A (27002 \u00a78.6)"},
            {"decision": "Customer communication", "control": "A.5.20 \u00b7 Supplier agreements", "guidance": "Turnaround and credit terms (27002 \u00a75.20)"},
            {"decision": "Workforce redeployment", "control": "A.6.7 \u00b7 Remote working", "guidance": "Redeploy care agents safely (27002 \u00a76.7)"},
            {"decision": "Lessons learned", "control": "A.5.27 \u00b7 Learning from incidents", "guidance": "Improve site resilience (27002 \u00a75.27)"},
        ],
        "hotwash": "Could Site A absorb the full inbound call volume tomorrow morning? What is our real inbound answer rate without Site B?",
        "highlights": [
            "The site was evacuated safely with every care agent accounted for",
            "Care queues were redistributed to Site A by end of day",
            "The client received a turnaround estimate backed by a real capacity number",
        ],
        "lessons": [
            "Site A absorption capacity for the inbound program was assumed, not measured",
            "Care-queue overflow needs an alternate-site arrangement, not just a backup",
            "Staff accountability after evacuation must be a rehearsed routine",
        ],
        "actions": [
            {"item": "Measure and publish Site A care capacity (A.8.6)", "owner": "Care Operations Lead"},
            {"item": "Stand up an alternate-site runbook for the care platform (A.5.30)", "owner": "Operations"},
            {"item": "Agree an unanswered-call backlog-triage protocol with the client (A.5.20)", "owner": "Client Delivery"},
            {"item": "Rehearse evacuation accountability on every shift (A.5.29)", "owner": "Team Leaders"},
        ],
        "next_step": "Site recovery plan review within 10 working days; care absorption test next month.",
    },
    {
        "title": "Complete Power Outage at HQ", "category": BO, "difficulty": "ADVANCED",
        "description": "A multi-hour power outage takes the client inbound customer-care center offline mid peak inbound call window.",

        "profile": "ISO/IEC 27001-certified BPO running a client inbound Customer Care Program from a single HQ delivery center with 900 seats",
        "iso_scope": "Client Customer Care Program \u2014 inbound voice, chat and customer case handling under one client contract",
        "systems": ["Care agent desktops & telephony (HQ)", "Customer care platform (voice & chat)", "Workforce management & scheduling", "Customer SLA dashboard", "Peak call-window calendar"],
        "setting": "Weekday 15:00, with the client's billing-cycle announcement driving peak inbound call volumes into the close of day.",
        "injects": [
            {"time": "15:05", "title": "Regional power loss", "detail": "A regional outage hits HQ; the UPS carries the floor briefly but the backup generators fail to start."},
            {"time": "15:20", "title": "Floor shutting down", "detail": "Workstations and telephony shut down mid-call; inbound customers are disconnected and 100% of care agents are losing their systems."},
            {"time": "16:00", "title": "Extended outage confirmed", "detail": "The utility reports power out for 25% of the operating day or more; generators can be repaired, but not before midnight. The inbound care SLA is at risk."},
        ],
        "inject1": "15:05 \u2014 a regional power outage hits HQ. The UPS engages, but the backup generators fail to start and the care floor begins to shut down.",
        "inject1_name": "Regional power loss",
        "decision_a_name": "Continuity triage",
        "q1": [
            "Customer Care Manager \u2014 which inbound care channels are critical enough to keep running \u2014 emergency and complaint lines first \u2014 and which are suspended? (A.5.29)",
            "Customer Care Manager \u2014 who has authority to suspend care queues and to inform the client? (A.5.24, A.5.20)",
            "Team Leader \u2014 what is the floor plan for your care team right now \u2014 redeploy, release, or hold? (A.6.7, A.5.29)",
            "Care Operations Lead \u2014 how are in-flight calls and open chats handed over so no customer is dropped mid-interaction? (A.5.29)",
        ],
        "inject2": "16:00 \u2014 the utility confirms power out for 25% of the operating day; generators repair after midnight. Deferred inbound calls and chats pile up with the answer-time SLA immovable.",
        "inject2_name": "Extended outage confirmed",
        "decision_b_name": "Sustained operations",
        "q2": [
            "WFM \u2014 what staffing and scheduling changes sustain inbound customer care through a multi-hour outage? (A.5.29, A.8.6)",
            "Client Delivery Manager \u2014 which care commitments and SLA deadlines move, and how are the renegotiations handled? (A.5.20)",
            "Customer Care Manager \u2014 what is the order for resuming suspended inbound care queues once the site reopens? (A.5.29)",
            "Care Operations Lead \u2014 how is service-level progress reported to the client during the extended outage? (A.5.20)",
        ],
        "clause_map": [
            {"decision": "Continuity triage", "control": "A.5.29 \u00b7 Continuity planning", "guidance": "Trigger the site BCP (27002 \u00a75.29)"},
            {"decision": "Suspend care queues", "control": "A.5.24 \u00b7 Incident management planning", "guidance": "Coordinated decisions and authority (27002 \u00a75.24)"},
            {"decision": "Fallback work modes", "control": "A.6.7 \u00b7 Remote working", "guidance": "Continue critical care off-site (27002 \u00a76.7)"},
            {"decision": "Customer SLA deadlines", "control": "A.5.20 \u00b7 Supplier agreements", "guidance": "Renegotiate commitments (27002 \u00a75.20)"},
            {"decision": "Queue resumption order", "control": "A.8.6 \u00b7 Capacity management", "guidance": "Bring care queues back safely (27002 \u00a78.6)"},
            {"decision": "Lessons learned", "control": "A.5.27 \u00b7 Learning from incidents", "guidance": "Improve power resilience (27002 \u00a75.27)"},
        ],
        "hotwash": "Would our inbound customer care service have survived an outage lasting 25% of the operating day? Where does the inbound answer-time SLA break first?",
        "highlights": [
            "Triage was completed before the floor went dark, protecting in-flight customer interactions",
            "Emergency and complaint lines continued through the fallback arrangement",
            "The client knew the revised timeline before the SLA was breached",
        ],
        "lessons": [
            "The inbound care program's dependency on HQ needs a documented contingency",
            "Fallback work arrangements must be tested at real care scale",
            "Release-or-hold decisions for the floor need a pre-agreed script",
        ],
        "actions": [
            {"item": "Document the care continuity contingency for HQ (A.5.29)", "owner": "Customer Care Manager"},
            {"item": "Test fallback care work at full program scale (A.6.7)", "owner": "Operations"},
            {"item": "Agree SLA relief terms with the client in advance (A.5.20)", "owner": "Client Delivery"},
            {"item": "Write the floor release-or-hold script into the BCP (A.5.24)", "owner": "Team Leaders"},
        ],
        "next_step": "Power-resilience review within 10 working days; fallback care drill scheduled.",
    },
    {
        "title": "Geopolitic Concerns Reducing Workforce Availability", "category": BO, "difficulty": "ADVANCED",
        "description": "A health crisis removes 60% of the workforce from the client inbound customer-care program.",

        "profile": "ISO/IEC 27001-certified BPO running a client Customer Care Program with a 2,000-agent dedicated inbound team",
        "iso_scope": "Client Customer Care Program \u2014 inbound voice, chat and customer case handling under one client contract",
        "systems": ["Care queues (voice & chat)", "Workforce management & scheduling", "Customer SLA dashboard", "Absence & attendance tracking", "Cross-training matrix"],
        "setting": "Monday morning. A fast-spreading respiratory illness is reported across the city; the inbound care program team is calling in sick shift by shift.",
        "injects": [
            {"time": "09:00", "title": "60% absenteeism", "detail": "60% of the care program workforce is unavailable \u2014 sick, isolating or caring for family. Every inbound shift runs at 40% of planned headcount."},
            {"time": "09:30", "title": "Critical windows at risk", "detail": "Answer-time commitments on the inbound voice and chat queues are at risk; abandoned-call rates climb and the client asks for status."},
            {"time": "Tue 09:00", "title": "Service-credit trigger", "detail": "Absenteeism holds at 60%; the program answers 30% of inbound calls and the client triggers a service-credit clause."},
        ],
        "inject1": "By 09:00, 60% of the care program workforce is unavailable \u2014 sick, isolating or caring for family. Every inbound shift runs at 40% of planned headcount and the answer-time commitments are at risk.",
        "inject1_name": "Mass absenteeism",
        "decision_a_name": "Prioritisation",
        "q1": [
            "Customer Care Manager \u2014 which inbound care queues receive the staff that reported in? (A.5.29)",
            "Care Operations Lead \u2014 do you redeploy agents across the inbound queues, or protect the emergency and complaint lines? (A.5.29, A.8.6)",
            "Client Delivery Manager \u2014 what capacity message goes to the client, and when? (A.5.20)",
            "WFM \u2014 how do you forecast day-by-day availability and set minimum staffing per care queue? (A.5.29)",
        ],
        "inject2": "Tuesday \u2014 absenteeism holds at 60%. The program answers 30% of inbound calls and the client triggers a service-credit clause in the contract.",
        "inject2_name": "Service-credit trigger",
        "decision_b_name": "Sustained delivery",
        "q2": [
            "Team Leader \u2014 how do you triage inbound care work \u2014 emergency and complaint lines first, non-essential inbound queues paused? (A.5.29)",
            "Customer Care Manager \u2014 what surge capacity exists \u2014 contractors, cross-trained agents, overtime, other sites? (A.5.30, A.8.6)",
            "Care Operations Lead \u2014 how is SLA impact tracked and reported to the client per inbound care queue? (A.5.20)",
            "WFM \u2014 what workload limits and shift patterns keep the remaining care staff sustainable? (A.5.29)",
        ],
        "clause_map": [
            {"decision": "Prioritise care queues", "control": "A.5.29 \u00b7 Continuity planning", "guidance": "BCP for people availability (27002 \u00a75.29)"},
            {"decision": "Capacity management", "control": "A.8.6 \u00b7 Capacity management", "guidance": "Queue and load limits (27002 \u00a78.6)"},
            {"decision": "Customer reporting", "control": "A.5.20 \u00b7 Supplier agreements", "guidance": "SLA breach and service credits (27002 \u00a75.20)"},
            {"decision": "Surge arrangements", "control": "A.5.30 \u00b7 ICT readiness", "guidance": "Continuity arrangements (27002 \u00a75.30)"},
            {"decision": "Workforce wellbeing", "control": "A.6.1 / A.6.7 \u00b7 People controls", "guidance": "People controls during crisis (27002 \u00a76.1, \u00a76.7)"},
            {"decision": "Lessons learned", "control": "A.5.27 \u00b7 Learning from incidents", "guidance": "Improve workforce resilience (27002 \u00a75.27)"},
        ],
        "hotwash": "Could the inbound care program run at 40% staffing? What is our true minimum viable staffing per inbound queue?",
        "highlights": [
            "Inbound care queues were prioritised and the capacity message reached the client within hours",
            "Cross-training absorbed part of the absenteeism shock on day one",
            "SLA impact was tracked and reported per queue, not in aggregate",
        ],
        "lessons": [
            "Minimum viable staffing per inbound care queue should be defined in advance",
            "The cross-training matrix was thinner than the BCP assumed",
            "Workload limits for remaining care staff need active enforcement",
        ],
        "actions": [
            {"item": "Define minimum viable staffing per inbound care queue (A.5.29)", "owner": "Customer Care Manager"},
            {"item": "Expand the cross-training matrix across care channels (A.6.3)", "owner": "Team Leaders"},
            {"item": "Build the customer capacity-reporting routine (A.5.20)", "owner": "Client Delivery"},
            {"item": "Set enforced workload limits for crisis shifts (A.5.29)", "owner": "WFM"},
        ],
        "next_step": "Workforce-resilience plan within 10 working days; minimum care staffing reviewed with the client.",
    },
    {
        "title": "Vishing Attack", "category": BO, "difficulty": "INTERMEDIATE",
        "description": "Spoofed inbound calls to the care desk harvest customer data and trigger fraudulent account changes.",

        "profile": "ISO/IEC 27001-certified BPO running a client Customer Care Program \u2014 inbound voice and chat care with account servicing under one client contract",
        "iso_scope": "Client Customer Care Program \u2014 inbound voice, chat and customer account servicing under one client contract",
        "systems": ["Customer care desk (voice & chat)", "Account change & customer verification workflow", "Case management & knowledge base", "Care quality monitoring", "Workforce management & scheduling"],
        "setting": "Thursday afternoon. The care desk is handling a high volume of inbound account-change requests ahead of the client's billing date.",
        "injects": [
            {"time": "14:10", "title": "Spoofed calls", "detail": "Care agents receive calls from 'the client's fraud team' and 'internal support' asking them to bypass identity checks and update customer accounts urgently."},
            {"time": "14:35", "title": "Accounts changed", "detail": "3% of customer accounts are changed and fraudulent withdrawals equal to 30% of the day's payment value are initiated before anyone flags the calls as suspicious."},
            {"time": "15:00", "title": "Fraud confirmed", "detail": "Customers report account takeovers and the fraud is confirmed. A further 15% of care agents admit they received similar calls today."},
        ],
        "inject1": "14:10 \u2014 care agents receive calls from 'the client's fraud team' and 'internal support' asking them to bypass identity checks. 3% of customer accounts are changed before anyone flags it.",
        "inject1_name": "Spoofed calls",
        "decision_a_name": "Contain the fraud",
        "q1": [
            "Customer Care Manager \u2014 do you suspend account servicing on the care desk immediately, and who authorises that call? (A.5.24, A.5.25)",
            "Care Operations Lead \u2014 which customer accounts and queues are affected, and what is the customer impact? (A.5.20)",
            "Customer Care Manager \u2014 what is the escalation path \u2014 care leadership, client contacts, fraud team? (A.5.24)",
            "Team Leader \u2014 how do you keep the care desk answering calls for unaffected work while changes are paused? (A.5.29, A.5.30)",
        ],
        "inject2": "15:00 \u2014 the fraud is confirmed with customer accounts taken over. A further 15% of care agents admit they received similar calls today.",
        "inject2_name": "Fraud confirmed",
        "decision_b_name": "Prevent recurrence",
        "q2": [
            "Care Operations Lead \u2014 what identity-verification controls now apply to every inbound customer account interaction? (A.5.24, A.5.25)",
            "Customer Care Manager \u2014 how is account servicing resumed, and who signs off? (A.5.29)",
            "Client Delivery Manager \u2014 which customer and regulatory notifications are required, and who owns them? (A.5.20)",
            "Team Leader \u2014 what briefing does the care desk get before the next shift? (A.6.3)",
        ],
        "clause_map": [
            {"decision": "Pause account servicing", "control": "A.5.25 \u00b7 Incident assessment", "guidance": "Assess and act fast (27002 \u00a75.25)"},
            {"decision": "Escalation path", "control": "A.5.24 \u00b7 Incident management planning", "guidance": "Predefined authority (27002 \u00a75.24)"},
            {"decision": "Verification controls", "control": "A.5.24 / A.5.25 \u00b7 Planning & assessment", "guidance": "Approval and verification rules (27002 \u00a75.24\u20135.25)"},
            {"decision": "Resume servicing", "control": "A.5.29 \u00b7 Continuity planning", "guidance": "Restore care service safely (27002 \u00a75.29)"},
            {"decision": "Customer & regulator notice", "control": "A.5.20 \u00b7 Supplier agreements", "guidance": "Notification duties (27002 \u00a75.20)"},
            {"decision": "Care desk awareness", "control": "A.6.3 \u00b7 Awareness", "guidance": "Fraud-awareness briefing (27002 \u00a76.3)"},
        ],
        "hotwash": "Would our care desk challenge a call like that today? What is the customer identity-verification ritual on every account change?",
        "highlights": [
            "Account servicing was paused before the second fraudulent change could complete",
            "Affected customers were identified and notified within the hour",
            "The care desk kept answering calls for unaffected work during the pause",
        ],
        "lessons": [
            "Account changes need dual verification \u2014 a single agent's judgement is too easy to spoof",
            "Customer verification must be a desk ritual, not a guideline",
            "Fraud-awareness briefings must reach the care desk, not just the floor",
        ],
        "actions": [
            {"item": "Introduce dual verification for customer account changes (A.5.24)", "owner": "Customer Care Manager"},
            {"item": "Add a customer-verification ritual to the care runbook (A.6.3)", "owner": "Team Leaders"},
            {"item": "Write the pause-and-resume procedure into the BCP (A.5.29)", "owner": "Operations"},
            {"item": "Brief the care desk and the client on the new controls (A.5.20)", "owner": "Client Delivery"},
        ],
        "next_step": "Verification-controls review within 5 working days; care desk briefing refreshed this month.",
    },
]

SCENARIO_DECKS = [_build_deck(s) for s in SCENARIOS]
