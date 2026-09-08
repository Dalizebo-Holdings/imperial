#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / "constitution/reconciliation/review/pillar-review.csv"
REPORT = ROOT / "constitution/reconciliation/reports/CLUSTER_B.md"

# classification, domain, owner, safety_action,
# canonical_interpretation, decision_notes

D = {

"041": (
    "REFRAME", "Platform Strategy", "Platform Governance",
    "CANONICAL_REFRAME",
    "Build valuable commerce infrastructure that becomes a preferred regional platform through interoperability, reliability, economics, and customer value rather than coercive market capture.",
    "Structural capture becomes lawful platform leadership."
),

"042": (
    "REFRAME", "Public Policy / Legal", "Legal & Compliance",
    "CANONICAL_REFRAME",
    "Participate transparently in public-policy consultation, industry bodies, standards development, and regulatory engagement while avoiding improper influence, conflicts of interest, or regulatory capture.",
    "Dalizebo may advocate for sound policy but must not capture regulators."
),

"043": (
    "REFRAME", "Platform Strategy", "Executive Governance",
    "CANONICAL_REFRAME",
    "Pursue regional platform leadership by providing superior transaction, workforce, infrastructure, and business services while preserving competition and customer choice.",
    "Dominance becomes measurable market leadership."
),

"044": (
    "TECHNICAL", "Architecture", "Platform Architecture",
    "NONE",
    "Maintain a standardized global platform core with configurable regional localization for language, currency, tax, payments, logistics, compliance, and user experience.",
    "Directly supports the regional data-plane architecture."
),

"045": (
    "REFRAME", "Localization", "Product Governance",
    "CANONICAL_REFRAME",
    "Use local languages and cultural context to improve accessibility, trust, relevance, and usability without exploiting cultural identity or concealing material information.",
    "Cultural arbitrage becomes responsible localization."
),

"046": (
    "REFRAME", "Brand", "Brand Governance",
    "CANONICAL_REFRAME",
    "Maintain a coherent long-term brand narrative grounded in verifiable achievements, values, history, and customer outcomes.",
    "Brand mythology must not misrepresent reality."
),

"047": (
    "KEEP", "Brand / Reputation", "Executive Governance",
    "NONE",
    "Build authority primarily through reliable delivery, measurable results, technical competence, and demonstrated customer value rather than publicity alone.",
    "Results-driven credibility is retained."
),

"048": (
    "POLICY", "Competitive Intelligence", "Strategy",
    "NONE",
    "Maintain high-quality lawful market intelligence using public, licensed, contractual, consented, and internally generated data with clear provenance.",
    "Information advantage remains legitimate when acquisition is lawful."
),

"049": (
    "REFRAME", "Partnerships", "Partner Governance",
    "CANONICAL_REFRAME",
    "Use capable local partners to expand efficiently where incentives, responsibilities, economics, and accountability are contractually aligned.",
    "Partners are collaborators, not proxy instruments."
),

"050": (
    "REFRAME", "Corporate Governance", "Executive Governance",
    "CANONICAL_REFRAME",
    "Negotiate appropriate reserved matters, veto rights, board rights, and protective provisions according to ownership, risk, fiduciary duties, and the specific joint venture.",
    "Absolute veto power is replaced by proportionate governance rights."
),

"051": (
    "TECHNICAL", "Architecture / Regional Expansion", "Platform Architecture",
    "NONE",
    "Design deployable modules, infrastructure templates, configuration layers, and APIs so validated capabilities can be reproduced across geographic regions without product forks.",
    "Directly supports modular regional deployment."
),

"052": (
    "POLICY", "Capital Allocation", "Finance Governance",
    "NONE",
    "Evaluate deployments using explicit capital-efficiency and multi-outcome metrics rather than expenditure volume alone.",
    "The 1-to-5 ratio is treated as an optimization target rather than an immutable formula."
),

"053": (
    "TECHNICAL", "Engineering", "Engineering Governance",
    "NONE",
    "Continuously refactor high-value platform components based on defects, performance, maintainability, security, developer experience, and operational evidence.",
    "Self-improvement requires controlled engineering practice."
),

"054": (
    "REFRAME", "Governance Automation", "Pillars OS",
    "CANONICAL_REFRAME",
    "Automate deterministic governance controls where appropriate while preserving authorized human review, exceptions, appeal paths, emergency overrides, and auditability.",
    "Code may enforce policy but cannot replace accountable governance."
),

"055": (
    "REFRAME", "Partner Economics", "Partner Governance",
    "CANONICAL_REFRAME",
    "Use transparent commercial incentives, financing, revenue share, support, and shared investment to align long-term partner interests without engineering personal dependence or compulsory loyalty.",
    "Patronage becomes transparent incentive alignment."
),

"056": (
    "REFRAME", "Marketing", "Marketing Governance",
    "CANONICAL_REFRAME",
    "Use truthful pre-launch storytelling, demonstrations, education, customer research, and campaign sequencing to establish product understanding and demand.",
    "Psychological conditioning is not an approved marketing mechanism."
),

"057": (
    "REFRAME", "Marketing / Content", "Marketing Governance",
    "CANONICAL_REFRAME",
    "Design memorable and shareable brand messages that spread organically while remaining truthful, attributable, non-deceptive, and appropriate for their audience.",
    "Mind-virus terminology becomes ethical viral content design."
),

"058": (
    "RETIRE", "Communications", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo must not use propaganda systems designed to control public reality. Use transparent corporate communications, factual media relations, attributable content, and correction processes instead.",
    "Broadcast dominance intended to define reality is not an approved capability."
),

"059": (
    "RETIRE", "Markets / Marketing", "Risk Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo must not manipulate market sentiment to manufacture artificial buying or selling opportunities. Market communication must remain accurate and compliant.",
    "Intentional market-emotion manipulation is retired."
),

"060": (
    "REFRAME", "Product / UX", "Product Governance",
    "CANONICAL_REFRAME",
    "Use behavioral science and choice architecture to reduce friction and help users make informed decisions aligned with their interests, with clear pricing, consent, and cancellation paths.",
    "Dark patterns and margin-maximizing manipulation are prohibited."
),

"061": (
    "REFRAME", "Corporate Development", "Executive Governance",
    "CANONICAL_REFRAME",
    "Use minority investments with explicitly negotiated governance rights appropriate to ownership, contracts, fiduciary obligations, competition law, and stakeholder interests.",
    "Control must arise from legitimate contractual governance rather than concealed influence."
),

"062": (
    "REFRAME", "Knowledge Architecture", "Knowledge Governance",
    "CANONICAL_REFRAME",
    "Maintain a precise internal ontology and shared terminology that improves communication, documentation, search, and institutional knowledge.",
    "Terminology must improve coordination rather than deliberately exclude competitors or outsiders."
),

"063": (
    "RETIRE", "Design / Marketing", "Product Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Do not design interfaces or imagery specifically to bypass rational user judgment. Visual design should improve comprehension, trust, accessibility, identity, and usability.",
    "Circumventing rational resistance is not an approved design objective."
),

"064": (
    "RETIRE", "Commerce", "Commerce Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Artificial availability, fabricated inventory pressure, and false scarcity are prohibited. Scarcity messages must reflect genuine stock, capacity, deadlines, or availability.",
    "False scarcity is retired."
),

"065": (
    "RETIRE", "Automation / Physical Systems", "Security Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Automated physical systems may support logistics, inspection, monitoring, maintenance, and emergency safety under explicit authorization and bounded controls, but intelligence must not automatically trigger harmful physical action.",
    "The direct intelligence-to-kinetic-response mechanism is retired."
),

"066": (
    "POLICY", "Procurement / Pricing", "Finance Governance",
    "NONE",
    "Reduce third-party costs through competitive procurement, automation, scale, direct integration, and contract negotiation while pricing Dalizebo services transparently according to delivered value.",
    "Cost efficiency is retained without exploitative pricing."
),

"067": (
    "RETIRE", "Information Governance", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo-controlled spaces must not claim exclusive authority over truth. Platform information should be evidence-based, attributable, correctable, and open to appropriate external verification.",
    "Sole-arbiter information control is retired."
),

"068": (
    "KEEP", "Reliability", "Reliability Engineering",
    "NONE",
    "Prioritize platform integrity, service recovery, security, and operational continuity during incidents while communicating material impacts accurately.",
    "Reliability remains more important than superficial optics."
),

"069": (
    "POLICY", "Treasury", "Finance Governance",
    "NONE",
    "Diversify material treasury and ownership exposure across appropriate assets, currencies, providers, and jurisdictions according to approved risk limits.",
    "Portfolio diversification is retained."
),

"070": (
    "REFRAME", "Talent", "People Governance",
    "CANONICAL_REFRAME",
    "Recruit and develop high-performing talent using role-relevant skills, evidence, structured assessment, equal-opportunity practices, and transparent advancement criteria.",
    "Elite selection must not depend on ideological or ritual conformity."
),

"071": (
    "REFRAME", "Marketing / Communications", "Marketing Governance",
    "CANONICAL_REFRAME",
    "Create useful, memorable information products and campaigns designed for legitimate sharing, education, community participation, and brand awareness.",
    "Self-replicating content must remain truthful and non-manipulative."
),

"072": (
    "REFRAME", "Organizational Culture", "People Governance",
    "CANONICAL_REFRAME",
    "Turn effective operating practices into durable organizational habits, traditions, onboarding standards, and institutional routines while allowing challenge and improvement.",
    "Culture must support voluntary professional alignment rather than compulsory multi-generational compliance."
),

"073": (
    "REFRAME", "Market Intelligence", "Strategy",
    "CANONICAL_REFRAME",
    "Measure gaps between stakeholder perception and verified organizational capabilities, market position, service quality, and outcomes.",
    "Sentiment analysis becomes evidence-based perception-versus-performance measurement."
),

"074": (
    "REFRAME", "Design", "Brand Governance",
    "CANONICAL_REFRAME",
    "Use consistent, high-quality design to signal reliability, confidence, accessibility, technical quality, and brand identity.",
    "Aesthetic dominance becomes professional design quality."
),

"075": (
    "POLICY", "Strategy", "Executive Governance",
    "NONE",
    "Maintain strategic independence from short-term media cycles and popularity pressure while continuing to incorporate credible external evidence, customer feedback, regulation, and stakeholder risk.",
    "Independence must not become informational isolation."
),

"076": (
    "POLICY", "Partnerships", "Partner Governance",
    "NONE",
    "Align partner incentives so material upside and downside are shared proportionately through investment, performance terms, responsibilities, and transparent economics.",
    "Skin-in-the-game principle retained."
),

"077": (
    "REFRAME", "Security / Knowledge", "Security Governance",
    "CANONICAL_REFRAME",
    "Use multilingual terminology where operationally useful, but protect confidential intent through access control, encryption, classification, and information-security controls rather than linguistic obscurity.",
    "Security through hidden dialect terminology is not sufficient."
),

"078": (
    "REFRAME", "Brand / Continuity", "Brand Governance",
    "CANONICAL_REFRAME",
    "Build a durable institutional brand, documented history, culture, and body of work that can continue independently of any individual founder.",
    "Founder mythology becomes institutional brand continuity."
),

"079": (
    "RETIRE", "Competitive Intelligence", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Gather lawful intelligence and protect confidential information, but do not intentionally distribute deceptive decoys to manipulate external decision-makers.",
    "Deliberate outward deception is retired."
),

"080": (
    "REFRAME", "Legal / Contracts", "Legal Governance",
    "CANONICAL_REFRAME",
    "Use standardized contractual dispute-resolution, notice, escalation, mediation, arbitration, enforcement, and remedy clauses that are lawful, proportionate, reviewable, and auditable.",
    "Contracts may automate workflow but may not provide unilateral or abusive enforcement."
),

"081": (
    "KEEP", "Automation", "Automation Governance",
    "NONE",
    "Treat frequently repeated manual work as a candidate for standardization or automation when automation is economical, reliable, safe, and maintainable.",
    "Retains the automation heuristic without eliminating necessary human work."
),

"082": (
    "REFRAME", "Capital Allocation", "Finance Governance",
    "CANONICAL_REFRAME",
    "Systematically reinvest an approved portion of profit into capabilities that improve growth, resilience, productivity, customer value, and operating leverage while maintaining reserves and stakeholder obligations.",
    "Not every cent should automatically be reinvested."
),

"083": (
    "REFRAME", "Market Entry", "Strategy",
    "CANONICAL_REFRAME",
    "Enter markets where evidence supports a credible path to durable leadership, attractive economics, defensibility, and customer value rather than requiring mathematical certainty of number-one status.",
    "Ambition is retained without false certainty."
),

"084": (
    "TECHNICAL", "Data Security", "Security Architecture",
    "MODERNIZE",
    "Encrypt sensitive Dalizebo data in transit and at rest, apply strong key management and tenant isolation, and assess third-party infrastructure through security, residency, contractual, and compliance controls.",
    "Specific lattice encryption is not required until standardized and justified."
),

"085": (
    "POLICY", "Corporate Communications", "Executive Governance",
    "NONE",
    "Keep legitimately confidential strategic work private until appropriate release while complying with disclosure, contractual, regulatory, investor, employee, and customer obligations.",
    "Strategic silence becomes disciplined confidentiality."
),

"086": (
    "REFRAME", "Product Strategy", "Product Governance",
    "CANONICAL_REFRAME",
    "Build products with high recurring utility and strong customer value while preserving portability, informed choice, interoperability, cancellation, and avoidance of exploitative dependency.",
    "Customer dependence is not an acceptable design objective."
),

"087": (
    "RETIRE", "Regional Expansion", "Legal & Compliance",
    "PROHIBIT_IMPLEMENTATION",
    "Expansion into new jurisdictions must occur only after appropriate regulatory, tax, employment, privacy, payments, consumer, licensing, and operational readiness.",
    "Expanding before regulators can react is explicitly retired."
),

"088": (
    "REFRAME", "Automation", "Automation Governance",
    "CANONICAL_REFRAME",
    "Automate deterministic, repetitive, scalable work where technology improves quality, cost, speed, or reliability, while retaining human judgment and approval for tasks that materially require it.",
    "Automation-first is retained with human accountability."
),

"089": (
    "REFRAME", "Payments / Treasury", "Finance Governance",
    "CANONICAL_REFRAME",
    "Support Dalizebo-native credits or settlement instruments only where commercially useful and legally compliant, while maintaining interoperable regulated fiat payment options.",
    "DZC may not receive automatic priority over legal tender or regulated payment rails."
),

"090": (
    "REFRAME", "Brand / Community", "Brand Governance",
    "CANONICAL_REFRAME",
    "Build durable loyalty through shared values, reliable products, community participation, service quality, trust, recognition, and consistently delivered customer outcomes.",
    "Loyalty should be earned rather than psychologically engineered."
),

"091": (
    "TECHNICAL", "Engineering", "Engineering Governance",
    "NONE",
    "Maintain a continuous technical-debt program with regular refactoring prioritized by risk, defects, maintainability, security, performance, and business value.",
    "A mandatory weekly rewrite cycle and theoretical 100 percent efficiency are not required."
),

"092": (
    "RETIRE", "Markets", "Risk Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo must not attempt to manufacture or distort market reality. Forecasts and strategy should adapt to observed market conditions and lawful product execution.",
    "Market-bending as an intentional manipulation mechanism is retired."
),

"093": (
    "TECHNICAL", "Engineering / Automation", "Engineering Governance",
    "NONE",
    "Continuously improve feedback loops, workflows, decision rules, observability, and automation through versioned changes, testing, rollback, measurement, and review.",
    "Directly compatible with Algorithm OS and Loop OS governance."
),

"094": (
    "REFRAME", "Talent", "People Governance",
    "CANONICAL_REFRAME",
    "Retain high-value personnel through competitive compensation, meaningful work, development, healthy culture, recognition, succession planning, and lawful retention mechanisms.",
    "Employees and partners are not assets to be insulated from the labor market."
),

"095": (
    "POLICY", "Operations", "Operations Governance",
    "NONE",
    "Use regular operating reviews, automated checks, synchronization rituals, incident reviews, and decision logs at frequencies appropriate to risk and operational need.",
    "The cadence should be evidence-driven rather than universally daily."
),

"096": (
    "REFRAME", "Infrastructure Strategy", "Platform Architecture",
    "CANONICAL_REFRAME",
    "Reduce critical infrastructure dependency through selective ownership, portability, open standards, redundancy, exit plans, and diversified suppliers across hardware, software, energy, and cloud services.",
    "Total ownership is unnecessary where resilient alternatives exist."
),

"097": (
    "TECHNICAL", "Reliability Architecture", "Reliability Engineering",
    "NONE",
    "Identify and eliminate or explicitly manage critical single points of failure through redundancy, failover, backups, dependency isolation, testing, and recovery procedures.",
    "Direct reliability requirement."
),

"098": (
    "REFRAME", "Operational Effectiveness", "Executive Governance",
    "CANONICAL_REFRAME",
    "Design work environments and operating practices that support sustained focus, sound judgment, delegation, recovery, and high-quality executive and team performance.",
    "The system should not depend on maintaining one individual in a permanent peak state."
),

"099": (
    "REFRAME", "Automation / AI", "AI Governance",
    "CANONICAL_REFRAME",
    "Design automated systems capable of processing workloads beyond manual human scale while enforcing bounded autonomy, policy controls, observability, rate limits, approval requirements, and emergency shutdown mechanisms.",
    "Machine-speed operations remain accountable and governed."
),

"100": (
    "REFRAME", "Constitutional Governance", "Pillars OS",
    "CANONICAL_REFRAME",
    "Require platform behavior to remain consistent with the approved constitutional framework while permitting controlled amendments, exceptions, evidence-based review, and measurable business outcomes.",
    "The Codex is a governed constitution rather than an infallible success metric."
),

"101": (
    "POLICY", "Corporate Strategy", "Executive Governance",
    "NONE",
    "Use selective vertical integration where ownership of additional value-chain stages materially improves reliability, economics, quality, strategic resilience, or customer experience.",
    "Full value-chain ownership is not automatically optimal."
),

"102": (
    "POLICY", "Procurement / Partnerships", "Finance Governance",
    "NONE",
    "Use aggregated demand, platform scale, competitive tenders, benchmarks, and long-term relationships to negotiate better commercial terms with external platforms and suppliers.",
    "Scale-based negotiation is legitimate commercial practice."
),

"103": (
    "REFRAME", "Physical Security / Automation", "Security Governance",
    "CANONICAL_REFRAME",
    "Use appropriately authorized sensors and automated systems for detection, inspection, safety, access control, maintenance, and non-harmful protective responses, with human escalation for material actions.",
    "Autonomous protection must remain bounded and safety-oriented."
),

"104": (
    "RETIRE", "Legal / Contracts", "Legal Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Contracts must define rights, obligations, remedies, escalation, and dispute resolution fairly and proportionately. They must not be designed or operated as retaliatory weapons.",
    "Contractual aggression is retired."
),

"105": (
    "REFRAME", "Transparency / Governance", "Executive Governance",
    "CANONICAL_REFRAME",
    "Provide authorized internal stakeholders with strong operational visibility while maintaining appropriate confidentiality, privacy, security, and externally required transparency.",
    "Internal observability does not justify deliberate public opacity."
),

}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid pillar-review.csv")

expected = {f"{i:03d}" for i in range(41, 106)}
found = set()

for row in rows:
    pid = row["pillar_id"].zfill(3)

    if pid not in D:
        continue

    (
        classification,
        domain,
        owner,
        safety,
        canonical,
        notes,
    ) = D[pid]

    row["approved_classification"] = classification
    row["implementation_domain"] = domain
    row["safety_action"] = safety
    row["owner"] = owner
    row["canonical_interpretation"] = canonical
    row["decision_notes"] = notes

    found.add(pid)

missing = expected - found

if missing:
    raise SystemExit(
        "ERROR: Missing Cluster B Pillars: "
        + ", ".join(sorted(missing))
    )

tmp = REVIEW.with_suffix(".tmp")

with tmp.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

tmp.replace(REVIEW)

cluster = [
    row for row in rows
    if 41 <= int(row["pillar_id"]) <= 105
]

counts = Counter(
    row["approved_classification"]
    for row in cluster
)

lines = [
    "# Cluster B Constitutional Reconciliation",
    "",
    "## Source",
    "",
    "Cluster B: Hegemony, Capture & Narrative Engineering (041–105).",
    "",
    "The original source statements remain unchanged in the source registry.",
    "",
    "## Classification Summary",
    "",
]

for classification in [
    "KEEP",
    "POLICY",
    "TECHNICAL",
    "REFRAME",
    "R&D",
    "RETIRE",
]:
    lines.append(
        f"- {classification}: {counts.get(classification, 0)}"
    )

lines.extend(["", "## Decisions", ""])

for row in cluster:
    lines.extend([
        f"### Pillar {row['pillar_id']} — {row['name']}",
        "",
        f"**Classification:** {row['approved_classification']}",
        "",
        f"**Domain:** {row['implementation_domain']}",
        "",
        f"**Owner:** {row['owner']}",
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

print("OK: Pillars 041–105 reconciled.")
for key in sorted(counts):
    print(f"{key}: {counts[key]}")

print(f"Report: {REPORT}")
