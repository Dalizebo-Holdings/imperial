#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REPORT = ROOT / "operating-systems/reconciliation/reports/CLUSTER_D.md"
STATUS = ROOT / "operating-systems/reconciliation/reports/STATUS.md"

# type, domain, owner, priority, phase, security,
# disposition, dependencies, canonical, notes

D = {

"101": ("DATA_PRODUCT","Operations & Logistics","Industrial Governance","P3","15","CRITICAL","REFRAME",
"Geospatial OS;Environment OS;Safety OS;Compliance OS",
"Support lawful mineral-resource assessment, licensed exploration planning, project economics, environmental review, operational monitoring, and regulated mining workflows.",
"Mining activity requires permits, qualified professionals, environmental controls, worker safety, and applicable mineral law."),

"102": ("DATA_PRODUCT","Operations & Logistics","Supply Chain Governance","P3","15","HIGH","REFRAME",
"Supply-Chain OS;Procurement OS;Risk Governance",
"Track critical-mineral supply, demand, sourcing concentration, price exposure, supplier risk, recycling opportunities, and lawful strategic reserves.",
"Chokepoint control is replaced with resilient and diversified critical-material supply management."),

"103": ("SHARED_SERVICE","Infrastructure & Cloud","Infrastructure Engineering","P1","15","CRITICAL","REFRAME",
"Solar-Grid OS;Battery-Storage OS;Monitoring OS",
"Manage energy sourcing, generation, consumption, resilience, efficiency, capacity, cost, and backup strategies across Dalizebo infrastructure.",
"Energy independence becomes resilient and economically sustainable energy architecture."),

"104": ("SHARED_SERVICE","Infrastructure & Cloud","Infrastructure Engineering","P2","15","CRITICAL","KEEP",
"Energy OS;Battery-Storage OS;Monitoring OS",
"Monitor solar generation, inverter health, storage, load, yield, faults, maintenance, forecasts, and energy-system performance.",
"Solar-grid monitoring is a legitimate infrastructure capability."),

"105": ("SHARED_SERVICE","Infrastructure & Cloud","Infrastructure Engineering","P2","15","CRITICAL","REFRAME",
"Energy OS;Solar-Grid OS;Monitoring OS;Safety OS",
"Manage battery state, reserve thresholds, lifecycle, charging policy, backup capacity, health, alarms, and safe energy-storage operations.",
"Battery storage targets measured resilience rather than an absolute uptime guarantee."),

"106": ("RETIRED_REFRAMED","Operations & Logistics","Industrial Governance","P3","15","CRITICAL","REFRAME",
"Mining OS;Refinery OS;Safety OS;Environment OS",
"Represent mineral-processing and extraction workflows only as governed industrial-process records, compliance controls, monitoring, vendor interfaces, and safety requirements.",
"Detailed hazardous chemical extraction procedures are outside the platform capability and require licensed industrial specialists."),

"107": ("RETIRED_REFRAMED","Operations & Logistics","Industrial Governance","P3","15","CRITICAL","REFRAME",
"Mining OS;Extraction OS;Quality-Control OS;Safety OS",
"Manage refinery workflow records, material traceability, quality evidence, licensed processing partners, compliance, safety, and production status.",
"The platform does not prescribe hazardous refining procedures."),

"108": ("SHARED_SERVICE","Operations & Logistics","Manufacturing Operations","P2","12","HIGH","REFRAME",
"Manufacturing OS;Inventory OS;Quality-Control OS",
"Manage production schedules, work orders, assembly stages, materials, capacity, traceability, quality gates, and operational metrics.",
"Production OS becomes governed manufacturing execution."),

"109": ("SHARED_SERVICE","Operations & Logistics","Manufacturing Operations","P2","12","HIGH","REFRAME",
"Production OS;Hardware OS;Quality-Control OS",
"Manage additive manufacturing, approved fabrication processes, bills of materials, machine capacity, work instructions, quality records, and production traceability.",
"Manufacturing automation remains subject to equipment safety and quality controls."),

"110": ("SHARED_SERVICE","Infrastructure & Cloud","Hardware Engineering","P2","12","HIGH","KEEP",
"Inventory OS;Maintenance OS;Safety OS",
"Manage hardware inventory, configuration, lifecycle, components, firmware references, service history, compatibility, and asset records.",
"Hardware OS becomes physical technology asset management."),

"111": ("R&D","Automation & Workflow","Robotics Governance","R&D","18","CRITICAL","REFRAME",
"Hardware OS;Actuator OS;Safety OS;Monitoring OS",
"Research and govern non-weapon robotic systems for authorized industrial, logistics, inspection, maintenance, and service tasks with bounded autonomy and human oversight.",
"Robotics must include safety limits, authorization, emergency stop, monitoring, and defined operating environments."),

"112": ("R&D","Automation & Workflow","Robotics Governance","R&D","18","CRITICAL","REFRAME",
"Robotics OS;Safety OS;Monitoring OS",
"Manage calibration, diagnostics, constraints, position feedback, maintenance, and safe control interfaces for authorized robotic actuators.",
"Actuation remains bounded by equipment-specific safety controls."),

"113": ("R&D","Automation & Workflow","Robotics Governance","R&D","18","CRITICAL","REFRAME",
"Robotics OS;Fleet OS;Geospatial OS;Safety OS",
"Research coordinated non-weapon drone fleets for lawful inspection, mapping, inventory, logistics, agriculture, and infrastructure operations using geofencing, authorization, collision avoidance, and human oversight.",
"Weaponization, harmful targeting, evasion of aviation controls, and unsafe autonomous swarm behavior are prohibited."),

"114": ("PRODUCT","Operations & Logistics","Logistics Operations","P1","6","HIGH","REFRAME",
"Logistics OS;Maintenance OS;Geospatial OS",
"Manage vehicles, couriers, approved drones, assignments, capacity, location, maintenance, utilization, compliance, and dispatch.",
"Fleet OS provides governed transportation asset management."),

"115": ("PRODUCT","Operations & Logistics","Logistics Operations","P0","6","HIGH","REFRAME",
"Fleet OS;Courier OS;Mapping OS",
"Plan and optimize lawful delivery, transport, routing, capacity, handoffs, service levels, cost, and contingency routes.",
"Ghost routes become resilient, documented logistics alternatives rather than concealed corridors."),

"116": ("PRODUCT","Operations & Logistics","Supply Chain Governance","P1","6","HIGH","REFRAME",
"Procurement OS;Inventory OS;Warehousing OS;Logistics OS",
"Track materials, suppliers, purchase orders, shipments, inventory movement, provenance, lead time, cost, quality, risk, and chain of custody.",
"Atom-level language becomes practical end-to-end supply-chain traceability."),

"117": ("PRODUCT","Operations & Logistics","Warehouse Operations","P1","6","HIGH","REFRAME",
"Inventory OS;Locker OS;Logistics OS",
"Manage warehouses, storage locations, receiving, picking, packing, transfers, cycle counts, capacity, security, and dispatch.",
"Ghost-node terminology becomes ordinary secured distributed warehousing."),

"118": ("PRODUCT","Commerce & Retail","Commerce Platform","P0","6","HIGH","KEEP",
"Warehousing OS;Supply-Chain OS;Commerce",
"Provide real-time inventory quantities, reservations, availability, stock movement, reorder points, locations, valuation inputs, and operational alerts.",
"Inventory OS is a core Commerce capability."),

"119": ("PRODUCT","Operations & Logistics","Procurement Governance","P1","9","HIGH","REFRAME",
"Inventory OS;Supply-Chain OS;Contract OS",
"Manage requisitions, supplier selection, approvals, purchase orders, receiving, invoices, budgets, and procurement records.",
"Payment mechanism is configurable; procurement is not dependent on DZC."),

"120": ("PRODUCT","Operations & Logistics","Logistics Operations","P1","6","HIGH","KEEP",
"Fleet OS;Logistics OS;Records OS",
"Manage last-mile assignments, package status, proof of handoff, chain of custody, delivery exceptions, tracking, and customer notifications.",
"Courier OS is a legitimate last-mile logistics capability."),

"121": ("RETIRED_REFRAMED","Operations & Logistics","Logistics Operations","P2","9","HIGH","REFRAME",
"Locker OS;Access-Control OS;Monitoring OS",
"Manage distributed secure pickup and storage nodes using documented locations, authorized access, monitoring, audit logs, and privacy-conscious operations.",
"Concealment functionality is retired; distributed nodes must operate lawfully and transparently where required."),

"122": ("PRODUCT","Operations & Logistics","Commerce Platform","P1","9","HIGH","KEEP",
"Identity OS;Access-Control OS;Courier OS",
"Manage secure customer pickup lockers, temporary access credentials, reservations, compartments, delivery events, audit records, and service status.",
"Locker OS is a legitimate commerce and logistics service."),

"123": ("DATA_PRODUCT","Operations & Logistics","Trade Governance","P2","15","CRITICAL","REFRAME",
"Compliance OS;Logistics OS;Supply-Chain OS",
"Support lawful regional trade planning using customs requirements, tariffs, border procedures, transit times, documentation, trade agreements, and logistics data.",
"Tariff arbitrage becomes compliant trade optimization; customs or tax evasion is prohibited."),

"124": ("DATA_PRODUCT","Operations & Logistics","Logistics Strategy","P3","15","HIGH","REFRAME",
"Regional-Trade OS;Logistics OS;Corridor OS",
"Evaluate lawful rail freight options, capacity, schedules, costs, service providers, terminals, and infrastructure for bulk transport.",
"Rail capture is replaced by commercial rail-logistics planning and partnerships."),

"125": ("DATA_PRODUCT","Operations & Logistics","Logistics Strategy","P2","15","HIGH","REFRAME",
"Mapping OS;Regional-Trade OS;Logistics OS",
"Model regional transport corridors using travel time, border conditions, infrastructure, risk, capacity, cost, redundancy, and service availability.",
"Corridor dominance becomes resilient regional route planning."),

"126": ("PRODUCT","Operations & Logistics","Property Governance","P2","12","HIGH","REFRAME",
"Land-Title OS;Records OS;Compliance OS",
"Manage property records, ownership, leases, valuations, maintenance, due diligence, obligations, documents, and portfolio performance.",
"Property management must rely on lawful ownership and documented records."),

"127": ("DATA_PRODUCT","Data & Knowledge","Property Governance","P2","12","CRITICAL","REFRAME",
"Property OS;Records OS;Compliance OS",
"Maintain verified references to deeds, title records, ownership evidence, transactions, encumbrances, and relevant public registries.",
"Blockchain is optional and must never replace legally authoritative land registries."),

"128": ("R&D","Operations & Logistics","Agriculture Operations","P3","18","HIGH","REFRAME",
"Water-Source OS;Climate OS;Safety OS",
"Research and manage precision agriculture, irrigation, crop monitoring, farm operations, equipment, environmental conditions, yields, and resource efficiency.",
"Autonomous farming requires agricultural safety, environmental, and human-oversight controls."),

"129": ("SHARED_SERVICE","Operations & Logistics","Infrastructure Engineering","P2","15","CRITICAL","REFRAME",
"Environment OS;Maintenance OS;Safety OS",
"Monitor lawful water sources, storage, pumps, filtration systems, usage, quality records, maintenance, availability, and resilience.",
"Water infrastructure must comply with environmental, health, and water-use requirements."),

"130": ("SHARED_SERVICE","Operations & Logistics","Infrastructure Engineering","P2","15","CRITICAL","REFRAME",
"Property OS;Infrastructure OS;Safety OS",
"Manage authorized construction projects, plans, contractors, materials, milestones, costs, inspections, approvals, safety records, and handover.",
"Construction requires qualified professionals and applicable building approvals."),

"131": ("SHARED_SERVICE","Infrastructure & Cloud","Infrastructure Engineering","P1","15","CRITICAL","REFRAME",
"Energy OS;Network infrastructure;Maintenance OS",
"Manage physical energy, communications, facilities, utility, resilience, maintenance, capacity, and infrastructure lifecycle records.",
"Infrastructure OS becomes governed physical-infrastructure management."),

"132": ("R&D","Infrastructure & Cloud","Infrastructure Governance","R&D","18","CRITICAL","REFRAME",
"Infrastructure OS;IoT;Identity OS;Privacy Governance",
"Research interoperable civic and site infrastructure using authorized sensors, utilities, mobility, environmental data, public services, and privacy-preserving automation.",
"Municipal integration requires government authorization, security, privacy, procurement, and public-interest governance."),

"133": ("DATA_PRODUCT","Legal & Compliance","Property Governance","P2","15","CRITICAL","REFRAME",
"Property OS;Mapping OS;Compliance OS",
"Analyze public or otherwise authorized zoning, land-use, development-plan, infrastructure, and planning data for property decisions.",
"Using confidential pre-publication zoning information or improperly obtained planning data is prohibited."),

"134": ("RETIRED_REFRAMED","Operations & Logistics","Property Governance","P3","15","HIGH","REFRAME",
"Property OS;Zoning OS;Capital-Allocation OS",
"Evaluate lawful urban property acquisition, redevelopment, leasing, infrastructure investment, and operating-node opportunities through due diligence and planning controls.",
"Urban capture becomes lawful property and infrastructure development."),

"135": ("RETIRED_REFRAMED","Operations & Logistics","Regional Strategy","P3","15","HIGH","REFRAME",
"Agriculture OS;Regional-Trade OS;Infrastructure OS",
"Support sustainable rural operations through agriculture, logistics, infrastructure, connectivity, procurement, employment, and community partnerships.",
"Dominance of rural regions is replaced with lawful regional development and commercial participation."),

"136": ("R&D","Frontier R&D","R&D Governance","R&D","18","CRITICAL","R&D",
"Geospatial OS;Environment OS;Compliance OS",
"Research lawful use of satellite imagery and remote-sensing services for agriculture, environment, infrastructure, logistics, and geographic analytics.",
"Satellite operations require appropriate licensing, lawful data access, and privacy safeguards."),

"137": ("R&D","Frontier R&D","R&D Governance","R&D","18","CRITICAL","R&D",
"Satellite OS;Archive OS;Disaster-Recovery OS",
"Research future orbital communications, archival, sensing, and resilience capabilities only where technically and legally justified.",
"Orbital systems remain long-horizon research, not a current production dependency."),

"138": ("INTEGRATION","Infrastructure & Cloud","Infrastructure Engineering","P3","15","HIGH","REFRAME",
"Network infrastructure;Satellite OS;Monitoring OS",
"Integrate approved satellite or off-grid connectivity providers as optional redundant network paths for remote or resilience-critical locations.",
"Starlink is treated as one possible provider rather than an architectural dependency."),

"139": ("DATA_PRODUCT","Data & Knowledge","Geospatial Governance","P2","15","CRITICAL","REFRAME",
"Mapping OS;Recon OS;Compliance OS",
"Manage authorized geospatial datasets for Dalizebo assets, infrastructure, logistics, public market context, environmental conditions, and regional planning.",
"Tracking private competitor assets or individuals without lawful authorization is prohibited."),

"140": ("DATA_PRODUCT","Data & Knowledge","Geospatial Governance","P2","15","HIGH","REFRAME",
"Geospatial OS;Infrastructure OS",
"Provide maps and digital-twin views of authorized assets, facilities, routes, infrastructure, operations, and public regional datasets.",
"Regional visualization is limited to lawful, relevant, and appropriately sourced information."),

"141": ("DATA_PRODUCT","Data & Knowledge","Sustainability Governance","P2","15","HIGH","REFRAME",
"Environment OS;Solar-Grid OS;Geospatial OS",
"Use reputable weather and climate data for energy forecasting, operational planning, infrastructure risk, agriculture, and resilience.",
"Climate forecasts are probabilistic decision inputs rather than guaranteed predictions."),

"142": ("DATA_PRODUCT","Governance & Audit","Sustainability Governance","P2","15","HIGH","REFRAME",
"Sustainability OS;Climate OS;Compliance OS",
"Measure environmental impacts, energy, waste, water, emissions, land use, compliance obligations, and mitigation actions.",
"Environmental performance includes ecological, operational, financial, and regulatory dimensions."),

"143": ("POLICY","Governance & Audit","Sustainability Governance","P2","15","HIGH","REFRAME",
"Environment OS;Resource-Recovery OS;Compliance OS",
"Establish sustainability objectives covering efficiency, emissions, resource recovery, circularity, regulatory compliance, resilience, and transparent measurement.",
"Sustainability must not be reduced to tax hedging."),

"144": ("SHARED_SERVICE","Operations & Logistics","Sustainability Governance","P3","15","CRITICAL","REFRAME",
"Inventory OS;Environment OS;Safety OS",
"Manage lawful e-waste collection, classification, chain of custody, reuse, certified recycling providers, recovered-material records, and environmental reporting.",
"Hazardous material recovery must use qualified and appropriately licensed processors rather than platform-supplied extraction instructions."),

"145": ("POLICY","Governance & Audit","Business Continuity","P0","8","CRITICAL","KEEP",
"Backup systems;Archive OS;Infrastructure OS;Monitoring OS",
"Maintain disaster-recovery plans, backups, alternate infrastructure, restoration procedures, recovery objectives, exercises, ownership, and evidence.",
"Disaster Recovery OS is a foundational resilience capability."),

"146": ("SHARED_SERVICE","Operations & Logistics","Reliability Engineering","P1","12","HIGH","REFRAME",
"Hardware OS;Inventory OS;Monitoring OS",
"Manage preventive and corrective maintenance, inspections, work orders, spare parts, service history, scheduling, diagnostics, and technician or approved robotic dispatch.",
"Maintenance automation remains subject to equipment safety and authorization."),

"147": ("SHARED_SERVICE","Governance & Audit","Quality Governance","P1","8","HIGH","REFRAME",
"Production OS;Deployment OS;Records OS",
"Provide quality gates, testing, inspection, traceability, defect management, acceptance criteria, release controls, and corrective-action workflows.",
"Quality targets are measurable service objectives rather than an impossible absolute fidelity guarantee."),

"148": ("POLICY","Governance & Audit","Safety Governance","P0","8","CRITICAL","REFRAME",
"Hazard-Check OS;Maintenance OS;Compliance OS",
"Define physical, workplace, equipment, operational, emergency, and infrastructure safety controls with reporting, training, inspections, and corrective actions.",
"Safety OS protects people, facilities, equipment, customers, and authorized operations."),

"149": ("AUTOMATION","Operations & Logistics","Safety Governance","P1","8","CRITICAL","REFRAME",
"Safety OS;Monitoring OS;Maintenance OS",
"Schedule and record routine inspections for thermal conditions, dust, wear, damage, environmental exposure, equipment health, and other approved facility hazards.",
"Hazard checks support preventive maintenance and workplace safety."),

"150": ("AUTOMATION","Operations & Logistics","Regional Operations","P2","15","CRITICAL","REFRAME",
"Identity OS;Access-Control OS;Projects;Safety OS",
"Coordinate authorized field operations including site visits, inspections, maintenance, installations, logistics, partner support, documentation, check-in, and incident escalation.",
"Physical regional operations require identified personnel, permissions, safety controls, lawful purpose, and auditability."),
}

POLICIES = {
"Operations & Logistics":
"Safety;authorization;asset governance;environmental compliance;traceability",
"Infrastructure & Cloud":
"Reliability;security;change control;capacity;physical safety",
"Automation & Workflow":
"Bounded autonomy;authorization;observability;safety;emergency stop",
"Commerce & Retail":
"Inventory integrity;tenant isolation;audit;consumer operations",
"Data & Knowledge":
"Provenance;privacy;authorization;retention;data classification",
"Legal & Compliance":
"Applicable law;authorized data;professional review;audit",
"Governance & Audit":
"Policy enforcement;audit;evidence;safety;accountability",
"Frontier R&D":
"Research boundary;safety review;legal review;no production dependency",
}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid OS review ledger")

expected = {f"{i:03d}" for i in range(101, 151)}
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
        "Authorized operational, asset, logistics, environmental, "
        "infrastructure, telemetry, configuration, and governance data"
    )

    row["outputs"] = (
        "Governed plans, records, alerts, schedules, asset state, "
        "analyses, work orders, reports, or authorized operations"
    )

    row["policies"] = POLICIES[domain]
    row["events"] = f"os.{pid}.evaluated"
    row["apis"] = "Internal versioned API; external integrations only where approved"

    row["data_requirements"] = (
        "Tenant-scoped authorized records; provenance; asset identity; "
        "retention; geospatial/privacy controls; audit metadata"
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
        "ERROR: missing Cluster D OS entries: "
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
    "# Operating Systems Cluster D Reconciliation",
    "",
    "## Scope",
    "",
    "OS-101 through OS-150 — Physical, Logistical & Environmental.",
    "",
    "Original source statements remain unchanged.",
    "",
    "Hazardous, covert, coercive, surveillance-oriented, or unlawful "
    "source concepts are bounded, retired, or canonically reframed.",
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

Cluster D classified.

## Completed Canonical Range

OS-001 → OS-150

## Next Work

OS-151 → OS-200 — Specialized & Domain Dominance.

## Governing Rule

Source statements remain preserved.

Unsafe or unlawful source concepts are retired or canonically reframed.

Canonical implementation decisions are recorded separately from source history.
""",
encoding="utf-8",
)

print("OK: OS Cluster D 101-150 classified.")
print(f"Canonical classification: {classified}/269")

for key in sorted(types):
    print(f"{key}: {types[key]}")
