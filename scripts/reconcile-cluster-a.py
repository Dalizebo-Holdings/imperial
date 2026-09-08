#!/usr/bin/env python3

from pathlib import Path
import csv
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent

REVIEW = (
    ROOT
    / "constitution"
    / "reconciliation"
    / "review"
    / "pillar-review.csv"
)

REPORT = (
    ROOT
    / "constitution"
    / "reconciliation"
    / "reports"
    / "CLUSTER_A.md"
)

if not REVIEW.exists():
    raise SystemExit(
        "ERROR: pillar-review.csv missing. Run Phase 20 first."
    )

# classification, domain, owner, safety_action,
# canonical_interpretation, decision_notes

D = {

"001": (
    "POLICY",
    "Finance / Treasury",
    "Finance Governance",
    "NONE",
    "Use 40/40/20 as a configurable treasury allocation target subject to cash-flow requirements, legal obligations, risk limits, and approved exceptions.",
    "Preserves the allocation concept without treating a fixed ratio as universally mandatory."
),

"002": (
    "KEEP",
    "Strategy",
    "Executive Governance",
    "NONE",
    "Prefer differentiated, evidence-based market-entry strategies over mechanically copying incumbent competitive routes.",
    "Strategic differentiation is retained."
),

"003": (
    "REFRAME",
    "Finance / Strategy",
    "Capital Allocation",
    "CANONICAL_REFRAME",
    "Deploy capital to reduce customer and operational friction and build lawful strategic capabilities. Capital must not be used for coercion, sabotage, or unlawful exclusion.",
    "Replaces adversarial weaponization language with disciplined strategic capital deployment."
),

"004": (
    "KEEP",
    "Platform / Capital",
    "Platform Strategy",
    "NONE",
    "Compound reusable software, data, distribution, operating knowledge, and network effects through disciplined reinvestment.",
    "Directly compatible with the Dalizebo platform model."
),

"005": (
    "POLICY",
    "Treasury / Risk",
    "Treasury",
    "NONE",
    "Maintain sufficient liquidity and risk reserves to preserve optionality and pursue approved distressed or strategic opportunities.",
    "Liquidity principle retained under formal risk governance."
),

"006": (
    "POLICY",
    "Treasury / Assets",
    "Capital Allocation",
    "NONE",
    "Diversify retained earnings into productive physical assets only after liquidity, legal, environmental, valuation, and investment due diligence.",
    "Physical asset diversification retained with investment controls."
),

"007": (
    "POLICY",
    "Risk",
    "Risk Governance",
    "NONE",
    "Prefer opportunities with explicitly bounded downside and asymmetric upside, supported by scenario analysis, exposure limits, and exit criteria.",
    "Makes asymmetric investing measurable and governed."
),

"008": (
    "POLICY",
    "Finance / Audit",
    "Finance Governance",
    "NONE",
    "Protect strategic reserves through budget controls, traceable expenditure, periodic ROI review, reconciliation, and independent audit evidence.",
    "Zero-leakage becomes auditable financial governance."
),

"009": (
    "REFRAME",
    "Platform / Procurement",
    "Platform Economics",
    "CANONICAL_REFRAME",
    "Reduce avoidable intermediary costs through direct integrations, owned capabilities, competitive procurement, and automation without bypassing legally or operationally required intermediaries.",
    "Vendor independence is retained without blanket middleman bypass."
),

"010": (
    "REFRAME",
    "Markets / Finance",
    "Risk Governance",
    "CANONICAL_REFRAME",
    "Identify lawful market, timing, pricing, and geographic arbitrage opportunities subject to tax, regulatory, liquidity, and risk controls.",
    "Arbitrage remains legitimate only within applicable law and risk policy."
),

"011": (
    "REFRAME",
    "Corporate Strategy",
    "Executive Governance",
    "CANONICAL_REFRAME",
    "Each new subsidiary should establish a lawful and defensible advantage through technology, service, brand, distribution, data, efficiency, or approved regulatory capability, with early validation.",
    "Regulatory moat language is constrained to legitimate competitive advantage."
),

"012": (
    "POLICY",
    "Capital Allocation",
    "Finance Governance",
    "NONE",
    "Prioritize reinvestment into validated automation and growth opportunities while maintaining solvency, contractual obligations, reserves, and approved distributions.",
    "Recursive reinvestment retained with financial safeguards."
),

"013": (
    "REFRAME",
    "Finance / Tax",
    "Finance Governance",
    "CANONICAL_REFRAME",
    "Use documented arm's-length director or intercompany lending only where legally, tax, accounting, exchange-control, and governance compliant.",
    "The platform must never promise or engineer guaranteed zero-tax treatment."
),

"014": (
    "REFRAME",
    "Treasury",
    "Treasury",
    "CANONICAL_REFRAME",
    "Diversify material ZAR exposure using approved and regulated treasury instruments. Any Dalizebo Credits mechanism must satisfy applicable payments, securities, tax, consumer, and financial regulation before production use.",
    "Removes absolute currency decoupling while retaining treasury resilience."
),

"015": (
    "POLICY",
    "Corporate Development",
    "Executive Governance",
    "NONE",
    "Prefer ownership structures that improve long-term alignment and value creation where justified by valuation, governance, risk, and diversification considerations.",
    "Equity remains a strategic preference rather than an absolute rule."
),

"016": (
    "POLICY",
    "Supply Chain / Infrastructure",
    "Operations Governance",
    "NONE",
    "Reduce dependency on strategically critical inputs using ownership, long-term contracts, redundancy, alternative suppliers, or trusted infrastructure.",
    "Direct control becomes dependency-risk management."
),

"017": (
    "REFRAME",
    "Platform Strategy",
    "Platform Governance",
    "CANONICAL_REFRAME",
    "Build interoperable platform infrastructure that creates recurring value through useful services, transaction rails, integrations, and fair commercial access.",
    "Retains platform economics while rejecting coercive toll-gate behavior."
),

"018": (
    "REFRAME",
    "Strategy / Product",
    "Platform Strategy",
    "CANONICAL_REFRAME",
    "Engineer defensible advantages through superior products, automation, data, logistics, customer experience, distribution, and execution rather than unlawful exclusion.",
    "Unfair advantage becomes lawful defensibility."
),

"019": (
    "KEEP",
    "Architecture",
    "Platform Architecture",
    "NONE",
    "Design systems so output and transaction capacity can scale materially faster than manual headcount through automation, standardization, reusable services, and software leverage.",
    "Directly supports SaaS and BaaS scalability."
),

"020": (
    "REFRAME",
    "Growth Governance",
    "Executive Governance",
    "CANONICAL_REFRAME",
    "Use 40 percent annual growth as an aspirational benchmark where commercially appropriate, with sustainable risk-adjusted growth and unit economics taking precedence over arbitrary expansion.",
    "A fixed growth mandate must not force unsafe or uneconomic decisions."
),

"021": (
    "TECHNICAL",
    "Security",
    "Security Architecture",
    "MODERNIZE",
    "Apply zero-trust architecture, hardened baselines, least privilege, segmentation, secrets management, continuous monitoring, vulnerability management, and incident response across every production node.",
    "Retains the zero-trust intent while replacing black-site terminology."
),

"022": (
    "TECHNICAL",
    "Audit / DevSecOps",
    "Security Engineering",
    "NONE",
    "Perform scheduled source-control, ledger, dependency, backup, configuration, and integrity audits at least monthly where justified by system risk.",
    "Turns ritual audits into automated evidence-producing controls."
),

"023": (
    "REFRAME",
    "R&D / Security",
    "R&D Governance",
    "CANONICAL_REFRAME",
    "Protect pre-release research using lawful confidentiality, access controls, compartmentalization, trade-secret practices, staged disclosure, and responsible release management.",
    "Confidential R&D is retained without deceptive competitor operations."
),

"024": (
    "REFRAME",
    "Data / Intelligence",
    "Data Governance",
    "CANONICAL_REFRAME",
    "Build regional intelligence pipelines from licensed, public, contractual, or consented sources with provenance, purpose limitation, privacy, retention, and access controls.",
    "Information advantage must come from lawful intelligence collection."
),

"025": (
    "POLICY",
    "Information Management",
    "Knowledge Governance",
    "NONE",
    "Prioritize information using explicit relevance, quality, confidence, strategic value, and timeliness criteria while retaining evidence required for governance and compliance.",
    "Converts signal filtering into governed information prioritization."
),

"026": (
    "REFRAME",
    "Security / Compliance",
    "Security Operations",
    "CANONICAL_REFRAME",
    "Detect and respond to unauthorized access, espionage, insider threats, data exfiltration, and competitive-intelligence risks through lawful defensive security and incident-response controls. Regulatory engagement must remain transparent and compliant.",
    "Regulators are not adversaries to be neutralized."
),

"027": (
    "REFRAME",
    "Legal / Treasury",
    "Legal & Finance Governance",
    "CANONICAL_REFRAME",
    "Use lawful multi-jurisdiction structures for operational resilience and asset diversification only with tax, AML, exchange-control, sanctions, reporting, beneficial-ownership, and disclosure compliance.",
    "Jurisdiction diversification must never become regulatory or tax evasion."
),

"028": (
    "TECHNICAL",
    "Cryptography",
    "Security Architecture",
    "MODERNIZE",
    "Use modern authenticated encryption and cryptographic agility for sensitive communications. Adopt standardized post-quantum algorithms when appropriate, and use ephemeral communications only where retention obligations permit.",
    "Avoids prematurely mandating a specific experimental cryptographic mechanism."
),

"029": (
    "RETIRE",
    "Competitive Strategy",
    "Executive Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Do not fabricate strategic pivots or deliberately mislead competitors into resource-wasting activity. Legitimate confidentiality, positioning, and non-disclosure remain permitted.",
    "The original decoy-operation mechanism depends on intentional deception and is not an approved Dalizebo capability."
),

"030": (
    "REFRAME",
    "Backup / Resilience",
    "Reliability Engineering",
    "CANONICAL_REFRAME",
    "Maintain geographically separated, encrypted, tested, and recoverable backups using established redundancy principles. Off-world archival remains optional Frontier R&D and must not be a production dependency.",
    "Preserves redundancy while separating lunar storage into research."
),

"031": (
    "TECHNICAL",
    "Security",
    "Security Engineering",
    "NONE",
    "Continuously automate vulnerability scanning, dependency and SBOM analysis, secret detection, exposure monitoring, configuration review, and social-engineering defenses using risk-based remediation deadlines.",
    "Directly implementable security control."
),

"032": (
    "REFRAME",
    "Security / Legal",
    "Security & Legal",
    "CANONICAL_REFRAME",
    "Protect intellectual property and confidential logic using evidence preservation, credential revocation, containment, contractual enforcement, legal remedies, and proportionate incident response.",
    "No retaliatory sabotage or unlawful commercial strike is permitted."
),

"033": (
    "REFRAME",
    "Security / Governance",
    "Security Governance",
    "CANONICAL_REFRAME",
    "Reduce social-engineering risk through verified communication channels, awareness training, separation of duties, approval gates, protected executive contact paths, and identity verification.",
    "Security does not require blanket isolation from legitimate public or customer contact."
),

"034": (
    "TECHNICAL",
    "Networking",
    "Infrastructure Engineering",
    "MODERNIZE",
    "Design resilient connectivity using redundant ISPs, private links, VPNs, SD-WAN, secure mesh networking, or equivalent technologies where justified by availability, security, and cost.",
    "Network sovereignty becomes resilient vendor-independent connectivity."
),

"035": (
    "TECHNICAL",
    "Physical Security",
    "Security Operations",
    "NONE",
    "Protect critical facilities and energy infrastructure using layered physical access controls, surveillance where lawful, environmental monitoring, inventory controls, safety procedures, and incident response.",
    "Directly implementable physical-security requirement."
),

"036": (
    "TECHNICAL",
    "Reliability / DR",
    "Reliability Engineering",
    "NONE",
    "Run regular tabletop, chaos, continuity, and disaster-recovery exercises with defined scenarios, recovery objectives, evidence, lessons learned, and corrective actions.",
    "The extreme failure assumption becomes a measurable resilience-testing program."
),

"037": (
    "REFRAME",
    "Continuity / People",
    "Executive Governance",
    "CANONICAL_REFRAME",
    "Protect leadership and critical-team sustainability through workload management, delegation, succession, continuity planning, reasonable wellbeing practices, and elimination of single-person operational dependencies.",
    "Institutional continuity takes precedence over dependence on one biological node."
),

"038": (
    "REFRAME",
    "Knowledge / Continuity",
    "Knowledge Governance",
    "CANONICAL_REFRAME",
    "Preserve strategic continuity through versioned decision records, architecture records, runbooks, knowledge bases, succession documentation, and governed AI assistance.",
    "AI systems may preserve institutional knowledge but must not be treated as literal replicas of an individual."
),

"039": (
    "TECHNICAL",
    "Audit",
    "Security Architecture",
    "MODERNIZE",
    "Maintain append-only or tamper-evident strategic audit records with strong access control, cryptographic integrity, retention policy, timestamps, and independent verification.",
    "Blockchain is optional and should be used only where it provides demonstrated value."
),

"040": (
    "REFRAME",
    "Security / Incident Response",
    "Security Operations",
    "CANONICAL_REFRAME",
    "On unauthorized access, isolate affected systems, revoke sessions and credentials, rotate secrets, preserve forensic evidence, investigate scope, restore trusted service, and document the incident.",
    "Destructive wiping requires explicit authorization and incident policy and must never destroy required forensic or legal evidence."
),

}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: Invalid reconciliation CSV.")

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

expected = {f"{i:03d}" for i in range(1, 41)}

missing = expected - found

if missing:
    raise SystemExit(
        "ERROR: Missing Cluster A Pillars: "
        + ", ".join(sorted(missing))
    )

# Atomic-ish rewrite through temporary file.
tmp = REVIEW.with_suffix(".tmp")

with tmp.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

tmp.replace(REVIEW)

# Generate canonical human-readable report.
cluster = [
    row for row in rows
    if 1 <= int(row["pillar_id"]) <= 40
]

counts = Counter(
    row["approved_classification"]
    for row in cluster
)

lines = [
    "# Cluster A Constitutional Reconciliation",
    "",
    "## Source",
    "",
    "Cluster A: Fiscal Weaponization & Capital Hardening (001–040).",
    "",
    "Original source statements remain preserved in the canonical source registry.",
    "",
    "## Classification Summary",
    "",
]

for name in [
    "KEEP",
    "POLICY",
    "TECHNICAL",
    "REFRAME",
    "R&D",
    "RETIRE",
]:
    lines.append(f"- {name}: {counts.get(name, 0)}")

lines.extend([
    "",
    "## Decisions",
    "",
])

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

print("OK: Pillars 001–040 reconciled.")

for key in sorted(counts):
    print(f"{key}: {counts[key]}")

print(f"Report: {REPORT}")
