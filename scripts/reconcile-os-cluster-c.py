#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REPORT = ROOT / "operating-systems/reconciliation/reports/CLUSTER_C.md"
STATUS = ROOT / "operating-systems/reconciliation/reports/STATUS.md"

# implementation_type, domain, owner, priority, phase, security,
# disposition, dependencies, canonical_interpretation, decision_notes

D = {

"051": ("DATA_PRODUCT","Marketing & Customer","Marketing Governance","P1","9","HIGH","KEEP",
"Marketing OS;Knowledge OS",
"Measure customer and market sentiment using lawful research, surveys, feedback, social listening, support data, and aggregate analytics.",
"Sentiment analysis informs decisions without psychological manipulation."),

"052": ("SHARED_SERVICE","Marketing & Customer","Brand Governance","P2","9","MEDIUM","REFRAME",
"Marketing OS;Knowledge OS",
"Manage truthful brand narratives, positioning, product stories, institutional history, and communication consistency across channels.",
"Mythic-story engineering becomes evidence-based brand storytelling."),

"053": ("RETIRED_REFRAMED","Marketing & Customer","Marketing Governance","P3","9","HIGH","REFRAME",
"Marketing OS;Viral-Loop OS",
"Develop memorable, shareable, truthful campaign language and creative concepts without attempting psychological infection, coercion, or deceptive propagation.",
"Mind-virus mechanics are retired; legitimate creative-content optimization remains."),

"054": ("RETIRED_REFRAMED","Marketing & Customer","Communications Governance","P3","9","HIGH","REFRAME",
"Narrative OS;Marketing OS",
"Provide factual content management, public communications, campaign publishing, corrections, provenance, and channel governance.",
"Propaganda and deliberate reality distortion are prohibited."),

"055": ("RETIRED_REFRAMED","Marketing & Customer","Product Governance","P3","9","HIGH","REFRAME",
"Marketing OS;Sentiment OS",
"Use ethical UX research, personalization, experimentation, and choice architecture to improve customer outcomes while preserving autonomy and transparency.",
"Conditioning customers through covert interface triggers is prohibited."),

"056": ("PRODUCT","Marketing & Customer","Marketing Governance","P1","9","HIGH","REFRAME",
"Sentiment OS;Narrative OS",
"Manage campaigns, segmentation, localization, content, attribution, experimentation, consent, and marketing automation.",
"Cultural localization must serve relevance and accessibility rather than exploitation."),

"057": ("AUTOMATION","Marketing & Customer","Growth Governance","P2","9","HIGH","REFRAME",
"Marketing OS;Customer-Capture OS",
"Support referral, sharing, community, content-distribution, and product-led growth loops with measurement and abuse controls.",
"Growth loops must not use deception, spam, dark patterns, or coercive amplification."),

"058": ("PRODUCT","Marketing & Customer","Growth Governance","P1","9","HIGH","REFRAME",
"Marketing OS;CRM;Payments",
"Manage lawful customer acquisition and conversion funnels from awareness through signup, purchase, retention, and lifecycle engagement.",
"Customer capture becomes customer acquisition and conversion."),

"059": ("SHARED_SERVICE","Marketing & Customer","Brand Governance","P2","9","MEDIUM","REFRAME",
"Marketing OS;Knowledge OS",
"Build brand authority through measurable quality, reliable delivery, verified claims, customer outcomes, research, standards, and transparent communications.",
"Authority derives from evidence rather than manufactured status."),

"060": ("DATA_PRODUCT","Data & Knowledge","Knowledge Governance","P3","17","MEDIUM","REFRAME",
"Archive OS;Knowledge OS;Legacy OS",
"Maintain verified institutional history, milestones, provenance, achievements, lessons, and long-term brand records.",
"Legend building becomes governed institutional history."),

"061": ("DATA_PRODUCT","AI & Intelligence","Strategy","P2","10","HIGH","REFRAME",
"Simulation Engine;Decision-Matrix OS;Game-Theory OS",
"Stress-test strategies through simulations, scenarios, market models, assumptions, sensitivity analysis, and controlled adversarial testing.",
"Warfare terminology is reframed as strategic simulation."),

"062": ("DATA_PRODUCT","AI & Intelligence","Strategy","P2","10","HIGH","REFRAME",
"Simulation-Warfare OS;Decision-Matrix OS",
"Model strategic interactions, incentives, negotiations, competition, partnerships, and multi-party scenarios using game-theoretic methods.",
"Game theory supports lawful strategy and negotiation, not hostile operations."),

"063": ("DATA_PRODUCT","AI & Intelligence","Strategy","P1","10","HIGH","REFRAME",
"Information-Vacuum OS;Signal-Filter OS",
"Provide lawful competitive intelligence using public, licensed, customer-provided, regulatory, financial, product, and market information.",
"Do not acquire private competitor data without authorization."),

"064": ("RETIRED_REFRAMED","AI & Intelligence","Legal & Compliance","P3","10","CRITICAL","REFRAME",
"Competitor-Analysis OS;Compliance OS",
"Collect market intelligence only from lawful public, licensed, consented, contractual, or otherwise authorized sources.",
"Espionage, unauthorized access, covert collection, and acquisition of non-public competitor information are prohibited."),

"065": ("DATA_PRODUCT","Operations & Logistics","Operations Governance","P2","15","HIGH","REFRAME",
"Geospatial data;Compliance OS",
"Use lawful geospatial, infrastructure, demographic, environmental, logistics, and public planning data for regional operations and site analysis.",
"Reconnaissance becomes lawful geospatial and regional planning."),

"066": ("SHARED_SERVICE","Data & Knowledge","Data Governance","P1","10","CRITICAL","REFRAME",
"Integrations OS;Knowledge OS;Signal-Filter OS",
"Ingest and index approved external and internal information sources with provenance, permissions, retention, classification, and data-minimization controls.",
"Total indiscriminate ingestion is replaced by governed information ingestion."),

"067": ("DATA_PRODUCT","AI & Intelligence","Data Governance","P1","10","HIGH","REFRAME",
"Information-Vacuum OS;Knowledge OS",
"Rank, filter, deduplicate, classify, summarize, and prioritize information according to defined relevance, quality, provenance, and confidence criteria.",
"Signal filtering uses explicit measurable criteria rather than vague claims of unlimited intelligence."),

"068": ("SHARED_SERVICE","AI & Intelligence","AI Governance","P1","10","HIGH","KEEP",
"Reasoning OS;Knowledge OS",
"Check structured arguments for logical consistency, unsupported assumptions, contradiction, fallacies, and traceable evidence.",
"Logic verification remains a legitimate decision-support capability."),

"069": ("SHARED_SERVICE","AI & Intelligence","AI Governance","P1","10","HIGH","REFRAME",
"Logic-Chain OS;Knowledge OS",
"Support structured reasoning, assumptions review, alternative hypotheses, evidence evaluation, uncertainty, and decision critique.",
"Reasoning supports human accountability rather than becoming an unquestionable strategic authority."),

"070": ("SHARED_SERVICE","AI & Intelligence","AI Governance","P1","10","CRITICAL","REFRAME",
"Knowledge OS;Information-Vacuum OS;Decision-Matrix OS",
"Synthesize governed information from authorized systems into traceable analyses, recommendations, summaries, and decision context.",
"Synthesis must retain source provenance and uncertainty."),

"071": ("SHARED_SERVICE","AI & Intelligence","Executive Governance","P1","10","CRITICAL","KEEP",
"Pillars OS;Synthesis OS;Risk Governance",
"Score options against approved criteria such as ROI, risk, compliance, strategic alignment, resilience, customer value, and confidence.",
"Decision matrices provide transparent recommendations rather than autonomous final authority."),

"072": ("SHARED_SERVICE","AI & Intelligence","Executive Governance","P2","10","HIGH","REFRAME",
"Synthesis OS;Decision-Matrix OS;Knowledge OS",
"Generate structured strategic-plan drafts including objectives, assumptions, risks, milestones, alternatives, evidence, and review requirements.",
"Generated strategy remains subject to accountable human approval."),

"073": ("AUTOMATION","Automation & Workflow","Executive Governance","P1","10","CRITICAL","REFRAME",
"Executive-Action OS;Pillars OS;Loop OS",
"Execute explicitly authorized operational plans through governed workflows after policy, permission, safety, approval, and audit checks.",
"Kinetic execution is replaced by bounded digital and business-process execution."),

"074": ("RETIRED_REFRAMED","Data & Knowledge","Strategy","P3","15","HIGH","REFRAME",
"Recon OS;Analytics",
"Provide regional maps of Dalizebo facilities, customers, logistics, infrastructure, market coverage, partnerships, risks, and opportunities using lawful data.",
"Geospatial dominance tracking is replaced by regional operations intelligence."),

"075": ("SHARED_SERVICE","Governance & Audit","Corporate Strategy","P2","15","HIGH","REFRAME",
"Scale-OS;Deployment OS;Alliance OS",
"Plan repeatable regional and product expansion using standardized architecture, capacity models, economics, compliance, partnerships, and measurable readiness gates.",
"Empire replication becomes governed platform and business expansion."),

"076": ("RETIRED_REFRAMED","Governance & Audit","Executive Governance","P3","15","CRITICAL","REFRAME",
"Jurisdiction OS;Cloud-OS;Compliance OS",
"Increase organizational resilience through portability, provider abstraction, redundancy, internal capability, open standards, and lawful operating independence.",
"Absolute independence from lawful external authorities is not an approved objective."),

"077": ("RETIRED_REFRAMED","Marketing & Customer","Corporate Strategy","P3","15","HIGH","REFRAME",
"Alliance OS;Marketing OS;Competitor-Analysis OS",
"Build legitimate market leadership through superior products, service, distribution, research, partnerships, standards participation, and customer trust.",
"Structural capture, coercive dependency, monopoly engineering, and unlawful market control are prohibited."),

"078": ("RETIRED_REFRAMED","Governance & Audit","Executive Governance","P3","15","CRITICAL","REFRAME",
"Strategy-Draft OS;Security OS;Compliance OS",
"Protect confidential strategic planning through need-to-know access, operational security, staged disclosure, and lawful competitive confidentiality.",
"Covert maneuvers intended to evade lawful accountability or harm competitors are prohibited."),

"079": ("SHARED_SERVICE","Marketing & Customer","Partner Governance","P2","17","HIGH","REFRAME",
"Contract OS;CRM;Governance OS",
"Manage partnerships, alliances, joint initiatives, referrals, ecosystem relationships, roles, agreements, incentives, performance, and governance.",
"Partners are governed collaborators, not covert proxies."),

"080": ("POLICY","Infrastructure & Cloud","Business Continuity","P3","15","CRITICAL","REFRAME",
"Jurisdiction OS;Cloud-OS;Archive OS",
"Maintain geographically independent operational, legal, infrastructure, data, treasury, and recovery options where justified by resilience and compliance.",
"Neutral harbors become lawful geographic redundancy and continuity planning."),

"081": ("R&D","Identity & Security","Security Architecture","R&D","18","CRITICAL","R&D",
"Encryption OS;Lattice-Crypt OS",
"Evaluate and progressively adopt standardized post-quantum cryptography according to threat models, interoperability, performance, and standards maturity.",
"Post-quantum migration is governed by cryptographic agility and recognized standards."),

"082": ("R&D","Identity & Security","Security Architecture","R&D","18","CRITICAL","R&D",
"Encryption OS;Quantum-Safe OS",
"Research standardized lattice-based cryptographic primitives and migration approaches for future platform security.",
"Experimental cryptography must not replace vetted production standards prematurely."),

"083": ("CORE","Data & Knowledge","Knowledge Governance","P1","5","CRITICAL","REFRAME",
"Records OS;Encryption OS;Storage",
"Provide durable, versioned, encrypted, integrity-checked, geographically redundant archival storage with retention and tested restoration.",
"Long-term archival is retained without relying on an arbitrary thousand-year guarantee."),

"084": ("CORE","Data & Knowledge","Knowledge Governance","P0","5","HIGH","REFRAME",
"Archive OS;Imperial-Library OS;AI Gateway",
"Index approved organizational knowledge for search, retrieval, citation, RAG, access control, versioning, and lifecycle governance.",
"Knowledge ingestion must respect authorization, provenance, privacy, and retention."),

"085": ("CORE","Data & Knowledge","Data Governance","P0","5","CRITICAL","REFRAME",
"Storage;Knowledge OS;Records OS",
"Provide governed raw and curated data storage for institutional knowledge, files, datasets, artifacts, documents, and strategic records.",
"Imperial Library becomes the governed institutional data library."),

"086": ("POLICY","Governance & Audit","Corporate Governance","P2","14","CRITICAL","REFRAME",
"Identity OS;Access-Control OS;Records OS",
"Maintain succession, delegation, emergency authority, key-person continuity, access transfer, institutional knowledge, and recovery procedures.",
"Succession requires governed triggers and accountable authorization."),

"087": ("R&D","AI & Intelligence","AI Governance","R&D","18","CRITICAL","REFRAME",
"Knowledge OS;Memory-Bank OS;Reasoning OS",
"Research an institutional AI decision-support system based on documented principles, authorized knowledge, historical decisions, and explicit governance.",
"It must not claim to reproduce a person's consciousness or identity."),

"088": ("R&D","AI & Intelligence","AI Governance","R&D","18","CRITICAL","REFRAME",
"Digital-Lucas Node;Knowledge OS",
"Improve institutional AI using curated authorized decision records, feedback, evaluations, versioned datasets, controlled training, and rollback.",
"Continuous uncontrolled copying of an individual's decisions into model weights is prohibited."),

"089": ("RETIRED_REFRAMED","AI & Intelligence","AI Governance","R&D","18","HIGH","REFRAME",
"Digital-Lucas Node;Reasoning OS",
"Evaluate institutional AI against documented decision principles, factual accuracy, consistency, calibration, safety, and task-specific benchmarks.",
"Literal 99.9 percent biological or psychological fidelity is not an approved target."),

"090": ("DATA_PRODUCT","AI & Intelligence","Strategy","P2","10","HIGH","REFRAME",
"Memory-Bank OS;Knowledge OS",
"Identify useful historical analogies and recurring patterns while explicitly testing whether current conditions support the comparison.",
"Historical pattern matching informs but does not mechanically determine decisions."),

"091": ("SHARED_SERVICE","Data & Knowledge","Knowledge Governance","P1","10","HIGH","REFRAME",
"Knowledge OS;Archive OS",
"Store reusable decision patterns, lessons, playbooks, models, assumptions, outcomes, and validated organizational knowledge.",
"Memory Bank becomes versioned institutional learning rather than unquestioned recursive reuse."),

"092": ("POLICY","Governance & Audit","Corporate Governance","P3","17","HIGH","REFRAME",
"Succession OS;Archive OS;Knowledge OS",
"Manage long-term institutional continuity, stewardship, governance history, ownership transitions, knowledge transfer, and societal impact.",
"Legacy management becomes accountable institutional continuity."),

"093": ("DATA_PRODUCT","AI & Intelligence","Strategy","P3","18","HIGH","REFRAME",
"Simulation-Warfare OS;Predictive-Crisis OS",
"Model long-horizon scenarios, second-order effects, option value, resilience, infrastructure lifecycle, and intergenerational consequences.",
"One-hundred-year projections are scenario tools rather than precise predictions."),

"094": ("DATA_PRODUCT","AI & Intelligence","Risk Governance","P2","10","HIGH","REFRAME",
"Signal-Filter OS;Simulation-Warfare OS;Black-Swan OS",
"Identify emerging risks using indicators, scenarios, anomaly detection, probabilistic forecasting, confidence ranges, and expert review.",
"Black swans cannot be guaranteed to be predicted."),

"095": ("POLICY","Governance & Audit","Business Continuity","P1","8","CRITICAL","REFRAME",
"Predictive-Crisis OS;Stability OS;Archive OS",
"Maintain resilience playbooks, reserves, recovery procedures, contingency plans, failover options, simulations, and crisis decision structures.",
"Black-Swan OS becomes business continuity and systemic resilience."),

"096": ("SHARED_SERVICE","Infrastructure & Cloud","Reliability Engineering","P1","8","CRITICAL","REFRAME",
"Monitoring OS;Equilibrium OS;Scale-OS",
"Monitor platform stability using service objectives, capacity, error rates, latency, dependency health, financial risk, and operational thresholds.",
"Stability is measured through explicit health and resilience indicators."),

"097": ("DATA_PRODUCT","AI & Intelligence","Risk Governance","P2","10","HIGH","REFRAME",
"Stability OS;Decision-Matrix OS",
"Balance growth, reliability, cost, security, compliance, human capacity, and structural resilience using explicit metrics and policy thresholds.",
"Equilibrium becomes governed trade-off analysis."),

"098": ("R&D","AI & Intelligence","AI Governance","R&D","18","CRITICAL","REFRAME",
"Automation Governance;Pillars OS;Stability OS",
"Research increasingly capable automation while requiring policy boundaries, observability, interruptibility, authorization, rollback, and human accountability.",
"Absolute strategic autonomy is not an approved state."),

"099": ("AUTOMATION","Automation & Workflow","Platform Architecture","P3","16","CRITICAL","REFRAME",
"Optimization OS;Monitoring OS;Pillars OS",
"Allow controlled system adaptation through versioned configuration, experiments, feature flags, policy-bounded optimization, testing, approval, and rollback.",
"Uncontrolled self-mutation of production systems is prohibited."),

"100": ("R&D","AI & Intelligence","AI Governance","R&D","18","CRITICAL","REFRAME",
"Singularity OS;Omega governance;Pillars OS",
"Treat the Omega concept as a long-horizon research milestone for highly integrated automation operating under constitutional, legal, safety, and human-accountability controls.",
"There is no terminal sequence that supersedes governance or human accountability."),
}

POLICY_BY_DOMAIN = {
"Marketing & Customer":
"Truthful communications;consent;privacy;anti-dark-patterns;campaign governance",
"AI & Intelligence":
"Model governance;provenance;human accountability;privacy;safety;evaluation",
"Data & Knowledge":
"Data authorization;provenance;privacy;retention;classification;access control",
"Operations & Logistics":
"Authorization;privacy;safety;geospatial data governance;compliance",
"Governance & Audit":
"Constitutional policy;authorization;audit;exceptions;accountability",
"Infrastructure & Cloud":
"Resilience;security;data residency;change control;business continuity",
"Identity & Security":
"Cryptographic standards;key management;security review;crypto agility",
"Automation & Workflow":
"Bounded autonomy;authorization;observability;rate limits;rollback",
}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid OS review ledger")

expected = {f"{i:03d}" for i in range(51, 101)}
found = set()

for row in rows:

    pid = row["canonical_id"]

    if pid not in D:
        continue

    (
        impl_type, domain, owner, priority, phase,
        security, disposition, dependencies,
        canonical, notes
    ) = D[pid]

    row["review_status"] = "CLASSIFIED"
    row["domain"] = domain
    row["owner"] = owner
    row["priority"] = priority
    row["implementation_type"] = impl_type
    row["dependencies"] = dependencies

    row["inputs"] = (
        "Authorized data, evidence, events, configuration, "
        "research, telemetry, and governance context"
    )

    row["outputs"] = (
        "Governed analyses, recommendations, content, decisions, "
        "records, alerts, plans, or authorized actions"
    )

    row["policies"] = POLICY_BY_DOMAIN[domain]
    row["events"] = f"os.{pid}.evaluated"
    row["apis"] = "Internal versioned API; external exposure only where approved"

    row["data_requirements"] = (
        "Tenant-scoped authorized data; provenance; classification; "
        "retention; audit metadata"
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
        "ERROR: missing Cluster C OS entries: "
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

counts = Counter(
    r["implementation_type"]
    for r in cluster
)

dispositions = Counter(
    r["disposition"]
    for r in cluster
)

lines = [
    "# Operating Systems Cluster C Reconciliation",
    "",
    "## Scope",
    "",
    "OS-051 through OS-100 — Intelligence, Strategy & Influence.",
    "",
    "Original source statements remain unchanged.",
    "",
    "Unsafe, unlawful, deceptive, coercive, or unbounded concepts are "
    "retired or canonically reframed.",
    "",
    "## Implementation Classification",
    "",
]

for key in sorted(counts):
    lines.append(f"- {key}: {counts[key]}")

lines += [
    "",
    "## Canonical Disposition",
    "",
]

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
        f"**Priority:** {row['priority']}",
        "",
        f"**Domain:** {row['domain']}",
        "",
        f"**Owner:** {row['owner']}",
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
f"""# Phase 2 Operating Systems Status

## Canonical ID Space

OS-001 → OS-269

## Raw Source Entries Preserved

279

## Overflow Reconciliation

10 / 10 reconciled

## Canonical Classification

{classified} / 269 complete

## Current Stage

Cluster C classified.

## Completed Canonical Range

OS-001 → OS-100

## Next Work

OS-101 → OS-150 — Physical, Logistical & Environmental.

## Governing Rule

Source statements remain preserved.

Unsafe or unlawful source concepts are retired or canonically reframed.

Canonical implementation decisions are recorded separately from source history.
""",
encoding="utf-8",
)

print("OK: OS Cluster C 051-100 classified.")
print(f"Canonical classification: {classified}/269")

for key in sorted(counts):
    print(f"{key}: {counts[key]}")

print("Disposition:")
for key in sorted(dispositions):
    print(f"{key}: {dispositions[key]}")
