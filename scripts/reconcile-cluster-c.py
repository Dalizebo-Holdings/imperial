#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "constitution/reconciliation/review/pillar-review.csv"
REPORT = ROOT / "constitution/reconciliation/reports/CLUSTER_C.md"

# classification, domain, owner, safety_action,
# canonical_interpretation, decision_notes

D = {

"106": (
    "REFRAME",
    "Energy Infrastructure",
    "Infrastructure Governance",
    "CANONICAL_REFRAME",
    "Increase energy resilience through solar generation, storage, grid integration, backup power, efficiency, and diversified energy supply where economically justified.",
    "Energy ownership becomes resilience rather than an absolute requirement."
),

"107": (
    "R&D",
    "Geospatial / Resource Intelligence",
    "R&D Governance",
    "RESEARCH_BOUNDARY",
    "Research lawful remote sensing, satellite imagery, geological datasets, and geospatial analytics for resource exploration subject to licensing, environmental, data-access, and mineral-rights requirements.",
    "Orbital resource detection remains a governed research capability."
),

"108": (
    "REFRAME",
    "Logistics",
    "Operations Governance",
    "CANONICAL_REFRAME",
    "Build strong control over last-mile service quality through owned infrastructure, trusted partners, standardized APIs, tracking, SLAs, and operational redundancy.",
    "Dalizebo does not need to own every physical delivery component."
),

"109": (
    "RETIRE",
    "Infrastructure",
    "Legal & Compliance",
    "PROHIBIT_IMPLEMENTATION",
    "Distributed physical nodes may improve availability and access but must remain properly registered, permitted, documented, and visible to authorized regulators and operators.",
    "Infrastructure deliberately designed to evade regulatory tracking is retired."
),

"110": (
    "REFRAME",
    "Regional Logistics",
    "Operations Governance",
    "CANONICAL_REFRAME",
    "Develop resilient access to strategic SADC transport corridors through logistics partnerships, routing intelligence, warehousing, digital infrastructure, and commercial agreements.",
    "Chokepoint control becomes lawful corridor resilience."
),

"111": (
    "POLICY",
    "Water Resilience",
    "Infrastructure Governance",
    "NONE",
    "Maintain reliable water access for critical facilities through lawful boreholes, municipal supply, storage, recycling, efficiency, and alternative sources subject to permits and environmental limits.",
    "Water independence becomes responsible supply resilience."
),

"112": (
    "REFRAME",
    "Energy Optimization",
    "Energy Governance",
    "CANONICAL_REFRAME",
    "Route surplus energy toward economically justified storage, grid export, productive compute, industrial processes, or other approved uses based on economics and energy policy.",
    "No mandatory conversion to cryptocurrency or hash-rate is required."
),

"113": (
    "POLICY",
    "Circular Economy",
    "Operations Governance",
    "NONE",
    "Recover reusable components and strategic materials from electronic waste through safe, licensed recycling and refining processes where economically and environmentally viable.",
    "Supports circular supply-chain resilience."
),

"114": (
    "TECHNICAL",
    "Construction",
    "Infrastructure Engineering",
    "NONE",
    "Use modular, prefabricated, standardized, or additive-manufacturing construction where it improves speed, repeatability, cost, maintainability, and expansion.",
    "Direct engineering principle."
),

"115": (
    "REFRAME",
    "Land Strategy",
    "Property Governance",
    "CANONICAL_REFRAME",
    "Use lawful public planning information, infrastructure forecasts, due diligence, valuations, and strategic requirements when acquiring land near expected development corridors.",
    "Land strategy must not depend on confidential or improperly obtained planning information."
),

"116": (
    "REFRAME",
    "Physical Resilience",
    "Infrastructure Engineering",
    "CANONICAL_REFRAME",
    "Place critical infrastructure underground, hardened, distributed, or otherwise protected where threat models, environmental conditions, continuity requirements, and economics justify it.",
    "Sub-surface deployment becomes risk-based infrastructure hardening."
),

"117": (
    "R&D",
    "Hardware",
    "R&D Governance",
    "RESEARCH_BOUNDARY",
    "Develop increasing capability to design, prototype, repair, integrate, and where economically justified manufacture strategic sensors, actuators, and hardware components.",
    "Hardware self-sufficiency is a long-term capability rather than an absolute requirement."
),

"118": (
    "RETIRE",
    "Physical Infrastructure",
    "Security Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Physical facilities may use ordinary privacy, thermal efficiency, shielding, and security design, but must not be intentionally concealed from lawful satellite, aviation, regulatory, or safety oversight.",
    "Detection-evasion architecture is retired."
),

"119": (
    "POLICY",
    "Supply Chain",
    "Operations Governance",
    "NONE",
    "Maintain risk-based strategic inventories of critical materials where supply disruption, lead times, concentration, or geopolitical risk justify reserves.",
    "Strategic inventory replaces speculative hoarding."
),

"120": (
    "R&D",
    "Thermal Engineering",
    "R&D Governance",
    "RESEARCH_BOUNDARY",
    "Research advanced cooling approaches including liquid cooling, geothermal, sub-surface, ambient, heat recovery, and other high-efficiency thermal systems.",
    "Deep-sea or other unconventional cooling requires separate technical and environmental validation."
),

"121": (
    "REFRAME",
    "Logistics Resilience",
    "Operations Governance",
    "CANONICAL_REFRAME",
    "Maintain multiple authorized logistics routes and failover corridors, with sensitive routing information protected according to operational-security requirements.",
    "Ghost routes become documented contingency routes."
),

"122": (
    "TECHNICAL",
    "Robotics",
    "Hardware Engineering",
    "NONE",
    "Calibrate safety-critical sensors and actuators according to defined schedules, tolerances, diagnostics, telemetry, and maintenance requirements.",
    "Calibration frequency must match actual risk and equipment requirements."
),

"123": (
    "REFRAME",
    "Energy Networks",
    "Infrastructure Governance",
    "CANONICAL_REFRAME",
    "Develop cooperative solar and microgrid infrastructure that improves resilience and creates mutually beneficial energy relationships with customers and partners.",
    "Energy infrastructure must not intentionally create coercive dependency."
),

"124": (
    "TECHNICAL",
    "Property Records",
    "Data Governance",
    "MODERNIZE",
    "Maintain authenticated internal references and tamper-evident records for property ownership while treating authoritative government land registries and legally recognized records as controlling sources.",
    "Blockchain may supplement records but cannot replace lawful title systems."
),

"125": (
    "REFRAME",
    "Mining Automation",
    "Operations Governance",
    "CANONICAL_REFRAME",
    "Progressively automate mining and industrial operations where permitted and where safety, environmental protection, workforce transition, economics, reliability, and regulation support automation.",
    "A mandatory twelve-month autonomous-production deadline is removed."
),

"126": (
    "TECHNICAL",
    "Facility Safety",
    "Safety Engineering",
    "NONE",
    "Protect controlled facilities using appropriate filtration, ventilation, hygiene, monitoring, biosafety procedures, occupational-health controls, and emergency response.",
    "Direct facility-safety requirement."
),

"127": (
    "TECHNICAL",
    "Supply Chain",
    "Data Governance",
    "NONE",
    "Provide end-to-end supply-chain traceability for material provenance, custody, location, processing, inventory, quality, and compliance using proportionate data collection.",
    "Traceability must respect privacy, confidentiality, and data minimization."
),

"128": (
    "TECHNICAL",
    "Physical Security",
    "Security Governance",
    "SAFETY_BOUNDARY",
    "Use layered preventive physical security, access control, detection, alerts, barriers, emergency procedures, and proportionate non-harmful automated responses.",
    "Material or potentially harmful interventions require explicit authorization and safety controls."
),

"129": (
    "RETIRE",
    "Municipal Infrastructure",
    "Legal & Compliance",
    "PROHIBIT_IMPLEMENTATION",
    "Municipal technology integration must occur through explicit authorization, documented interfaces, procurement processes, security review, support ownership, and public-sector governance.",
    "Covert black-box infrastructure insertion is retired."
),

"130": (
    "REFRAME",
    "Architecture / Brand",
    "Infrastructure Governance",
    "CANONICAL_REFRAME",
    "Design physical locations to communicate durability, quality, safety, local relevance, environmental responsibility, and Dalizebo brand identity.",
    "Physical storytelling replaces territorial intimidation."
),

"131": (
    "REFRAME",
    "Minerals / Commerce",
    "Corporate Strategy",
    "CANONICAL_REFRAME",
    "Build competitive capabilities in lawful mineral sourcing, processing, logistics, market intelligence, contracting, and value-added production.",
    "Market participation must not become unlawful control of mineral flows."
),

"132": (
    "R&D",
    "Robotics",
    "R&D Governance",
    "RESEARCH_BOUNDARY",
    "Research autonomous diagnostics, predictive maintenance, robotic repair assistance, modular replacement, and machine-to-machine maintenance.",
    "Autonomous repair is a legitimate long-term robotics program."
),

"133": (
    "TECHNICAL",
    "Environmental Engineering",
    "Infrastructure Engineering",
    "NONE",
    "Engineer equipment and facilities for local heat, dust, humidity, storms, power quality, vibration, and other relevant environmental conditions.",
    "Direct infrastructure-hardening control."
),

"134": (
    "POLICY",
    "Risk",
    "Risk Governance",
    "NONE",
    "Prefer physical investments with clearly modeled downside, risk controls, insurance where appropriate, staged capital deployment, and significant potential upside.",
    "Asymmetric risk principle retained."
),

"135": (
    "REFRAME",
    "Water Infrastructure",
    "Infrastructure Governance",
    "CANONICAL_REFRAME",
    "Build lawful and sustainable water security through permitted access, storage, recycling, efficiency, monitoring, diversified supply, and protection of shared water resources.",
    "Total control of aquifers is not an approved objective."
),

"136": (
    "POLICY",
    "Energy Economics",
    "Energy Governance",
    "NONE",
    "Optimize grid, solar, storage, and flexible loads according to time-of-use pricing, demand charges, generation forecasts, reliability requirements, and applicable market rules.",
    "Legitimate energy arbitrage is retained."
),

"137": (
    "TECHNICAL",
    "Communications",
    "Infrastructure Engineering",
    "NONE",
    "Design resilient fleet communications using authenticated links, redundancy, interference detection, channel diversity, fallback modes, and lawful anti-jamming resilience.",
    "Communications resilience must comply with spectrum regulation."
),

"138": (
    "TECHNICAL",
    "Digital Twins",
    "Platform Architecture",
    "NONE",
    "Represent material physical assets through governed digital twins containing identity, state, telemetry, maintenance, location, lifecycle, and operational history where useful.",
    "Direct physical-to-digital architecture."
),

"139": (
    "TECHNICAL",
    "Logistics",
    "Operations Engineering",
    "NONE",
    "Dynamically optimize routes using border conditions, congestion, cost, service level, risk, customs status, weather, availability, and delivery constraints.",
    "Direct logistics capability."
),

"140": (
    "POLICY",
    "Property Strategy",
    "Executive Governance",
    "NONE",
    "Maintain a long-term land and facilities strategy based on forecast capacity, infrastructure requirements, valuation, development plans, environmental factors, and capital discipline.",
    "Constant land acquisition is replaced by demand-driven strategic expansion."
),

"141": (
    "R&D",
    "Agriculture",
    "R&D Governance",
    "RESEARCH_BOUNDARY",
    "Research resilient food-production systems including controlled agriculture, irrigation automation, renewable energy, monitoring, storage, and supply-chain resilience.",
    "Agricultural resilience remains an optional strategic capability."
),

"142": (
    "RETIRE",
    "Competitive Intelligence",
    "Security Governance",
    "PROHIBIT_IMPLEMENTATION",
    "Use lawful public geospatial, commercial, regulatory, and market information for regional planning. Do not covertly track the precise physical location of competitor assets.",
    "Unlawful or intrusive competitor geolocation is retired."
),

"143": (
    "R&D",
    "Mineral Processing",
    "R&D Governance",
    "RESEARCH_BOUNDARY",
    "Research economically and environmentally viable movement from raw mineral extraction toward beneficiation, refining, higher-purity processing, and value-added manufacturing.",
    "Value-added mineral processing remains strategic R&D until justified."
),

"144": (
    "RETIRE",
    "Logistics Infrastructure",
    "Legal & Compliance",
    "PROHIBIT_IMPLEMENTATION",
    "Parcel lockers and logistics nodes must be identifiable to authorized operators and regulators and must not impersonate municipal infrastructure.",
    "Infrastructure disguise and deceptive placement are retired."
),

"145": (
    "TECHNICAL",
    "Hardware Reliability",
    "Hardware Engineering",
    "NONE",
    "Design strategic hardware for long service life through reliability engineering, modular replacement, environmental hardening, predictive maintenance, repairability, and lifecycle testing.",
    "Ten years may be used as a product-specific target where justified."
),

"146": (
    "TECHNICAL",
    "Energy Security",
    "Security Engineering",
    "NONE",
    "Protect distributed energy infrastructure through physical controls, secure firmware, network segmentation, authenticated management, tamper detection, monitoring, incident response, and redundancy.",
    "Direct cyber-physical security requirement."
),

"147": (
    "REFRAME",
    "Trade Policy",
    "Legal & Compliance",
    "CANONICAL_REFRAME",
    "Participate transparently in SADC trade policy, standards, industry bodies, consultations, research, and public-private collaboration to support efficient regional commerce.",
    "Policy influence must be transparent and must not become regulatory capture."
),

"148": (
    "REFRAME",
    "Infrastructure Lifecycle",
    "Infrastructure Governance",
    "CANONICAL_REFRAME",
    "Build critical infrastructure for long useful life through lifecycle engineering, maintainability, adaptability, durable materials, documentation, and planned renewal.",
    "Durability becomes measurable lifecycle engineering."
),

"149": (
    "TECHNICAL",
    "Environmental Monitoring",
    "Data & Infrastructure",
    "NONE",
    "Use environmental sensors, weather data, forecasting, and climate models to improve solar forecasting, infrastructure protection, agriculture, water planning, and operational resilience.",
    "Direct environmental intelligence capability."
),

"150": (
    "REFRAME",
    "Regional Operations",
    "Executive Governance",
    "CANONICAL_REFRAME",
    "Build a credible regional physical presence through reliable facilities, infrastructure, local employment, community relationships, service quality, partnerships, and long-term investment.",
    "Physical authority becomes trusted operational presence rather than intimidation."
),

}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid pillar-review.csv")

expected = {f"{i:03d}" for i in range(106, 151)}
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
        "ERROR: Missing Cluster C Pillars: "
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
    if 106 <= int(row["pillar_id"]) <= 150
]

counts = Counter(
    row["approved_classification"]
    for row in cluster
)

lines = [
    "# Cluster C Constitutional Reconciliation",
    "",
    "## Source",
    "",
    "Cluster C: Infrastructure & Physical Dominance (106–150).",
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

print("OK: Pillars 106–150 reconciled.")

for key in sorted(counts):
    print(f"{key}: {counts[key]}")

print(f"Report: {REPORT}")
