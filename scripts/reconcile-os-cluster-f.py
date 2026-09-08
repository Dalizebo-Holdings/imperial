#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REPORT = ROOT / "operating-systems/reconciliation/reports/CLUSTER_F.md"
STATUS = ROOT / "operating-systems/reconciliation/reports/STATUS.md"

# type, domain, owner, priority, phase, security, disposition, dependencies
META = {
"201": ("CORE","Data & Knowledge","Data Platform","P0","4","CRITICAL","KEEP","Integrations OS;Knowledge OS;Records OS"),
"202": ("SHARED_SERVICE","Data & Knowledge","AI Platform","P1","10","HIGH","KEEP","Data OS;Knowledge OS;RAG OS"),
"203": ("SHARED_SERVICE","AI & Intelligence","AI Platform","P1","10","HIGH","REFRAME","Vector-DB OS;Knowledge OS;Inference OS"),
"204": ("SHARED_SERVICE","AI & Intelligence","AI Platform","P1","10","CRITICAL","REFRAME","RAG OS;Reasoning OS;AI Gateway"),
"205": ("R&D","AI & Intelligence","AI Governance","R&D","18","CRITICAL","REFRAME","Data OS;Inference OS;Evidence OS"),
"206": ("PRODUCT","Developer Platform","Mobile Platform","P1","9","HIGH","REFRAME","Mobile-Engine OS;Identity OS;Interface OS"),
"207": ("PRODUCT","Developer Platform","Mobile Platform","P1","9","HIGH","REFRAME","Mobile-Engine OS;Identity OS;Interface OS"),
"208": ("SHARED_SERVICE","Developer Platform","Mobile Platform","P1","9","HIGH","KEEP","Android OS;iOS OS;Protocol OS"),
"209": ("R&D","Developer Platform","Platform Architecture","P3","17","HIGH","REFRAME","Protocol OS;Security OS;Network OS"),
"210": ("SHARED_SERVICE","Developer Platform","Design Platform","P0","5","HIGH","REFRAME","Design OS;Identity OS;Protocol OS"),
"211": ("AUTOMATION","Developer Platform","Product Governance","P2","9","HIGH","REFRAME","Interface OS;Sentiment OS;Experimentation"),
"212": ("CORE","Payments & Billing","Payments Platform","P0","5","CRITICAL","REFRAME","Payment-Gateway OS;Medici-Ledger OS;Compliance OS"),
"213": ("PRODUCT","Commerce & Retail","Commerce Platform","P0","6","CRITICAL","REFRAME","Payments OS;Shopping OS;Pricing OS"),
"214": ("CORE","Payments & Billing","Billing Platform","P0","5","CRITICAL","REFRAME","Payments OS;Pricing OS;Medici-Ledger OS"),
"215": ("PRODUCT","Commerce & Retail","Commerce Platform","P1","6","HIGH","REFRAME","Billing OS;Pricing data;Compliance OS"),
"216": ("PRODUCT","Data & Knowledge","Learning Platform","P3","17","HIGH","REFRAME","Learning OS;Talent-Forge OS;Identity OS"),
"217": ("POLICY","Data & Knowledge","Learning Platform","P3","17","HIGH","REFRAME","University OS;Learning OS;Knowledge OS"),
"218": ("PRODUCT","Data & Knowledge","Learning Platform","P2","17","HIGH","KEEP","Pedagogy OS;Knowledge OS;Identity OS"),
"219": ("PRODUCT","Data & Knowledge","Talent Platform","P2","17","HIGH","REFRAME","Learning OS;University OS;Projects"),
"220": ("POLICY","Data & Knowledge","Talent Platform","P2","17","CRITICAL","REFRAME","Talent-Forge OS;Evidence OS;Ethics OS"),
"221": ("POLICY","Governance & Audit","Ethics Governance","P0","3","CRITICAL","KEEP","Pillars OS;Governance OS;Compliance OS"),
"222": ("POLICY","Governance & Audit","Ethics Governance","P3","17","HIGH","REFRAME","Ethics OS;Reasoning OS;Knowledge OS"),
"223": ("RETIRED_REFRAMED","Data & Knowledge","Cultural Governance","P3","17","HIGH","REFRAME","Ethics OS;Knowledge OS;Media OS"),
"224": ("RETIRED_REFRAMED","Marketing & Customer","Brand Governance","P3","17","HIGH","REFRAME","Narrative OS;Media OS;Ethics OS"),
"225": ("RETIRED_REFRAMED","Marketing & Customer","Brand Governance","P3","17","HIGH","REFRAME","Aesthetic OS;Art OS;Ethics OS"),
"226": ("SHARED_SERVICE","Governance & Audit","Corporate Strategy","P3","17","HIGH","REFRAME","Jurisdiction OS;Regional-Trade OS;Compliance OS"),
"227": ("DATA_PRODUCT","Data & Knowledge","Strategy","P3","17","HIGH","REFRAME","Geospatial OS;Risk OS;Information-Vacuum OS"),
"228": ("DATA_PRODUCT","Finance & Capital","Treasury Governance","P3","15","CRITICAL","REFRAME","Risk OS;Fiat-Hedge OS;Portfolio OS"),
"229": ("DATA_PRODUCT","Data & Knowledge","International Strategy","P3","17","HIGH","REFRAME","Geopolitics OS;Supply-Chain OS;Compliance OS"),
"230": ("DATA_PRODUCT","Data & Knowledge","International Strategy","P3","17","HIGH","REFRAME","Geopolitics OS;Wall Street OS;Compliance OS"),
"231": ("DATA_PRODUCT","Legal & Compliance","Regional Strategy","P1","8","CRITICAL","REFRAME","Compliance OS;Property OS;Regional-Trade OS"),
"232": ("DATA_PRODUCT","Legal & Compliance","International Strategy","P3","17","HIGH","REFRAME","Geopolitics OS;Jurisdiction OS;Compliance OS"),
"233": ("DATA_PRODUCT","Legal & Compliance","International Strategy","P3","17","HIGH","REFRAME","Geopolitics OS;Jurisdiction OS;Compliance OS"),
"234": ("DATA_PRODUCT","Data & Knowledge","International Strategy","P3","17","HIGH","REFRAME","Geopolitics OS;Alliance OS;Compliance OS"),
"235": ("R&D","Finance & Capital","Treasury Governance","R&D","18","CRITICAL","REFRAME","Portfolio OS;Risk OS;Compliance OS"),
"236": ("DATA_PRODUCT","Finance & Capital","Capital Markets","P3","15","HIGH","REFRAME","Market data integrations;Risk OS;Portfolio OS"),
"237": ("DATA_PRODUCT","Finance & Capital","Capital Markets","P2","15","HIGH","REFRAME","Market data integrations;Risk OS;Portfolio OS"),
"238": ("DATA_PRODUCT","Finance & Capital","Capital Markets","P2","15","HIGH","REFRAME","Market data integrations;Risk OS;Portfolio OS"),
"239": ("R&D","Finance & Capital","Capital Markets","R&D","18","CRITICAL","REFRAME","Trading OS;Portfolio OS;Risk OS;Compliance OS"),
"240": ("DATA_PRODUCT","Finance & Capital","Capital Markets","P3","15","HIGH","REFRAME","Wall Street OS;Knowledge OS"),
"241": ("R&D","Finance & Capital","Capital Markets","R&D","18","CRITICAL","REFRAME","Market data integrations;Risk OS;Compliance OS;Audit-Vigil OS"),
"242": ("PRODUCT","Finance & Capital","Treasury Governance","P2","12","CRITICAL","KEEP","Medici-Ledger OS;Risk OS;Records OS"),
"243": ("DATA_PRODUCT","Finance & Capital","Treasury Governance","P2","12","HIGH","REFRAME","Portfolio OS;Risk OS;Capital-Allocation OS"),
"244": ("CORE","Governance & Audit","Risk Governance","P1","8","CRITICAL","KEEP","Monte-Carlo OS;Monitoring OS;Decision-Matrix OS"),
"245": ("DATA_PRODUCT","AI & Intelligence","Risk Governance","P2","10","HIGH","KEEP","Risk OS;Statistics OS;Mathematics OS"),
"246": ("PRODUCT","Marketing & Customer","Media Platform","P2","9","HIGH","REFRAME","Media OS;Engagement OS;Sentiment OS"),
"247": ("PRODUCT","Marketing & Customer","Community Platform","P2","9","HIGH","REFRAME","Membership OS;CRM;Media OS"),
"248": ("DATA_PRODUCT","Marketing & Customer","Product Governance","P2","9","HIGH","REFRAME","Community OS;Analytics;Experimentation"),
"249": ("PRODUCT","Marketing & Customer","Partner Marketing","P2","9","HIGH","REFRAME","CRM;Contract OS;Media OS"),
"250": ("DATA_PRODUCT","Data & Knowledge","Strategy","P2","15","CRITICAL","REFRAME","Alliance OS;Geospatial OS;Knowledge OS"),
"251": ("PRODUCT","Legal & Compliance","Public-Sector Governance","P2","14","CRITICAL","REFRAME","Bidding OS;Contracts OS;Compliance OS"),
"252": ("DATA_PRODUCT","Legal & Compliance","Public-Sector Governance","P2","14","CRITICAL","REFRAME","Tendering System OS;Pricing OS;Risk OS"),
"253": ("SHARED_SERVICE","Governance & Audit","Compliance Governance","P1","8","CRITICAL","KEEP","Compliance OS;Audit-Vigil OS;Evidence OS"),
"254": ("RETIRED_REFRAMED","Legal & Compliance","Public-Sector Governance","P3","14","CRITICAL","REFRAME","Tendering System OS;Contracts OS;Compliance OS"),
"255": ("DATA_PRODUCT","Finance & Capital","Corporate Development","P3","15","CRITICAL","REFRAME","Capital-Allocation OS;Contract OS;Risk OS;Compliance OS"),
"256": ("SHARED_SERVICE","Legal & Compliance","Legal Governance","P1","8","CRITICAL","REFRAME","Contract OS;Records OS;Evidence OS"),
"257": ("R&D","Legal & Compliance","Legal Governance","R&D","18","CRITICAL","REFRAME","Contracts OS;Payments OS;Compliance OS"),
"258": ("INTEGRATION","Payments & Billing","Payments Platform","P2","12","CRITICAL","REFRAME","Payments OS;Contracts OS;Compliance OS"),
"259": ("RETIRED_REFRAMED","Legal & Compliance","Legal Governance","P2","10","CRITICAL","REFRAME","Conflict-Resolution OS;Arbitration OS;Evidence OS"),
"260": ("CORE","Developer Platform","Platform Engineering","P0","4","CRITICAL","REFRAME","Identity OS;Access-Control OS;Audit-Vigil OS;Pillars OS"),
"261": ("SHARED_SERVICE","Data & Knowledge","Data Platform","P1","10","HIGH","KEEP","Data OS;Mathematics OS;Evidence OS"),
"262": ("SHARED_SERVICE","Data & Knowledge","Data Platform","P2","10","HIGH","REFRAME","Statistics OS;Logic-Chain OS"),
"263": ("DATA_PRODUCT","Data & Knowledge","Data Platform","P3","17","HIGH","REFRAME","Mathematics OS;Statistics OS"),
"264": ("DATA_PRODUCT","AI & Intelligence","Strategy","P3","17","HIGH","REFRAME","Game-Theory OS;Reasoning OS;Decision-Matrix OS"),
"265": ("SHARED_SERVICE","AI & Intelligence","AI Platform","P2","10","HIGH","REFRAME","Synthesis OS;Decision-Matrix OS;Reasoning OS"),
"266": ("POLICY","Governance & Audit","Executive Governance","P2","10","CRITICAL","REFRAME","Solutions OS;Ethics OS;Risk OS;Pillars OS"),
"267": ("RETIRED_REFRAMED","Data & Knowledge","Cultural Governance","P3","17","HIGH","REFRAME","Theology OS;Knowledge OS;Ethics OS"),
"268": ("PRODUCT","Marketing & Customer","Events Platform","P2","9","HIGH","REFRAME","Community OS;Membership OS;Payments OS"),
"269": ("CORE","Data & Knowledge","Records Governance","P0","4","CRITICAL","KEEP","Archive OS;Evidence OS;Medici-Ledger OS"),
}

SPECIAL = {
"203": ("Provide retrieval-augmented generation using authorized knowledge, citations, provenance, access controls, evaluation, and bounded context assembly.",
        "RAG supports governed Dalizebo assistants rather than a personality-specific authority node."),
"205": ("Manage controlled model adaptation through curated datasets, evaluation, versioning, approval, rollback, safety testing, and documented training provenance.",
        "Unattended continuous retraining of production decision systems is prohibited."),
"209": ("Research resilient web delivery and optional peer-to-peer or decentralized distribution where it improves availability, portability, privacy, or offline operation.",
        "Decentralization must remain lawful, observable, secure, and compatible with governance requirements."),
"211": ("Support reversible, measured interface personalization and feature adaptation using consented signals, explicit experiments, accessibility, and user controls.",
        "Real-time UI changes must not manipulate users or deploy unreviewed hot patches."),
"212": ("Manage payment intents, methods, authorization, capture, refunds, settlement state, reconciliation, ledger events, and approved payment instruments.",
        "DZC is optional and only available if separately authorized and compliant."),
"213": ("Provide transparent checkout flows covering cart validation, pricing, taxes, shipping, payment, confirmation, recovery, accessibility, and fraud controls.",
        "Checkout optimization must not use dark patterns or deceptive urgency."),
"214": ("Manage invoices, subscriptions, usage, credits, taxes, receivables, revenue events, statements, collections, and authorized internal allocations.",
        "Dividend or owner distributions require separate corporate, accounting, tax, and approval processes."),
"215": ("Manage price lists, currencies, promotions, cost inputs, margins, customer-visible adjustments, experiments, approvals, and effective dates.",
        "Dynamic pricing must be transparent, lawful, auditable, and must not use protected traits or exploit vulnerable users."),
"216": ("Provide structured internal and external learning programs, applications, assessments, cohorts, credentials, mentorship, and transparent talent pathways.",
        "Talent selection must use documented, relevant, fair criteria rather than elite-status gatekeeping."),
"217": ("Define evidence-based curriculum design, learning objectives, assessment methods, feedback, accessibility, instructional quality, and content review.",
        "Pedagogy must not enforce a proprietary ideological truth."),
"219": ("Support skills development, mentoring, project experience, competency evidence, career pathways, and role readiness for people participating in Dalizebo programs.",
        "People are participants and professionals, not strategic assets to be engineered."),
"220": ("Govern high-responsibility role assessment using job-relevant criteria, structured evaluation, documented scoring, appeal paths, privacy, and human review.",
        "High-stakes testing must be fair, explainable, and proportionate."),
"223": ("Support respectful study and documentation of theology, ritual, history, and cultural context where relevant to education, research, or creative work.",
        "Religious belief or ritual must not be exploited as a mechanism for brand manipulation."),
"224": ("Use archetypes and storytelling as transparent creative devices for brand and media work while keeping factual claims distinguishable from fiction or symbolism.",
        "Mythos OS cannot manufacture deceptive authority or identity."),
"225": ("Manage optional symbolic, historical, esoteric, and aesthetic references for creative work with cultural respect and clear artistic framing.",
        "Deep-psychological cues must not be used for covert influence or behavior control."),
"226": ("Plan international expansion through market research, localization, lawful entity structures, partnerships, regulatory readiness, infrastructure, and staged investment.",
        "Blitzkrieg expansion is replaced by lawful, paced, evidence-based international growth."),
"227": ("Provide geopolitical, regulatory, economic, infrastructure, trade, and country-risk analysis from lawful public, licensed, or authorized sources.",
        "Geopolitical analysis supports risk management rather than dominance."),
"228": ("Analyze macroeconomic, currency, inflation, rates, commodity, and liquidity scenarios to inform lawful treasury diversification and hedging decisions.",
        "Macro analysis must not become unbounded speculative betting."),
"231": ("Maintain South African regulatory, corporate, tax, property, infrastructure, procurement, market, and operating information from authoritative or authorized sources.",
        "Regulatory and land-title dominance is replaced with lawful local operating intelligence."),
"235": ("Research a governed long-term investment vehicle or treasury structure subject to legal form, licensing, mandate, custody, valuation, reporting, tax, and oversight requirements.",
        "An Imperial Fund is not established automatically and must meet all applicable financial-services requirements."),
"239": ("Research alternative and absolute-return investment strategies under explicit mandates, risk limits, independent valuation, compliance, custody, and governance.",
        "High-risk asymmetric bets cannot execute outside approved regulated investment structures."),
"241": ("Research or integrate authorized order-management and execution capabilities through regulated brokers with pre-trade controls, limits, monitoring, reconciliation, and kill switches.",
        "No unbounded autonomous trading, market manipulation, front-running, or misuse of confidential information is permitted."),
"246": ("Manage social publishing, scheduling, moderation, listening, analytics, community responses, rights, and campaign measurement across approved channels.",
        "Mind-virus tracking is removed; social analytics must respect privacy and platform rules."),
"248": ("Measure useful engagement, retention, satisfaction, task completion, community health, and content performance while preserving user autonomy and wellbeing.",
        "Attention optimization must not use addictive, compulsive, or deceptive mechanics."),
"249": ("Manage transparent creator, ambassador, affiliate, expert, and influencer partnerships including contracts, disclosures, content, compensation, performance, and compliance.",
        "Influencers are disclosed partners rather than covert proxy nodes."),
"250": ("Maintain lawful relationship graphs for organizations, partners, public institutions, markets, suppliers, infrastructure, and other authorized entities using provenance and access controls.",
        "Network mapping must not become covert personal surveillance or unauthorized profiling."),
"251": ("Manage tender discovery, eligibility, requirements, deadlines, evidence, approvals, submissions, clarifications, awards, and audit trails for lawful procurement.",
        "Tendering OS cannot automate bribery, collusion, false claims, favoritism, or guaranteed winning."),
"252": ("Support bid costing and pricing with documented assumptions, scope, margin, risk, capacity, competition-law controls, approvals, and auditability.",
        "Algorithmic bid support must not facilitate bid rigging, collusion, predatory pricing, or misrepresentation."),
"254": ("Manage lawful public-sector opportunities, procurement participation, partnerships, service delivery, reporting, stakeholder obligations, and contract performance.",
        "State infrastructure capture, corruption, coercion, favoritism, or misuse of public resources is prohibited."),
"255": ("Manage corporate-development pipelines for lawful partnerships, investments, mergers, or acquisitions using valuation, due diligence, financing, approvals, competition-law review, and integration planning.",
        "SME acquisition must be consensual, lawful, financially sound, and non-coercive."),
"257": ("Research machine-executable agreement clauses for narrow deterministic obligations with explicit legal text, auditability, pause mechanisms, dispute paths, and human override.",
        "Code cannot replace applicable law, consent, professional review, or required contractual formalities."),
"258": ("Integrate approved escrow or safeguarded-value providers and manage milestone conditions, authorization, release, refund, reconciliation, evidence, and dispute state.",
        "Dalizebo must not hold regulated client money without the required legal and licensing structure."),
"259": ("Manage commercial disputes through issue intake, evidence, negotiation, mediation, arbitration, court workflows, remedies, settlement, and outcome tracking.",
        "Commercial sabotage, retaliation, destruction, or interference with counterparties is prohibited."),
"260": ("Provide an authenticated administrative CLI for authorized platform operations with scoped commands, policy checks, confirmations, audit logs, safe defaults, and rollback where feasible.",
        "Terminal OS is not an unrestricted root bypass; least privilege and governance remain mandatory."),
"266": ("Favor practical, testable, reversible actions when evidence supports them while preserving legal, ethical, safety, financial, customer, and governance constraints.",
        "Short-term cash yield never overrides constitutional, legal, safety, or fiduciary obligations."),
"267": ("Support respectful documentation and study of religions, rituals, institutions, history, beliefs, and cultural context where relevant to education or research.",
        "Religion must not be instrumentalized for manipulation, coercion, brand worship, or political control."),
"268": ("Manage conferences, summits, workshops, launches, registrations, venues, agendas, speakers, tickets, communications, attendance, sponsorships, and post-event records.",
        "Token or credit distributions are permitted only when lawful, transparent, approved, and operationally supported."),
}

POLICIES = {
"Data & Knowledge": "Provenance;authorization;privacy;retention;classification;reproducibility",
"AI & Intelligence": "Model governance;evaluation;provenance;human accountability;safety;privacy",
"Developer Platform": "Security;versioning;least privilege;accessibility;change control;observability",
"Payments & Billing": "Authorization;reconciliation;fraud controls;consumer protection;financial regulation",
"Commerce & Retail": "Consumer protection;pricing transparency;fair UX;privacy;payments security",
"Governance & Audit": "Constitutional policy;audit;evidence;accountability;exceptions;legal compliance",
"Marketing & Customer": "Truthful communication;consent;privacy;anti-dark-patterns;customer autonomy",
"Finance & Capital": "Risk limits;market conduct;authorization;valuation;custody;financial compliance",
"Legal & Compliance": "Lawful process;professional review;anti-corruption;competition law;evidence;authorization",
}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid OS review ledger")

expected = {f"{i:03d}" for i in range(201, 270)}
found = set()

for row in rows:
    pid = row["canonical_id"]
    if pid not in META:
        continue

    (
        impl_type,
        domain,
        owner,
        priority,
        phase,
        security,
        disposition,
        dependencies,
    ) = META[pid]

    if pid in SPECIAL:
        canonical, notes = SPECIAL[pid]
    else:
        canonical = (
            "Implement " + row["name"] +
            " as a governed Dalizebo capability using authorized data, "
            "documented controls, auditable decisions, and applicable platform policies."
        )
        notes = (
            "Original source terminology is preserved historically; "
            "canonical implementation is limited to lawful, safe, transparent, "
            "and reviewable operation."
        )

    row["review_status"] = "CLASSIFIED"
    row["domain"] = domain
    row["owner"] = owner
    row["priority"] = priority
    row["implementation_type"] = impl_type
    row["dependencies"] = dependencies
    row["inputs"] = (
        "Authorized platform, market, customer, content, legal, financial, "
        "operational, research, configuration, and governance data"
    )
    row["outputs"] = (
        "Governed records, analyses, recommendations, transactions, "
        "workflows, interfaces, alerts, reports, or authorized actions"
    )
    row["policies"] = POLICIES[domain]
    row["events"] = "os." + pid + ".evaluated"
    row["apis"] = "Internal versioned API; external exposure only where explicitly approved"
    row["data_requirements"] = (
        "Tenant-scoped authorized data; provenance; retention; classification; "
        "privacy and audit metadata"
    )
    row["security_level"] = security
    row["roadmap_phase"] = phase
    row["disposition"] = disposition
    row["canonical_interpretation"] = canonical
    row["decision_notes"] = notes

    found.add(pid)

missing = expected - found
if missing:
    raise SystemExit(
        "ERROR: missing Cluster F OS entries: " + ", ".join(sorted(missing))
    )

tmp = REVIEW.with_suffix(".tmp")
with tmp.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
tmp.replace(REVIEW)

cluster = [r for r in rows if r["canonical_id"] in expected]
types = Counter(r["implementation_type"] for r in cluster)
dispositions = Counter(r["disposition"] for r in cluster)

lines = [
    "# Operating Systems Cluster F Reconciliation",
    "",
    "## Scope",
    "",
    "OS-201 through OS-269 — Advanced, Meta & Terminal.",
    "",
    "Original source statements remain unchanged.",
    "",
    "Unsafe, deceptive, manipulative, coercive, unlawful, privacy-invasive, "
    "financially unbounded, or governance-bypassing concepts are retired, "
    "research-bounded, or canonically reframed.",
    "",
    "## Implementation Classification",
    "",
]

for key in sorted(types):
    lines.append("- " + key + ": " + str(types[key]))

lines += ["", "## Canonical Disposition", ""]

for key in sorted(dispositions):
    lines.append("- " + key + ": " + str(dispositions[key]))

lines.extend(["", "## Decisions", ""])

for row in cluster:
    lines.extend([
        "### OS-" + row["canonical_id"] + " — " + row["name"],
        "",
        "**Type:** " + row["implementation_type"],
        "",
        "**Disposition:** " + row["disposition"],
        "",
        "**Domain:** " + row["domain"],
        "",
        "**Owner:** " + row["owner"],
        "",
        "**Priority:** " + row["priority"],
        "",
        "**Security:** " + row["security_level"],
        "",
        "**Original Source Statement**",
        "",
        "> " + row["source_statement"],
        "",
        "**Canonical Interpretation**",
        "",
        row["canonical_interpretation"],
        "",
        "**Decision**",
        "",
        row["decision_notes"],
        "",
        "---",
        "",
    ])

REPORT.write_text("\n".join(lines), encoding="utf-8")

classified = sum(
    1 for r in rows
    if r["canonical_id"] and r["review_status"] == "CLASSIFIED"
)

STATUS.write_text(
"""# Phase 2 Operating Systems Status

## Canonical ID Space

OS-001 → OS-269

## Raw Source Entries Preserved

279

## Overflow Reconciliation

10 / 10 reconciled

## Canonical Classification

%d / 269 complete

## Current Stage

Phase 2 complete.

## Completed Canonical Range

OS-001 → OS-269

## Catalogue Status

CANONICALLY CLASSIFIED

## Next Phase

Phase 3 — Algorithm OS + Loop OS + Integrations OS.

## Governing Rule

Source statements remain preserved.

Unsafe or unlawful source concepts remain retired, research-bounded,
or canonically reframed.

Canonical implementation decisions are recorded separately from source history.
""" % classified,
encoding="utf-8",
)

print("OK: OS Cluster F 201-269 classified.")
print("Canonical classification: %d/269" % classified)

for key in sorted(types):
    print("%s: %d" % (key, types[key]))

if classified != 269:
    raise SystemExit(
        "ERROR: expected 269 classified canonical OS entries, found %d" % classified
    )

print("STATUS: PHASE 2 CATALOGUE CLASSIFIED")
