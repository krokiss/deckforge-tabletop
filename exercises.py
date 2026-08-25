"""Cyber-incident tabletop exercise decks for Business Process Outsourcing
(BPO), aligned to ISO/IEC 27001:2022 (Annex A controls) and ISO/IEC 27002:2022
(implementation guidance for those controls).

Each exercise follows the same arc: title -> objectives & ground rules ->
scenario background -> roles -> injects (revelations) -> decision points
(discussion questions) -> ISO/IEC 27001 clause map -> hotwash ->
after-action review.

Note on naming: "ISO 72001" is a common industry mislabel of ISO/IEC 27001
(the information-security management requirements standard). The clause maps
below cite 27001:2022 Annex A control numbers, with 27002:2022 guidance.
"""

from scenarios import (AAR_ASSESSMENT_DEFAULT, AAR_BODY, AAR_CAPABILITY_DEFAULT,
                       AAR_DECISIONS_REQUESTED, AAR_EVIDENCE_PACK, AAR_FRAMEWORK_ALIGNMENT,
                       AAR_KPIS, AAR_META_DEFAULT, AAR_ROADMAP, AAR_SCORE_DEFAULT,
                       SCENARIO_DECKS, capa_rows, deck_story, inject_slides,
                       recommendations_from_actions)

EXERCISE_DECKS = [
    # ------------------------------------------------------------------ #
    # Deck 1 — Ransomware at a BPO                                         #
    # ------------------------------------------------------------------ #
    {
        "name": "Table Top Exercise · Ransomware at a BPO",

        "slides": [
            {
                "name": "Title",

                "layout": "title",
                "body": "# Table Top Exercise\n\n## {{scenario.title}}\n\n{{scenario.kicker}}",
                "data": {
                    "scenario": {
                        "title": "Ransomware at a BPO",
                        "kicker": "Cyber Incident Tabletop · ISO/IEC 27001:2022 & ISO/IEC 27002:2022 · 90 minutes · Facilitated discussion",
                    },
                },
            },
            {
                "name": "Objectives & ground rules",

                "layout": "content",
                "body": "## {{objectives.title}}\n\n{{#each objectives.items}}\n- {{this}}\n{{/each}}\n\n**Ground rules:** {{ground_rules}}",
                "data": {
                    "objectives": {
                        "title": "Objectives & ground rules",
                        "items": [
                            "Test incident response when client data and client SLAs are at stake",
                            "Map every decision to an ISO/IEC 27001:2022 Annex A control",
                            "Expose gaps in monitoring, isolation and supplier agreements",
                            "Leave with an after-action list with owners and dates",
                        ],
                    },
                    "ground_rules": "Stay in role. No wrong answers — this is a discussion, not a test. Call out what you don't know. Every decision gets an Annex A control.",
                },
            },
            {
                "name": "Scenario background",

                "layout": "content",
                "body": "## Scenario background\n\n**Organisation:** {{company.profile}}\n\n**ISO/IEC 27001 scope:** {{iso_scope}}\n\n**Key systems:**\n{{#each systems}}\n- {{this}}\n{{/each}}\n\n**Setting:** {{setting}}",
                "data": {
                    "company": {

                        "profile": "ISO/IEC 27001-certified BPO: customer support, finance & accounting, and claims processing for 9 clients across banking, healthcare and retail",
                    },
                    "iso_scope": "Outsourced customer support, finance & accounting and claims-processing services",
                    "systems": [
                        "Contact-center platform (CTI + CRM)",
                        "Claims-processing environment (shared with clients)",
                        "Client data shares (SFTP, mapped drives)",
                        "Corporate AD, email and endpoint fleet (~1,400 agents, 40% remote)",
                        "Backup infrastructure (daily, restored quarterly)",
                    ],
                    "setting": "It is 09:00 on a Tuesday. Two clients have month-end claims batches in progress and one has a service-level review that morning.",
                },
            },
            {
                "name": "Roles",

                "layout": "content",
                "body": "## Roles & responsibilities\n\n| Role | Owner | Key concerns |\n|------|-------|--------------|\n{{#each roles}}\n| {{role}} | {{owner}} | {{concern}} |\n{{/each}}",
                "data": {
                    "roles": [
                        {"role": "Corporate Security", "owner": "Security", "concern": "Information & privacy security (A.5.x, A.8.2)"},
                        {"role": "IT Server & System Team", "owner": "Infrastructure", "concern": "Servers, systems, recovery (A.8.13)"},
                        {"role": "IT Desktop Team", "owner": "End-user computing", "concern": "Endpoints, patching, user access (A.8.7, A.8.8)"},
                        {"role": "IT Network Team", "owner": "Networking", "concern": "Connectivity, segmentation, VPN (A.8.20, A.8.31)"},
                        {"role": "Compliance", "owner": "Legal & Compliance", "concern": "Legal & compliance concerns (A.5.20, A.5.34)"},
                        {"role": "Human Resources", "owner": "HR", "concern": "Employee policies & violations (A.6.1, A.6.3)"},
                        {"role": "Marketing", "owner": "Corporate communications", "concern": "Official corporate press statements (A.5.20)"},
                        {"role": "Executive Leadership", "owner": "C-suite", "concern": "Executive decision-making (A.5.24)"},
                    ],
                },
            },
            {
                "name": "Inject 1 — Detection",

                "layout": "section",
                "body": "# Inject 1 — Detection\n\n{{text}}",
                "data": {
                    "text": "09:05 — A phishing email captured an agent's credentials. Encryption activity is detected on the claims-processing environment and a client-shared drive. Nothing is down yet — but it is spreading.",
                },
            },
            {
                "name": "Decision A — Initial response",

                "layout": "content",
                "body": "## Decision A — Initial response\n\n{{#each questions}}\n1. {{this}}\n{{/each}}\n\n**Timebox:** {{timebox}}",
                "data": {
                    "questions": [
                        "Who leads, and what is the escalation trigger to the client delivery lead? (A.5.24, A.5.25)",
                        "Do you isolate client environments from each other right now? What breaks? (A.8.31)",
                        "What evidence do you preserve, and where? (A.8.15)",
                        "Which client gets told first — and what is the contractual notification trigger? (A.5.20)",
                    ],
                    "timebox": "15 minutes",
                },
            },
            {
                "name": "Inject 2 — Escalation",

                "layout": "section",
                "body": "# Inject 2 — Escalation\n\n{{text}}",
                "data": {
                    "text": "09:45 — Two clients' SLAs are now being missed and a month-end claims batch is stalled. The ransom note demands $400,000 in crypto. Client PII is believed to be within the encrypted scope.",
                },
            },
            {
                "name": "Decision B — Client impact",

                "layout": "content",
                "body": "## Decision B — Client impact\n\n{{#each questions}}\n1. {{this}}\n{{/each}}\n\n**Timebox:** {{timebox}}",
                "data": {
                    "questions": [
                        "Do you pay the ransom? Who decides, and under what client contract? (A.5.25)",
                        "How do you restore the claims batch — and prove it is clean? (A.8.13)",
                        "What do you tell each of the nine clients — same message or per-client? (A.5.20)",
                        "Which regulators and breach-notification duties apply to client PII? (A.5.24, compliance)",
                    ],
                    "timebox": "20 minutes",
                },
            },
            {
                "name": "ISO/IEC 27001 clause map",

                "layout": "content",
                "body": "## Aligning decisions to ISO/IEC 27001\n\n| Decision | ISO/IEC 27001:2022 control | ISO/IEC 27002:2022 guidance |\n|----------|----------------------------|-----------------------------|\n{{#each clause_map}}\n| {{decision}} | {{control}} | {{guidance}} |\n{{/each}}\n\n*ISO/IEC 27002:2022 is the code of practice that guides implementation of the Annex A controls referenced above.*",
                "data": {
                    "clause_map": [
                        {"decision": "Isolate client environments", "control": "A.8.31 · Separation of environments", "guidance": "Segregate client data & processing (27002 §8.31)"},
                        {"decision": "Preserve evidence", "control": "A.8.15 · Logging", "guidance": "Log, protect and review records (27002 §8.15)"},
                        {"decision": "Notify client per SLA", "control": "A.5.20 · Supplier agreements", "guidance": "Contractual security & notification terms (27002 §5.20)"},
                        {"decision": "Pay / refuse ransom", "control": "A.5.24 / A.5.25 · Incident planning & assessment", "guidance": "Assess, decide, involve leadership (27002 §5.24–5.25)"},
                        {"decision": "Restore from backup", "control": "A.8.13 · Information backup", "guidance": "Restore to a clean environment, verify integrity (27002 §8.13)"},
                        {"decision": "Lessons learned", "control": "A.5.27 / A.5.28 · Learning & evidence", "guidance": "Improve controls from the incident (27002 §5.27–5.28)"},
                    ],
                },
            },
            {
                "name": "Hotwash",

                "layout": "section",
                "body": "# Hotwash\n\n{{text}}",
                "data": {
                    "text": "How fast could we actually isolate one client from another? Would we notice a slow, quiet exfiltration?",
                },
            },
            {
                "name": "After Action Executive Summary",

                "layout": "content",
                "body": "## After Action Executive Summary\n\n**Exercise:** {{exercise.name}}\n**Date:** {{exercise.date | default:\"—\"}}\n**Participants:** {{participants | default:\"—\"}}\n\n### Exercise highlights\n{{#each highlights}}\n- {{this}}\n{{/each}}\n\n### Lessons learned\n{{#each lessons}}\n- {{this}}\n{{/each}}",
                "data": {
                    "exercise": {"name": "Ransomware at a BPO", "date": ""},
                    "participants": "CISO, Client delivery, InfoSec, Service desk, Communications",
                    "highlights": [
                        "The claims environment was isolated from client shares within the first 15 minutes",
                        "All nine clients were briefed with a single, consistent message",
                        "Decisions were mapped live to Annex A controls (A.8.31, A.8.13, A.5.20)",
                    ],
                    "lessons": [
                        "Client environments are only as segmented as the file shares they touch",
                        "Backup restore of the claims environment had not been exercised end-to-end this year",
                        "The ransom decision needs a pre-agreed escalation authority",
                    ],
                },
            },
            {
                "name": "After-action review",

                "layout": "content",
                "body": "## After-action review\n\n{{#each actions}}\n- **{{item}}** — owner: {{owner}}\n{{/each}}\n\n**Next step:** {{next_step}}",
                "data": {
                    "actions": [
                        {"item": "Segment client environments and test isolation (A.8.31)", "owner": "InfoSec"},
                        {"item": "Tune detection for client-data exfiltration (A.8.12, A.8.16)", "owner": "Security operations"},
                        {"item": "Review client agreements for incident-notification SLAs (A.5.20)", "owner": "Client delivery"},
                        {"item": "Re-test backup restore of the claims environment (A.8.13)", "owner": "Service desk"},
                    ],
                    "next_step": "Incident review with all nine clients within 5 working days; findings into the ISMS risk treatment plan.",
                },
            },
        ],
    },
    # ------------------------------------------------------------------ #
    # Deck 2 — Breach via the remote-access vendor                         #
    # ------------------------------------------------------------------ #
    {
        "name": "Table Top Exercise · Breach via Remote-Access Vendor",

        "slides": [
            {
                "name": "Title",

                "layout": "title",
                "body": "# Table Top Exercise\n\n## {{scenario.title}}\n\n{{scenario.kicker}}",
                "data": {
                    "scenario": {
                        "title": "Breach via Remote-Access Vendor",
                        "kicker": "Cyber Incident Tabletop · ISO/IEC 27001:2022 & ISO/IEC 27002:2022 · 90 minutes · Focus on the ICT supply chain (A.5.21)",
                    },
                },
            },
            {
                "name": "Objectives & ground rules",

                "layout": "content",
                "body": "## {{objectives.title}}\n\n{{#each objectives.items}}\n- {{this}}\n{{/each}}\n\n**Ground rules:** {{ground_rules}}",
                "data": {
                    "objectives": {
                        "title": "Objectives & ground rules",
                        "items": [
                            "Decide how far a vendor compromise reaches into our client-facing operations",
                            "Apply the ICT supply-chain controls (A.5.19–A.5.21) under pressure",
                            "Handle the client-data exposure question without over- or under-reacting",
                            "Define supplier reassessment and corrective actions",
                        ],
                    },
                    "ground_rules": "Stay in role. Say 'we don't know' instead of guessing. Every decision gets an Annex A control.",
                },
            },
            {
                "name": "Scenario background",

                "layout": "content",
                "body": "## Scenario background\n\n**Organisation:** {{company.profile}}\n\n**ISO/IEC 27001 scope:** {{iso_scope}}\n\n**Key systems:**\n{{#each systems}}\n- {{this}}\n{{/each}}\n\n**Setting:** {{setting}}",
                "data": {
                    "company": {

                        "profile": "ISO/IEC 27001-certified BPO providing HR and payroll administration to 12 corporate clients",
                    },
                    "iso_scope": "HR and payroll administration services delivered through a third-party remote-workforce platform",
                    "systems": [
                        "Remote-workforce (VDI) platform — third-party vendor, used by all agents",
                        "Client HR & payroll portals (client-issued access)",
                        "Payroll processing queue and PII data store",
                        "Session-recording and quality-monitoring tools",
                        "Corporate AD, email, SIEM",
                    ],
                    "setting": "Monday 07:00. The VDI vendor deployed a routine platform update over the weekend. Two clients have payroll runs due Wednesday.",
                },
            },
            {
                "name": "Roles",

                "layout": "content",
                "body": "## Roles & responsibilities\n\n| Role | Owner | Key concerns |\n|------|-------|--------------|\n{{#each roles}}\n| {{role}} | {{owner}} | {{concern}} |\n{{/each}}",
                "data": {
                    "roles": [
                        {"role": "Corporate Security", "owner": "Security", "concern": "Information & privacy security (A.5.x, A.8.2)"},
                        {"role": "IT Server & System Team", "owner": "Infrastructure", "concern": "Servers, systems, recovery (A.8.13)"},
                        {"role": "IT Desktop Team", "owner": "End-user computing", "concern": "Endpoints, patching, user access (A.8.7, A.8.8)"},
                        {"role": "IT Network Team", "owner": "Networking", "concern": "Connectivity, segmentation, VPN (A.8.20, A.8.31)"},
                        {"role": "Compliance", "owner": "Legal & Compliance", "concern": "Legal & compliance concerns (A.5.20, A.5.34)"},
                        {"role": "Human Resources", "owner": "HR", "concern": "Employee policies & violations (A.6.1, A.6.3)"},
                        {"role": "Marketing", "owner": "Corporate communications", "concern": "Official corporate press statements (A.5.20)"},
                        {"role": "Executive Leadership", "owner": "C-suite", "concern": "Executive decision-making (A.5.24)"},
                    ],
                },
            },
            {
                "name": "Inject 1 — Compromised platform",

                "layout": "section",
                "body": "# Inject 1 — Compromised platform\n\n{{text}}",
                "data": {
                    "text": "07:15 — The VDI vendor confirms its weekend update was compromised. Some agent sessions — including screen recordings — were accessed by the attacker. The vendor says several other BPOs are affected.",
                },
            },
            {
                "name": "Decision A — Initial response",

                "layout": "content",
                "body": "## Decision A — Initial response\n\n{{#each questions}}\n1. {{this}}\n{{/each}}\n\n**Timebox:** {{timebox}}",
                "data": {
                    "questions": [
                        "Do you suspend the vendor platform immediately? What happens to client payroll runs? (A.5.21, A.5.30)",
                        "What evidence do you request from the vendor, and on what legal basis? (A.5.28)",
                        "Which clients are affected — and what do you tell them today? (A.5.20)",
                        "Can agents reach client systems through an alternative path while this is investigated? (A.5.29)",
                    ],
                    "timebox": "15 minutes",
                },
            },
            {
                "name": "Inject 2 — Exposure window",

                "layout": "section",
                "body": "# Inject 2 — Exposure window\n\n{{text}}",
                "data": {
                    "text": "10:00 — The vendor reports a 10-day exposure window. Session recordings and payroll data for two clients were accessed. A subcontractor used by our overflow team also had access to the platform.",
                },
            },
            {
                "name": "Decision B — Exposure & reassessment",

                "layout": "content",
                "body": "## Decision B — Exposure & reassessment\n\n{{#each questions}}\n1. {{this}}\n{{/each}}\n\n**Timebox:** {{timebox}}",
                "data": {
                    "questions": [
                        "Do you quarantine all work done through the platform during the window? (A.8.31)",
                        "How do you verify the payroll data was not altered, not just read? (A.8.15)",
                        "What do you require from the vendor before restoring service? (A.5.19, A.5.21)",
                        "Do you tell clients about the subcontractor — and does your contract require it? (A.5.20)",
                    ],
                    "timebox": "20 minutes",
                },
            },
            {
                "name": "ISO/IEC 27001 clause map",

                "layout": "content",
                "body": "## Aligning decisions to ISO/IEC 27001\n\n| Decision | ISO/IEC 27001:2022 control | ISO/IEC 27002:2022 guidance |\n|----------|----------------------------|-----------------------------|\n{{#each clause_map}}\n| {{decision}} | {{control}} | {{guidance}} |\n{{/each}}\n\n*ISO/IEC 27002:2022 is the code of practice that guides implementation of the Annex A controls referenced above.*",
                "data": {
                    "clause_map": [
                        {"decision": "Suspend the vendor platform", "control": "A.5.21 · ICT supply chain", "guidance": "Manage supply-chain security, verify updates (27002 §5.21)"},
                        {"decision": "Client notification", "control": "A.5.20 · Supplier agreements", "guidance": "Contractual notification & security terms (27002 §5.20)"},
                        {"decision": "Quarantine window work", "control": "A.8.31 · Separation of environments", "guidance": "Isolate affected client processing (27002 §8.31)"},
                        {"decision": "Preserve vendor evidence", "control": "A.5.28 · Evidence collection", "guidance": "Secure and chain-of-custody evidence (27002 §5.28)"},
                        {"decision": "Restore service", "control": "A.5.30 · ICT readiness", "guidance": "Continuity arrangements for key services (27002 §5.30)"},
                        {"decision": "Vendor reassessment", "control": "A.5.19 · Supplier relationships", "guidance": "Re-evaluate and re-approve the supplier (27002 §5.19)"},
                    ],
                },
            },
            {
                "name": "Hotwash",

                "layout": "section",
                "body": "# Hotwash\n\n{{text}}",
                "data": {
                    "text": "How dependent are we on that single platform? What would we do tomorrow if it was down for a week?",
                },
            },
            {
                "name": "After Action Executive Summary",

                "layout": "content",
                "body": "## After Action Executive Summary\n\n**Exercise:** {{exercise.name}}\n**Date:** {{exercise.date | default:\"—\"}}\n**Participants:** {{participants | default:\"—\"}}\n\n### Exercise highlights\n{{#each highlights}}\n- {{this}}\n{{/each}}\n\n### Lessons learned\n{{#each lessons}}\n- {{this}}\n{{/each}}",
                "data": {
                    "exercise": {"name": "Breach via Remote-Access Vendor", "date": ""},
                    "participants": "CISO, Client delivery, Procurement, Cloud operations, DPO",
                    "highlights": [
                        "The vendor platform was suspended before the payroll run was exposed further",
                        "Both affected clients were notified with the exposure window and scope",
                        "Subcontractor access was traced and included in the notification",
                    ],
                    "lessons": [
                        "The VDI platform is a single point of failure — a secondary access path is required",
                        "Vendor updates need integrity verification before deployment",
                        "Supplier agreements must cover subcontractor and breach-notification terms",
                    ],
                },
            },
            {
                "name": "After-action review",

                "layout": "content",
                "body": "## After-action review\n\n{{#each actions}}\n- **{{item}}** — owner: {{owner}}\n{{/each}}\n\n**Next step:** {{next_step}}",
                "data": {
                    "actions": [
                        {"item": "Re-assess the VDI vendor and subcontractor under A.5.19–A.5.21", "owner": "Procurement"},
                        {"item": "Define a secondary access path for agents (A.5.29, A.5.30)", "owner": "Cloud operations"},
                        {"item": "Add vendor compromise to the ISMS risk treatment plan", "owner": "CISO"},
                        {"item": "Review session-recording retention and access (A.8.15)", "owner": "InfoSec"},
                    ],
                    "next_step": "Supplier reassessment within 10 working days; findings into management review and the risk register.",
                },
            },
        ],
    },
    # ------------------------------------------------------------------ #
    # Deck 3 — Insider data theft by an agent                              #
    # ------------------------------------------------------------------ #
    {
        "name": "Table Top Exercise · Insider Data Theft by an Agent",

        "slides": [
            {
                "name": "Title",

                "layout": "title",
                "body": "# Table Top Exercise\n\n## {{scenario.title}}\n\n{{scenario.kicker}}",
                "data": {
                    "scenario": {
                        "title": "Insider Data Theft by an Agent",
                        "kicker": "Cyber Incident Tabletop · ISO/IEC 27001:2022 & ISO/IEC 27002:2022 · 90 minutes · Focus on people controls (A.6) & monitoring (A.8)",
                    },
                },
            },
            {
                "name": "Objectives & ground rules",

                "layout": "content",
                "body": "## {{objectives.title}}\n\n{{#each objectives.items}}\n- {{this}}\n{{/each}}\n\n**Ground rules:** {{ground_rules}}",
                "data": {
                    "objectives": {
                        "title": "Objectives & ground rules",
                        "items": [
                            "Practice containment when the threat is an insider with legitimate access",
                            "Verify the integrity of client data, not just the fact of the leak",
                            "Map access, screening and monitoring gaps to Annex A controls",
                            "Build a corrective action plan that survives contact with the workforce (A.6)",
                        ],
                    },
                    "ground_rules": "Stay in role. Presume innocence but protect client data. Every decision gets an Annex A control.",
                },
            },
            {
                "name": "Scenario background",

                "layout": "content",
                "body": "## Scenario background\n\n**Organisation:** {{company.profile}}\n\n**ISO/IEC 27001 scope:** {{iso_scope}}\n\n**Key systems:**\n{{#each systems}}\n- {{this}}\n{{/each}}\n\n**Setting:** {{setting}}",
                "data": {
                    "company": {

                        "profile": "ISO/IEC 27001-certified BPO providing payroll and HR administration to 12 corporate clients",
                    },
                    "iso_scope": "Payroll and HR administration services on behalf of client organisations",
                    "systems": [
                        "Client HR portals (client-issued credentials)",
                        "Payroll processing queue and PII data store",
                        "SIEM and identity/access management (IAM)",
                        "Data-leakage prevention (DLP) tools",
                        "HR system — recruitment, screening, leavers",
                    ],
                    "setting": "Friday 01:30. A SIEM alert fires: a bulk download from a client HR portal using a support agent's account — payroll PII for 1,200 employees of one client.",
                },
            },
            {
                "name": "Roles",

                "layout": "content",
                "body": "## Roles & responsibilities\n\n| Role | Owner | Key concerns |\n|------|-------|--------------|\n{{#each roles}}\n| {{role}} | {{owner}} | {{concern}} |\n{{/each}}",
                "data": {
                    "roles": [
                        {"role": "Corporate Security", "owner": "Security", "concern": "Information & privacy security (A.5.x, A.8.2)"},
                        {"role": "IT Server & System Team", "owner": "Infrastructure", "concern": "Servers, systems, recovery (A.8.13)"},
                        {"role": "IT Desktop Team", "owner": "End-user computing", "concern": "Endpoints, patching, user access (A.8.7, A.8.8)"},
                        {"role": "IT Network Team", "owner": "Networking", "concern": "Connectivity, segmentation, VPN (A.8.20, A.8.31)"},
                        {"role": "Compliance", "owner": "Legal & Compliance", "concern": "Legal & compliance concerns (A.5.20, A.5.34)"},
                        {"role": "Human Resources", "owner": "HR", "concern": "Employee policies & violations (A.6.1, A.6.3)"},
                        {"role": "Marketing", "owner": "Corporate communications", "concern": "Official corporate press statements (A.5.20)"},
                        {"role": "Executive Leadership", "owner": "C-suite", "concern": "Executive decision-making (A.5.24)"},
                    ],
                },
            },
            {
                "name": "Inject 1 — Bulk download",

                "layout": "section",
                "body": "# Inject 1 — Bulk download\n\n{{text}}",
                "data": {
                    "text": "01:30 Friday — SIEM flags a bulk download from a client HR portal using a support agent's account. The agent's role does not include payroll administration, and the download used a client-issued credential the agent was not supposed to hold.",
                },
            },
            {
                "name": "Decision A — Containment & notification",

                "layout": "content",
                "body": "## Decision A — Containment & notification\n\n{{#each questions}}\n1. {{this}}\n{{/each}}\n\n**Timebox:** {{timebox}}",
                "data": {
                    "questions": [
                        "What do you disable right now — the account, the client credential, the agent's sessions? (A.8.3)",
                        "What evidence do you preserve, and who may touch it? (A.8.15, A.5.28)",
                        "Do you contact the client before you know the full scope? What does the contract require? (A.5.20)",
                        "Is the agent still on site tonight? Do you change their physical access too? (A.6.5)",
                    ],
                    "timebox": "15 minutes",
                },
            },
            {
                "name": "Inject 2 — A ring, and an integrity question",

                "layout": "section",
                "body": "# Inject 2 — A ring, and an integrity question\n\n{{text}}",
                "data": {
                    "text": "Saturday — Forensics find a data-broker channel on the agent's personal cloud drive and patterns suggesting two more agents are involved. Two payroll files show modification timestamps after the download.",
                },
            },
            {
                "name": "Decision B — Scope & corrective action",

                "layout": "content",
                "body": "## Decision B — Scope & corrective action\n\n{{#each questions}}\n1. {{this}}\n{{/each}}\n\n**Timebox:** {{timebox}}",
                "data": {
                    "questions": [
                        "How wide do you cast the investigation — the ring, the shift, the client, all clients? (A.5.25)",
                        "How do you verify that processed payroll records are still accurate? (A.8.15)",
                        "What does this say about screening, access reviews and awareness? (A.6.1, A.6.3)",
                        "Should DLP have caught a bulk download — and why didn't it? (A.8.12, A.8.16)",
                    ],
                    "timebox": "20 minutes",
                },
            },
            {
                "name": "ISO/IEC 27001 clause map",

                "layout": "content",
                "body": "## Aligning decisions to ISO/IEC 27001\n\n| Decision | ISO/IEC 27001:2022 control | ISO/IEC 27002:2022 guidance |\n|----------|----------------------------|-----------------------------|\n{{#each clause_map}}\n| {{decision}} | {{control}} | {{guidance}} |\n{{/each}}\n\n*ISO/IEC 27002:2022 is the code of practice that guides implementation of the Annex A controls referenced above.*",
                "data": {
                    "clause_map": [
                        {"decision": "Revoke agent access", "control": "A.8.3 · Access restriction", "guidance": "Restrict access to need-to-know (27002 §8.3)"},
                        {"decision": "Preserve evidence", "control": "A.5.28 · Evidence collection", "guidance": "Chain of custody, forensic integrity (27002 §5.28)"},
                        {"decision": "Client notification", "control": "A.5.20 · Supplier agreements", "guidance": "Contractual breach-notification terms (27002 §5.20)"},
                        {"decision": "Investigate the ring", "control": "A.5.25 · Incident assessment", "guidance": "Assess and respond to incidents (27002 §5.25)"},
                        {"decision": "DLP & monitoring", "control": "A.8.12 / A.8.16 · Data leakage prevention & monitoring", "guidance": "Detect bulk egress; monitor activity (27002 §8.12, §8.16)"},
                        {"decision": "Screening & awareness", "control": "A.6.1 / A.6.3 · Screening & awareness", "guidance": "Screen candidates; train the workforce (27002 §6.1, §6.3)"},
                    ],
                },
            },
            {
                "name": "Hotwash",

                "layout": "section",
                "body": "# Hotwash\n\n{{text}}",
                "data": {
                    "text": "How fast could we identify every credential that agent held? Would we notice a slow, low-and-slow exfiltration next time?",
                },
            },
            {
                "name": "After Action Executive Summary",

                "layout": "content",
                "body": "## After Action Executive Summary\n\n**Exercise:** {{exercise.name}}\n**Date:** {{exercise.date | default:\"—\"}}\n**Participants:** {{participants | default:\"—\"}}\n\n### Exercise highlights\n{{#each highlights}}\n- {{this}}\n{{/each}}\n\n### Lessons learned\n{{#each lessons}}\n- {{this}}\n{{/each}}",
                "data": {
                    "exercise": {"name": "Insider Data Theft by an Agent", "date": ""},
                    "participants": "CISO, Client delivery, HR, DPO, IAM",
                    "highlights": [
                        "The agent's access was revoked within the hour, before the shift ended",
                        "Evidence was preserved with a forensic chain of custody",
                        "The affected client received a verified data-integrity statement",
                    ],
                    "lessons": [
                        "Client-issued credentials must be covered by access reviews, not just corporate accounts",
                        "DLP should have flagged a bulk download — gap confirmed and queued",
                        "Exit processes must revoke access on the exit date, not the following Monday",
                    ],
                },
            },
            {
                "name": "After-action review",

                "layout": "content",
                "body": "## After-action review\n\n{{#each actions}}\n- **{{item}}** — owner: {{owner}}\n{{/each}}\n\n**Next step:** {{next_step}}",
                "data": {
                    "actions": [
                        {"item": "Automate periodic access reviews for client-issued credentials (A.8.2, A.8.3)", "owner": "IAM"},
                        {"item": "Tune DLP for bulk downloads and personal-cloud egress (A.8.12)", "owner": "InfoSec"},
                        {"item": "Reinforce screening and awareness for PII handling (A.6.1, A.6.3)", "owner": "HR"},
                        {"item": "Notify the affected client with a verified data-integrity statement", "owner": "Client delivery"},
                    ],
                    "next_step": "Corrective action review in 30 days; lessons into the internal ISMS audit programme (A.5.35).",
                },
            },
        ],
    },
]


# ---------------------------------------------------------------------- #
# Interactive inject timelines for the three hand-written BPO decks.       #
# The generator decks (SCENARIO_DECKS) carry their own injects; these are #
# spliced in here, and the legacy "Inject 1 / Inject 2" section slides   #
# are replaced with timeline slides built by inject_slides().             #
# ---------------------------------------------------------------------- #
_BPO_INJECTS = {
    "Table Top Exercise · Ransomware at a BPO": [
        {"time": "09:05", "title": "Credentials captured",
         "detail": "A phishing email captured an agent's credentials. Encryption activity is detected on the claims-processing environment — nothing is down yet, but it is spreading."},
        {"time": "09:25", "title": "Spread to client share",
         "detail": "Encryption activity spreads to a client-shared drive and the contact-center platform begins to slow. Two clients have month-end claims batches in progress."},
        {"time": "09:45", "title": "Ransom demand & PII at risk",
         "detail": "Two clients' SLAs are now being missed and a month-end claims batch is stalled. The ransom note demands $400,000 in crypto; client PII is believed to be within the encrypted scope."},
    ],
    "Table Top Exercise · Breach via Remote-Access Vendor": [
        {"time": "07:15", "title": "Vendor update compromised",
         "detail": "The VDI vendor confirms its weekend update was compromised. Some agent sessions — including screen recordings — were accessed by the attacker."},
        {"time": "08:30", "title": "Other BPOs affected",
         "detail": "The vendor reports several other BPOs are affected by the same compromise. Two clients have payroll runs due Wednesday."},
        {"time": "10:00", "title": "Exposure window confirmed",
         "detail": "The vendor reports a 10-day exposure window. Session recordings and payroll data for two clients were accessed; a subcontractor also had access to the platform."},
    ],
    "Table Top Exercise · Insider Data Theft by an Agent": [
        {"time": "01:30", "title": "Bulk download flagged",
         "detail": "SIEM flags a bulk download from a client HR portal using a support agent's account. The role does not include payroll administration, and the credential was not supposed to be held."},
        {"time": "02:10", "title": "Exfiltration to personal cloud",
         "detail": "Monitoring confirms the downloaded payroll PII — 1,200 records — was uploaded to a personal cloud drive by the same agent."},
        {"time": "Sat 06:00", "title": "A ring, and an integrity question",
         "detail": "Forensics find a data-broker channel on the agent's personal cloud drive and patterns suggesting two more agents are involved. Two payroll files show modification timestamps after the download."},
    ],
}

_BPO_META = {
    "Table Top Exercise · Ransomware at a BPO": {
        "title": "Ransomware at a BPO", "diff": "ADVANCED", "cat": "INFORMATION TECHNOLOGY",
        "desc": "Mass encryption of a client-shared claims environment with a $400,000 ransom demand and client PII in scope."},
    "Table Top Exercise · Breach via Remote-Access Vendor": {
        "title": "Breach via Remote-Access Vendor", "diff": "ADVANCED", "cat": "INFORMATION TECHNOLOGY",
        "desc": "A trojanized update from the VDI vendor exposes session recordings and payroll data across a 10-day window."},
    "Table Top Exercise · Insider Data Theft by an Agent": {
        "title": "Insider Data Theft by an Agent", "diff": "ADVANCED", "cat": "INFORMATION TECHNOLOGY",
        "desc": "An agent with a client-issued credential bulk-downloads payroll PII, turning into a data-broker ring."},
}


def _enrich_aar(deck):
    """Add the summary, recommendations and CAPA register to a
    deck's After Action Executive Summary slide, synthesised from the deck's
    own slides. Scenario decks already carry these fields (built from their
    specs) — this fills the hand-written BPO decks and upgrades the template."""
    out = []
    for s in deck.get("slides") or []:
        if s.get("name", "").startswith("After Action Executive"):
            s = dict(s)
            d = dict(s.get("data") or {})
            s["body"] = AAR_BODY
            if not d.get("story"):
                d["story"] = deck_story(deck)
            actions = []
            for sl in deck.get("slides") or []:
                if sl.get("name", "") == "After-action review":
                    actions = (sl.get("data") or {}).get("actions") or []
                    break
            if not d.get("recommendations"):
                d["recommendations"] = recommendations_from_actions(actions)
            if not d.get("capa"):
                d["capa"] = capa_rows(actions)
            if not d.get("meta"):
                d["meta"] = dict(AAR_META_DEFAULT)
            if not d.get("executive_assessment"):
                d["executive_assessment"] = AAR_ASSESSMENT_DEFAULT
            if not d.get("score"):
                d["score"] = dict(AAR_SCORE_DEFAULT)
            if not d.get("capability"):
                d["capability"] = [dict(r) for r in AAR_CAPABILITY_DEFAULT]
            if not d.get("framework_alignment"):
                d["framework_alignment"] = [dict(r) for r in AAR_FRAMEWORK_ALIGNMENT]
            if not d.get("kpis"):
                d["kpis"] = [dict(r) for r in AAR_KPIS]
            if not d.get("decisions"):
                d["decisions"] = list(AAR_DECISIONS_REQUESTED)
            if not d.get("evidence"):
                d["evidence"] = list(AAR_EVIDENCE_PACK)
            if not d.get("roadmap"):
                d["roadmap"] = [dict(r) for r in AAR_ROADMAP]
            s["data"] = d
        out.append(s)
    deck = dict(deck)
    deck["slides"] = out
    return deck


def _normalize(deck):
    """Splice interactive injects + meta into the hand-written BPO decks."""
    injs = _BPO_INJECTS.get(deck["name"])
    if not injs:
        return deck
    deck = dict(deck)
    deck["injects"] = injs
    deck["meta"] = _BPO_META.get(deck["name"], {})
    new_slides, inserted = [], False
    for s in deck["slides"]:
        nm = s.get("name", "")
        if nm.startswith("Inject 1 ") or nm.startswith("Inject 2 "):
            if not inserted:
                new_slides.extend(inject_slides(injs))
                inserted = True
            continue
        new_slides.append(s)
    deck["slides"] = new_slides
    return deck


EXERCISE_DECKS = [_enrich_aar(_normalize(d)) for d in EXERCISE_DECKS + SCENARIO_DECKS]
