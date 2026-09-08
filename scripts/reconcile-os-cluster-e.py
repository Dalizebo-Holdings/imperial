#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REPORT = ROOT / "operating-systems/reconciliation/reports/CLUSTER_E.md"
STATUS = ROOT / "operating-systems/reconciliation/reports/STATUS.md"

# type, domain, owner, priority, phase, security,
# disposition, dependencies, canonical, notes

D = {

"151": ("DATA_PRODUCT","Data & Knowledge","Wellness Governance","P3","17","CRITICAL","REFRAME",
"Identity OS;Records OS;Privacy Governance",
"Support consent-based personal wellness records, trends, user-entered observations, activity information, and optional integrations without replacing qualified healthcare.",
"Health OS must not independently diagnose, prescribe, or make high-stakes medical decisions."),

"152": ("R&D","Frontier R&D","Wellness Governance","R&D","18","CRITICAL","REFRAME",
"Health OS;Privacy Governance;Evidence OS",
"Research evidence-based circadian, wellness, biological and optionally consented genetic-data applications with strict privacy, professional oversight, and scientific validation.",
"Genetic optimization or biological intervention is not an autonomous platform function."),

"153": ("CORE","Identity & Security","Identity Platform","P1","4","CRITICAL","REFRAME",
"Identity OS;Access-Control OS;Encryption OS",
"Support privacy-preserving biometric authentication where lawful and justified, using secure templates, consent, strong encryption, anti-spoofing, revocation, and non-biometric alternatives.",
"Neural identification is not required; biometrics must remain optional where practical and proportionate."),

"154": ("RETIRED_REFRAMED","Data & Knowledge","Wellness Governance","P3","17","CRITICAL","REFRAME",
"Health OS;Evidence OS",
"Provide neutral educational information and tracking for user-selected wellness practices without recommending unapproved cognitive-enhancement substances or autonomous dosing.",
"Nootropic optimization is replaced with evidence-based wellness education and professional-review boundaries."),

"155": ("PRODUCT","Automation & Workflow","Productivity Platform","P2","9","MEDIUM","REFRAME",
"Focus OS;Circadian OS",
"Help users identify productive work periods using calendars, self-reported preferences, task history, focus sessions, and workload patterns.",
"Peak performance becomes user-controlled productivity support rather than claims about alpha states."),

"156": ("DATA_PRODUCT","Data & Knowledge","Wellness Governance","P2","9","HIGH","REFRAME",
"Sleep OS;Focus OS;Automation",
"Support user-controlled scheduling, lighting preferences, work timing, reminders, and routine analysis informed by ordinary circadian principles.",
"Circadian support must avoid unsupported medical claims."),

"157": ("DATA_PRODUCT","Data & Knowledge","Wellness Governance","P2","9","HIGH","REFRAME",
"Health OS;Circadian OS",
"Track user-provided or authorized sleep data and surface descriptive trends, routines, reminders, and general sleep-hygiene information.",
"Sleep OS does not diagnose sleep disorders or guarantee REM optimization."),

"158": ("DATA_PRODUCT","Data & Knowledge","Wellness Governance","P2","9","HIGH","REFRAME",
"Health OS;Records OS",
"Support user-controlled food logging, preferences, meal planning, general nutritional information, and optional authorized wellness integrations.",
"Nutrition functionality avoids autonomous clinical diet prescription."),

"159": ("DATA_PRODUCT","Data & Knowledge","Wellness Governance","P2","9","HIGH","REFRAME",
"Health OS;Records OS",
"Support activity logging, workout planning, progress tracking, reminders, and general fitness information under user control.",
"Exercise OS provides wellness tooling rather than medical clearance or clinical rehabilitation."),

"160": ("R&D","Frontier R&D","Wellness Governance","R&D","18","CRITICAL","REFRAME",
"Health OS;Biology OS;Evidence OS",
"Research long-horizon healthy-living, preventive-wellness, activity, sleep, nutrition and scientifically validated longevity information.",
"Longevity OS must not promise biological preservation or unsupported life-extension outcomes."),

"161": ("DATA_PRODUCT","Data & Knowledge","Wellness Governance","P2","9","CRITICAL","REFRAME",
"Health OS;Resilience OS;Privacy Governance",
"Provide private user-controlled wellbeing check-ins, journaling, coping resources, routine support, and pathways to qualified professional or emergency support when appropriate.",
"Mental-Health OS is supportive tooling and not autonomous diagnosis, therapy, crisis adjudication, or treatment."),

"162": ("DATA_PRODUCT","Data & Knowledge","Wellness Governance","P2","9","HIGH","REFRAME",
"Mental-Health OS;Disaster-Recovery OS",
"Support personal and organizational resilience through preparedness checklists, reflection, workload management, recovery planning, training, and wellbeing resources.",
"Psychological black-swan auditing becomes voluntary resilience and preparedness support."),

"163": ("DATA_PRODUCT","Data & Knowledge","Learning Governance","P3","17","MEDIUM","REFRAME",
"Resilience OS;Knowledge OS",
"Provide optional learning material and reflection exercises based on Stoic philosophy, critical thinking, emotional regulation concepts, and decision discipline.",
"Stoicism remains educational rather than a mandated psychological operating model."),

"164": ("DATA_PRODUCT","Data & Knowledge","Wellness Governance","P3","17","MEDIUM","REFRAME",
"Focus OS;Health OS",
"Provide optional meditation timers, guided exercises, reminders, journaling, and general mindfulness resources.",
"Meditation OS makes no unlimited-IQ or medical-performance claims."),

"165": ("PRODUCT","Automation & Workflow","Productivity Platform","P1","9","MEDIUM","KEEP",
"Kiro-OS;Notification systems;Peak-Flow OS",
"Provide user-controlled focus modes, notification suppression, session timers, priority queues, interruption controls, and distraction management.",
"Focus controls remain reversible and user-configurable."),

"166": ("SHARED_SERVICE","Data & Knowledge","Localization Platform","P1","9","HIGH","REFRAME",
"Translation OS;Semantic OS",
"Manage platform terminology, locale rules, language resources, style guidance, content standards, and multilingual consistency.",
"Language standards support clarity and localization rather than centralized ideological control."),

"167": ("SHARED_SERVICE","Data & Knowledge","Localization Platform","P2","9","HIGH","KEEP",
"Language OS;Translation OS",
"Provide Sepedi terminology, localization resources, translation memory, interface language support, documentation standards, and regional communication tooling.",
"Sepedi OS supports authentic local-language accessibility and operations."),

"168": ("SHARED_SERVICE","AI & Intelligence","Localization Platform","P1","10","HIGH","REFRAME",
"Language OS;Knowledge OS;AI Gateway",
"Provide governed machine-assisted translation and localization with terminology control, human review, confidence indicators, and regional language support.",
"Localized skins become transparent multilingual product localization."),

"169": ("RETIRED_REFRAMED","Data & Knowledge","Localization Platform","P3","9","HIGH","REFRAME",
"Language OS;Sepedi OS;Access-Control OS",
"Maintain internal glossaries, controlled vocabulary, technical terminology, and role-appropriate documentation without intentionally obscuring unlawful activity or misleading external audiences.",
"Using dialect to hide intent is retired."),

"170": ("DATA_PRODUCT","Marketing & Customer","Marketing Governance","P2","9","HIGH","REFRAME",
"Language OS;Marketing OS;Search Analytics",
"Analyze lawful search, content and social-language trends for relevance, discoverability, customer intent, localization and content planning.",
"Keyword dominance becomes ethical semantic and search intelligence."),

"171": ("RETIRED_REFRAMED","Marketing & Customer","Product Governance","P3","9","CRITICAL","REFRAME",
"Sentiment OS;Marketing OS;Experimentation",
"Use transparent behavioral research, consent-aware experimentation and user research to improve products while preserving autonomy and avoiding deception or coercion.",
"Engineering social outcomes through manipulative techniques is prohibited."),

"172": ("RETIRED_REFRAMED","Marketing & Customer","Product Governance","P2","9","HIGH","REFRAME",
"Marketing OS;Design OS;Experimentation",
"Support clear persuasive communication and legitimate choice architecture while requiring truthful claims, transparency, accessibility, user autonomy and anti-dark-pattern controls.",
"Covert cognitive nudging designed to override user interests is prohibited."),

"173": ("SHARED_SERVICE","Data & Knowledge","Communications Governance","P2","10","HIGH","REFRAME",
"Logic-Chain OS;Reasoning OS;Evidence OS",
"Help draft and evaluate clear arguments using evidence, logical structure, source verification, counterarguments and respectful communication.",
"Rhetoric OS supports defensible communication rather than deceptive persuasion."),

"174": ("SHARED_SERVICE","Marketing & Customer","Partner Governance","P2","17","HIGH","REFRAME",
"Alliance OS;Contract OS;CRM",
"Manage stakeholder and partner relationships, communications, agreements, commitments, cultural considerations, escalation paths and relationship history.",
"Proxy relationships become transparent governed partnerships."),

"175": ("SHARED_SERVICE","Legal & Compliance","Legal Governance","P2","10","HIGH","REFRAME",
"Contract OS;Decision-Matrix OS;Evidence OS",
"Support negotiation preparation, options, constraints, concessions, objectives, documented positions and agreement tracking under authorized human decision-making.",
"Status signaling becomes transparent negotiation strategy."),

"176": ("SHARED_SERVICE","Legal & Compliance","Partner Governance","P1","9","HIGH","KEEP",
"Contract OS;Negotiation OS;Evidence OS",
"Manage mediation, escalation, issue tracking, documented agreements, remedies, action items and structured partner-dispute resolution.",
"Conflict resolution prioritizes proportional and documented business resolution."),

"177": ("SHARED_SERVICE","Legal & Compliance","Legal Governance","P2","10","CRITICAL","REFRAME",
"Conflict-Resolution OS;Contract OS;Evidence OS",
"Manage arbitration cases, evidence, deadlines, submissions, tribunal information, awards, obligations and enforcement records.",
"The platform does not manufacture binding verdicts outside a valid arbitration process."),

"178": ("SHARED_SERVICE","Legal & Compliance","Legal Governance","P2","10","CRITICAL","REFRAME",
"Evidence OS;Contract OS;Records OS",
"Manage litigation matters, deadlines, documents, counsel, filings, evidence, decisions, costs, risks and authorized case workflows.",
"Court OS becomes litigation case management rather than offensive lawfare."),

"179": ("RETIRED_REFRAMED","Legal & Compliance","Legal Governance","P3","10","CRITICAL","REFRAME",
"Court OS;Contract OS;Conflict-Resolution OS",
"Support lawful contractual enforcement, notices, negotiation, mediation, arbitration and court remedies where proportionate and professionally reviewed.",
"Abusive litigation, retaliation and legal harassment are prohibited."),

"180": ("CORE","Governance & Audit","Legal Governance","P0","5","CRITICAL","KEEP",
"Records OS;Audit-Vigil OS;Encryption OS",
"Preserve tamper-evident evidence, provenance, timestamps, custody records, access history, integrity verification and retention metadata.",
"Evidence OS is foundational for audit, compliance and lawful dispute resolution."),

"181": ("PRODUCT","Marketing & Customer","Media Platform","P1","9","HIGH","REFRAME",
"Marketing OS;Design OS;Records OS",
"Manage content planning, production, approvals, publishing, asset lifecycle, channels, analytics, rights and editorial governance.",
"Media OS becomes governed content operations."),

"182": ("PRODUCT","Marketing & Customer","Media Platform","P2","9","HIGH","REFRAME",
"Media OS;Video OS;Audio systems",
"Manage lawful distribution of approved content across broadcast, streaming, social, web and partner channels with scheduling and analytics.",
"Broadcasting supports transparent communications rather than propaganda."),

"183": ("PRODUCT","Marketing & Customer","Media Platform","P3","17","MEDIUM","REFRAME",
"Video OS;Art OS;Media OS",
"Manage cinematic storytelling, scripts, assets, production workflows, editing, rendering, licensing and publishing.",
"Mythic imagery becomes ordinary creative storytelling."),

"184": ("PRODUCT","Marketing & Customer","Media Platform","P3","17","MEDIUM","REFRAME",
"Media OS;Audio systems",
"Manage licensed music assets, playlists, production metadata, audio environments and optional focus-oriented sound experiences.",
"Binaural or frequency effects must not be represented as guaranteed cognitive enhancement."),

"185": ("RETIRED_REFRAMED","Marketing & Customer","Product Governance","P3","9","HIGH","REFRAME",
"Music OS;Shopping OS;Experimentation",
"Use ordinary audio branding and interface sound design while requiring clear user control and prohibiting subliminal or covert behavior-modification techniques.",
"Frequency-coded checkout manipulation is prohibited."),

"186": ("PRODUCT","Marketing & Customer","Media Platform","P1","9","HIGH","KEEP",
"Media OS;Design OS;Storage",
"Manage video assets, production, encoding, metadata, rights, review, distribution and analytics.",
"Video OS is a standard multimedia capability."),

"187": ("DATA_PRODUCT","Marketing & Customer","Product Governance","P2","9","CRITICAL","REFRAME",
"Design OS;Analytics;Privacy Governance",
"Manage image assets and privacy-preserving UX analytics using aggregate, consented or otherwise lawful interaction data.",
"Eye or gaze tracking requires explicit authorization and must not become covert biometric surveillance."),

"188": ("SHARED_SERVICE","Developer Platform","Design Platform","P0","5","HIGH","KEEP",
"Aesthetic OS;Accessibility;Frontend Platform",
"Maintain reusable design tokens, components, interaction patterns, accessibility standards, documentation and implementation guidance.",
"Design OS provides the Dalizebo design system."),

"189": ("POLICY","Developer Platform","Design Platform","P1","5","MEDIUM","REFRAME",
"Design OS;Accessibility",
"Define typography, color, spacing, imagery, motion and visual-brand standards optimized for clarity, accessibility, usability and consistent identity.",
"Visual trust must derive from quality and clarity, not deceptive signaling."),

"190": ("PRODUCT","Marketing & Customer","Media Platform","P3","17","MEDIUM","REFRAME",
"Design OS;Media OS;Localization Platform",
"Support creation and management of culturally respectful artwork, illustrations, murals and generated media with attribution, licensing and localization review.",
"Cultural arbitrage becomes respectful localized creative production."),

"191": ("PRODUCT","Commerce & Retail","Commerce Platform","P0","6","HIGH","REFRAME",
"POS OS;Inventory OS;CRM",
"Manage stores, branches, assortments, pricing, inventory, staff operations, customers, fulfillment, reporting and physical commerce workflows.",
"Retail growth means competitive service and market expansion, not domination."),

"192": ("PRODUCT","Commerce & Retail","Commerce Platform","P0","6","CRITICAL","REFRAME",
"Inventory OS;Payment-Gateway OS;Identity OS",
"Provide secure point-of-sale checkout, carts, receipts, taxes, payments, refunds, inventory updates, staff permissions and offline-aware transaction handling.",
"DZC may only be one approved payment option if legally and operationally authorized."),

"193": ("RETIRED_REFRAMED","Commerce & Retail","Product Governance","P3","9","HIGH","REFRAME",
"CRM;Retail OS;Shopping OS",
"Manage customer profiles, preferences, household or business needs, service history and lifecycle engagement using consented data and fair customer practices.",
"Engineering dependency on essential needs is prohibited."),

"194": ("PRODUCT","Commerce & Retail","Product Governance","P0","6","HIGH","REFRAME",
"E-commerce OS;Design OS;Recommendation systems",
"Provide accessible product discovery, search, recommendations, carts, checkout, wishlists, comparison, reviews and customer-controlled shopping experiences.",
"Dopamine engineering and dark patterns are replaced by user-centered commerce design."),

"195": ("PRODUCT","Commerce & Retail","Commerce Platform","P0","6","CRITICAL","KEEP",
"Inventory OS;Shopping OS;Payment-Gateway OS;Identity OS",
"Provide the core digital commerce storefront, catalogue, cart, checkout, customer, order, fulfillment, promotion and service workflows.",
"E-commerce OS is a primary Dalizebo SaaS capability."),

"196": ("CORE","Payments & Billing","Payments Platform","P0","5","CRITICAL","REFRAME",
"Banking OS;Medici-Ledger OS;Compliance OS",
"Provide a payment abstraction layer over approved processors and banking rails for authorization, capture, refunds, settlement, reconciliation, webhooks and payment-state management.",
"Payment ownership means architectural control and portability, not bypassing regulated payment networks."),

"197": ("SHARED_SERVICE","Developer Platform","Platform Architecture","P2","17","HIGH","REFRAME",
"Platform OS;Identity OS;Billing;Marketplace",
"Coordinate interoperability, identity, billing, data contracts, navigation, integrations and shared experiences across Dalizebo products.",
"Ecosystem synergy becomes explicit multi-product platform integration."),

"198": ("CORE","Developer Platform","Platform Architecture","P1","12","CRITICAL","REFRAME",
"Identity OS;Protocol OS;Cloud-OS;Governance OS",
"Provide the shared control plane, tenancy, service contracts, identity, configuration, observability and platform primitives supporting multiple Dalizebo products.",
"Platform scale targets reliable multi-tenant operation rather than ideological signal propagation."),

"199": ("PRODUCT","Marketing & Customer","Customer Platform","P2","9","HIGH","REFRAME",
"Identity OS;Billing;CRM;Contract OS",
"Manage membership tiers, eligibility, subscriptions, partner programs, benefits, entitlements, renewals, account state and transparent access rules.",
"Membership differentiation must be documented, lawful and non-deceptive."),

"200": ("PRODUCT","Marketing & Customer","Customer Platform","P2","9","HIGH","REFRAME",
"Membership OS;CRM;Commerce",
"Manage transparent loyalty points, benefits, rewards, redemption, expiry rules, customer consent, fraud controls and program analytics.",
"Variable reward mechanics designed to create compulsive dependence are prohibited."),
}

POLICIES = {
"Data & Knowledge":
"Privacy;consent;provenance;retention;professional-boundary controls",
"Frontier R&D":
"Research boundary;scientific validation;safety review;privacy;no unsupported claims",
"Identity & Security":
"Privacy;consent;biometric protection;encryption;least privilege",
"Automation & Workflow":
"User control;bounded automation;reversibility;privacy",
"AI & Intelligence":
"Model governance;human review;provenance;privacy;localization quality",
"Marketing & Customer":
"Truthful communication;consent;privacy;anti-dark-patterns;customer autonomy",
"Legal & Compliance":
"Lawful process;professional review;proportionality;evidence;authorization",
"Governance & Audit":
"Evidence integrity;audit;retention;chain of custody;access control",
"Developer Platform":
"Standards;accessibility;security;versioning;platform governance",
"Commerce & Retail":
"Consumer protection;pricing transparency;payments security;privacy;fair UX",
"Payments & Billing":
"PCI-aligned controls;authorization;reconciliation;fraud controls;regulatory compliance",
}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid OS review ledger")

expected = {f"{i:03d}" for i in range(151, 201)}
found = set()

for row in rows:

    pid = row["canonical_id"]

    if pid not in D:
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
        canonical,
        notes,
    ) = D[pid]

    row["review_status"] = "CLASSIFIED"
    row["domain"] = domain
    row["owner"] = owner
    row["priority"] = priority
    row["implementation_type"] = impl_type
    row["dependencies"] = dependencies

    row["inputs"] = (
        "Authorized user, platform, content, customer, legal, "
        "wellness, localization, commerce, and governance data"
    )

    row["outputs"] = (
        "Governed records, content, recommendations, workflows, "
        "transactions, analyses, interfaces, or audit evidence"
    )

    row["policies"] = POLICIES[domain]
    row["events"] = f"os.{pid}.evaluated"
    row["apis"] = "Internal versioned API; external exposure only where explicitly approved"

    row["data_requirements"] = (
        "Tenant-scoped authorized data; provenance; consent where required; "
        "retention; classification; audit metadata"
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
        "ERROR: missing Cluster E OS entries: "
        + ", ".join(sorted(missing))
    )

tmp = REVIEW.with_suffix(".tmp")

with tmp.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

tmp.replace(REVIEW)

cluster = [
    r for r in rows
    if r["canonical_id"] in expected
]

types = Counter(r["implementation_type"] for r in cluster)
dispositions = Counter(r["disposition"] for r in cluster)

lines = [
    "# Operating Systems Cluster E Reconciliation",
    "",
    "## Scope",
    "",
    "OS-151 through OS-200 — Specialized & Domain Dominance.",
    "",
    "Original source statements remain unchanged.",
    "",
    "Health, biometric, behavioral, legal, media and commerce capabilities "
    "are subject to privacy, consent, professional-review, autonomy and "
    "anti-dark-pattern controls.",
    "",
    "## Implementation Classification",
    "",
]

for key in sorted(types):
    lines.append(f"- {key}: {types[key]}")

lines += ["", "## Canonical Disposition", ""]

for key in sorted(dispositions):
    lines.append(f"- {key}: {dispositions[key]}")

lines.extend(["", "## Decisions", ""])

for row in cluster:
    lines.extend([
        f"### OS-{row['canonical_id']} — {row['name']}",
        "",
        f"**Type:** {row['implementation_type']}",
        "",
        f"**Disposition:** {row['disposition']}",
        "",
        f"**Domain:** {row['domain']}",
        "",
        f"**Owner:** {row['owner']}",
        "",
        f"**Priority:** {row['priority']}",
        "",
        f"**Security:** {row['security_level']}",
        "",
        "**Original Source Statement**",
        "",
        f"> {row['source_statement']}",
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

REPORT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

classified = sum(
    1 for r in rows
    if r["canonical_id"]
    and r["review_status"] == "CLASSIFIED"
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

Cluster E classified.

## Completed Canonical Range

OS-001 → OS-200

## Next Work

OS-201 → OS-269 — Advanced, Meta & Terminal.

## Governing Rule

Source statements remain preserved.

Unsafe, unlawful, deceptive, coercive, privacy-invasive, or medically
unsupported source concepts are retired or canonically reframed.

Canonical implementation decisions are recorded separately from source history.
""" % classified,
encoding="utf-8",
)

print("OK: OS Cluster E 151-200 classified.")
print(f"Canonical classification: {classified}/269")

for key in sorted(types):
    print(f"{key}: {types[key]}")
