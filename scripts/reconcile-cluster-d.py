#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "constitution/reconciliation/review/pillar-review.csv"
REPORT = ROOT / "constitution/reconciliation/reports/CLUSTER_D.md"

D = {

"151": (
    "REFRAME", "AI / Institutional Knowledge", "AI Governance",
    "CANONICAL_REFRAME",
    "Build governed AI systems that capture documented decision principles, institutional knowledge, preferences, and historical reasoning without claiming to reproduce an individual person with measurable psychological fidelity.",
    "Digital Lucas becomes institutional decision-support rather than a literal cognitive replica."
),

"152": (
    "KEEP", "Knowledge Management", "Knowledge Governance",
    "NONE",
    "Record significant strategic failures, assumptions, outcomes, corrective actions, and lessons as searchable institutional learning assets.",
    "Direct organizational-learning principle."
),

"153": (
    "REFRAME", "Leadership Sustainability", "People Governance",
    "CANONICAL_REFRAME",
    "Use sustainable workload design, delegation, recovery, focus practices, health-supportive working conditions, and succession planning to reduce burnout and preserve decision quality.",
    "Peak cognition must not depend on unrealistic permanent performance states."
),

"154": (
    "REFRAME", "Communications / Media Literacy", "Marketing Governance",
    "CANONICAL_REFRAME",
    "Protect customers and communities from misinformation through accurate communications, media literacy, transparent corrections, product education, and evidence-based claims.",
    "Competitor messaging is not treated as a mind-virus requiring manipulation."
),

"155": (
    "REFRAME", "Language / Knowledge", "Knowledge Governance",
    "CANONICAL_REFRAME",
    "Support Sepedi as a first-class technical and organizational language alongside other required languages, with consistent terminology and accessible translations.",
    "Language becomes an inclusion and institutional-knowledge capability rather than dominance."
),

"156": (
    "REFRAME", "Organizational Learning", "Executive Governance",
    "CANONICAL_REFRAME",
    "Treat external work, projects, partnerships, and professional experience as opportunities to acquire lawful knowledge, relationships, capabilities, and reusable institutional learning.",
    "External people and time are not resources to be extracted."
),

"157": (
    "REFRAME", "Succession", "Corporate Governance",
    "CANONICAL_REFRAME",
    "Maintain documented succession, delegation, emergency authority, key-person continuity, and access-transfer procedures that activate through governed triggers and authorized human oversight.",
    "Authority must not transfer solely through an autonomous biological-latency trigger."
),

"158": (
    "RETIRE", "Brand / Culture", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo may build a durable mission and institutional identity, but must not engineer narratives that encourage people to sacrifice their lives or safety for the organization.",
    "Extreme personal sacrifice is not an approved organizational objective."
),

"159": (
    "POLICY", "Strategy / Markets", "Risk Governance",
    "NONE",
    "Study cognitive and market biases when evaluating investments, forecasts, negotiations, and strategic assumptions, while using risk limits and evidence-based decision processes.",
    "Behavioral insight remains legitimate when not used for coercive manipulation."
),

"160": (
    "TECHNICAL", "Information Security", "Security Architecture",
    "MODERNIZE",
    "Protect sensitive organizational information using classification, least privilege, authenticated encryption, key management, secure storage, retention controls, and cryptographic agility.",
    "Specific lattice encryption is not mandatory until standardized and justified."
),

"161": (
    "REFRAME", "Privacy / Incident Response", "Security Governance",
    "CANONICAL_REFRAME",
    "Maintain rapid procedures to reduce unnecessary public exposure, revoke compromised accounts, remove obsolete content, protect executive privacy, and respond to active security incidents while preserving legal and audit obligations.",
    "Digital privacy must not become concealment from lawful accountability."
),

"162": (
    "REFRAME", "AI Learning", "AI Governance",
    "CANONICAL_REFRAME",
    "Improve AI decision-support systems using approved decision records, feedback, evaluations, curated training data, and versioned model updates rather than continuously copying an executive's behavior directly into model weights.",
    "AI learning requires controlled datasets, evaluation, approval, and rollback."
),

"163": (
    "KEEP", "Strategy / Innovation", "Executive Governance",
    "NONE",
    "Continuously challenge incumbent assumptions and seek business-model, technology, distribution, or operational innovations that redefine competitive boundaries.",
    "Strategic innovation is retained."
),

"164": (
    "RETIRE", "Reputation / Communications", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo must not manufacture false expertise signals. Authority must come from verified credentials, published work, demonstrated competence, customer outcomes, research, and accountable leadership.",
    "Fabricated authority signals are retired."
),

"165": (
    "REFRAME", "Product Analytics", "Data Governance",
    "CANONICAL_REFRAME",
    "Measure customer behavior using proportionate analytics, consent and privacy controls where required, data minimization, aggregate reporting, experimentation governance, and clear customer benefit.",
    "Behavioral data must not feed manipulative mind-virus systems."
),

"166": (
    "REFRAME", "Talent", "People Governance",
    "CANONICAL_REFRAME",
    "Select high-responsibility partners and leaders using resilience, competence, integrity, judgment, performance, collaboration, and alignment with documented organizational values.",
    "Talent selection must use objective professional criteria rather than ideological labels."
),

"167": (
    "KEEP", "Automation / Productivity", "Automation Governance",
    "NONE",
    "Automate repetitive and low-value cognitive work where doing so preserves human attention for judgment, creativity, relationships, strategy, and high-value execution.",
    "Direct productivity principle."
),

"168": (
    "KEEP", "Knowledge Architecture", "Knowledge Governance",
    "NONE",
    "Maintain precise shared terminology, definitions, schemas, naming standards, and decision language to reduce ambiguity and reasoning errors.",
    "Direct knowledge-governance principle."
),

"169": (
    "POLICY", "Strategy / Knowledge", "Executive Governance",
    "NONE",
    "Use historical cases and previous Dalizebo outcomes as reference patterns while explicitly testing whether assumptions and conditions still apply.",
    "Historical analogy should inform rather than mechanically determine current strategy."
),

"170": (
    "REFRAME", "Education", "People Governance",
    "CANONICAL_REFRAME",
    "Use Dalizebo University as the authoritative source for approved internal standards and training while encouraging external research, professional education, independent verification, and evidence-based challenge.",
    "No institution should be the exclusive source of truth."
),

"171": (
    "RETIRE", "Communications", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo must not intentionally distort public perception to manufacture strategic openings. Communications must remain materially truthful and attributable.",
    "Reality distortion is retired."
),

"172": (
    "KEEP", "Long-Term Strategy", "Executive Governance",
    "NONE",
    "Evaluate major strategic decisions against long-term consequences, optionality, resilience, stewardship, and intergenerational effects.",
    "The 100-year perspective is retained as long-horizon governance."
),

"173": (
    "REFRAME", "Decision Systems", "Algorithm OS",
    "CANONICAL_REFRAME",
    "Formalize repeatable decisions into explicit rules, models, scoring systems, or algorithms where doing so improves consistency and auditability, while retaining human judgment for ambiguity and material exceptions.",
    "Not every decision should be reduced to a formula."
),

"174": (
    "REFRAME", "Product Marketing", "Marketing Governance",
    "CANONICAL_REFRAME",
    "Build market understanding before launches through research, education, thought leadership, demonstrations, previews, community engagement, and truthful problem framing.",
    "Cognitive seeding becomes transparent category education."
),

"175": (
    "TECHNICAL", "AI Security", "Security Architecture",
    "NONE",
    "Protect institutional AI systems through strong identity, authorization, tenant isolation, model and data integrity, secret management, signed artifacts where appropriate, monitoring, recovery, and administrative controls.",
    "Direct AI security requirement."
),

"176": (
    "REFRAME", "Brand / Institutional Identity", "Brand Governance",
    "CANONICAL_REFRAME",
    "Develop an institutional Dalizebo Architect identity that represents documented principles, standards, design philosophy, and long-term mission independently of any single individual.",
    "Founder identity becomes institutional symbolism rather than personality dependence."
),

"177": (
    "POLICY", "Market Intelligence", "Strategy",
    "NONE",
    "Develop high-quality leading indicators and causal understanding so Dalizebo can identify important market changes before they become broadly obvious.",
    "Information superiority comes from lawful research and analytical quality."
),

"178": (
    "KEEP", "Leadership / Resilience", "Executive Governance",
    "NONE",
    "Maintain disciplined reasoning, decision records, scenario planning, escalation processes, and operating continuity under market, political, operational, or financial pressure.",
    "Direct resilience principle."
),

"179": (
    "REFRAME", "Brand / Terminology", "Brand Governance",
    "CANONICAL_REFRAME",
    "Develop distinctive terminology and conceptual frameworks that strengthen Dalizebo's intellectual identity while remaining understandable, documented, and usable by customers and partners.",
    "Semantic differentiation should not intentionally lock outsiders out."
),

"180": (
    "REFRAME", "AI Strategy", "AI Governance",
    "CANONICAL_REFRAME",
    "Maintain organizational control over critical AI strategy through provider abstraction, model evaluation, data governance, human accountability, portability, and the ability to change providers.",
    "Third-party AI may assist but must not become an uncontrolled strategic authority."
),

"181": (
    "RETIRE", "Human Interaction", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo must not treat people as programmable interfaces. Human relationships should be handled through ethical communication, negotiation, service, leadership, and consent-based interaction.",
    "Human social engineering as an operational control system is retired."
),

"182": (
    "KEEP", "Business Continuity", "Executive Governance",
    "NONE",
    "Design strategy, operations, infrastructure, and organizational knowledge so critical capabilities persist through adverse external conditions.",
    "Direct strategic-persistence principle."
),

"183": (
    "POLICY", "Brand / Communications", "Marketing Governance",
    "NONE",
    "Allow messaging, terminology, creative assets, and campaigns to evolve with audience and context while preserving factual accuracy and the approved core brand position.",
    "Message evolution is retained without manipulative memetic framing."
),

"184": (
    "REFRAME", "Customer / People Value", "Executive Governance",
    "CANONICAL_REFRAME",
    "Build products and employment systems that create practical value by addressing meaningful customer, employee, partner, and community needs without intentionally creating dependency.",
    "Basic-needs support becomes stakeholder value rather than control."
),

"185": (
    "REFRAME", "Institutional Governance", "Executive Governance",
    "CANONICAL_REFRAME",
    "Transfer organizational trust from dependence on individual leaders toward reliable institutions, documented governance, transparent systems, repeatable processes, accountable teams, and audited platform controls.",
    "This is a central institutionalization objective."
),

"186": (
    "POLICY", "Decision Governance", "Executive Governance",
    "NONE",
    "Periodically review material decisions for emotional bias, confirmation bias, conflicts, unsupported assumptions, missing evidence, and outcome quality.",
    "Cognitive auditing becomes structured decision review."
),

"187": (
    "KEEP", "R&D / Validation", "R&D Governance",
    "NONE",
    "Validate material technical and operational hypotheses through controlled prototypes, pilots, simulations, laboratories, or test environments before large-scale deployment.",
    "Direct validation principle."
),

"188": (
    "REFRAME", "Brand / Reputation", "Brand Governance",
    "CANONICAL_REFRAME",
    "Strengthen institutional reputation through consistent evidence, reliable delivery, transparency, correction of errors, documented history, quality, and trustworthy communications.",
    "A brand story must remain challengeable and fact-based rather than unassailable."
),

"189": (
    "REFRAME", "Knowledge Management", "Knowledge Governance",
    "CANONICAL_REFRAME",
    "Capture strategically valuable insights from authorized meetings, decisions, notes, research, retrospectives, and leadership reflections with appropriate consent, classification, retention, and privacy controls.",
    "Not every private thought should automatically become organizational data."
),

"190": (
    "TECHNICAL", "Decision Orchestration", "Algorithm OS",
    "NONE",
    "Design decision workflows so required context, policy checks, approvals, execution, events, and audit move efficiently across platform layers while preserving necessary control gates.",
    "Zero friction does not mean zero governance."
),

"191": (
    "POLICY", "Treasury / Succession", "Finance Governance",
    "NONE",
    "Structure long-term capital preservation, governance, ownership, diversification, succession, and estate planning to support multi-generational institutional continuity.",
    "Intergenerational wealth preservation remains subject to law and professional governance."
),

"192": (
    "RETIRE", "Competitive Intelligence", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo may protect confidential strategy and gather lawful intelligence but must not intentionally feed competitors false or deceptive information.",
    "Competitive noise operations are retired."
),

"193": (
    "REFRAME", "Strategy / Thought Leadership", "Executive Governance",
    "CANONICAL_REFRAME",
    "Build regional strategic leadership through superior research, technical capability, market understanding, standards participation, publications, partnerships, and execution.",
    "Cognitive dominance becomes legitimate intellectual and strategic leadership."
),

"194": (
    "REFRAME", "Localization / Communications", "People Governance",
    "CANONICAL_REFRAME",
    "Use different languages and registers to improve comprehension, cultural relevance, accessibility, and professional context without using language to manufacture artificial social status hierarchies.",
    "Multilingual communication should serve the audience."
),

"195": (
    "RETIRE", "Founder Brand", "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Dalizebo must not protect a founder legend through deception or suppression of ordinary human reality. Leadership reputation should remain grounded in documented work and accountable conduct.",
    "Personality-cult shielding is retired."
),

"196": (
    "REFRAME", "Brand Marketing", "Marketing Governance",
    "CANONICAL_REFRAME",
    "Increase brand salience through product quality, consistent identity, useful content, distribution, customer experience, community, partnerships, and responsible advertising.",
    "Brand awareness may be optimized without psychological saturation tactics."
),

"197": (
    "KEEP", "Strategy", "Executive Governance",
    "NONE",
    "Allow tactics, implementation methods, products, and operating plans to change rapidly when evidence changes while preserving approved constitutional principles.",
    "Direct strategy-versus-principles distinction."
),

"198": (
    "REFRAME", "Succession / Knowledge", "Knowledge Governance",
    "CANONICAL_REFRAME",
    "Document leadership principles, architecture philosophy, decision frameworks, institutional history, operating lessons, and governance practices so future leaders can learn from and improve them.",
    "Cognitive legacy becomes documented institutional knowledge."
),

"199": (
    "REFRAME", "Decision Intelligence", "AI Governance",
    "CANONICAL_REFRAME",
    "Combine experienced human judgment with data, models, simulations, AI assistance, explicit assumptions, and measurable feedback when making material decisions.",
    "Human intuition and algorithmic analysis should complement rather than replace one another."
),

"200": (
    "REFRAME", "Constitutional Governance", "Executive Governance",
    "CANONICAL_REFRAME",
    "The Dalizebo system exists to execute the approved organizational mission and constitutional strategy through accountable governance rather than the unrestricted will of any single individual.",
    "Founder vision is preserved as institutional mission subject to governance."
),

}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid pillar-review.csv")

expected = {f"{i:03d}" for i in range(151, 201)}
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
        "ERROR: Missing Cluster D Pillars: "
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
    if 151 <= int(row["pillar_id"]) <= 200
]

counts = Counter(
    row["approved_classification"]
    for row in cluster
)

lines = [
    "# Cluster D Constitutional Reconciliation",
    "",
    "## Source",
    "",
    "Cluster D: Cognitive Dominance & Succession (151–200).",
    "",
    "Original source statements remain unchanged.",
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

print("OK: Pillars 151–200 reconciled.")

for key in sorted(counts):
    print(f"{key}: {counts[key]}")

print(f"Report: {REPORT}")
