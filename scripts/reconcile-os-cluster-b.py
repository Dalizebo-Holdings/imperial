#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REPORT = ROOT / "operating-systems/reconciliation/reports/CLUSTER_B.md"
STATUS = ROOT / "operating-systems/reconciliation/reports/STATUS.md"

# type, domain, owner, priority, phase, security,
# disposition, dependencies, policies, canonical, notes

D = {
"021": (
"POLICY","Governance & Audit","Executive Governance","P1","3","CRITICAL",
"REFRAME","Pillars OS;Algorithm OS;Audit-Vigil OS",
"Delegated authority;approval thresholds;constitutional policy",
"Provide the governed executive control model for platform-wide strategic direction, delegated authority, escalation, approvals, and policy-constrained coordination.",
"Crown OS becomes accountable executive governance rather than absolute command."
),

"022": (
"SHARED_SERVICE","Developer Platform","Executive Governance","P1","3","CRITICAL",
"REFRAME","Crown OS;Identity OS;Access-Control OS;Audit-Vigil OS",
"Authentication;authorization;approval;non-repudiation",
"Provide an authenticated executive command interface through which authorized leaders submit governed directives, decisions, and execution requests.",
"Architect OS becomes an authorized control-plane interface rather than a single-person unrestricted command channel."
),

"023": (
"POLICY","Governance & Audit","Partner Governance","P2","12","HIGH",
"REFRAME","Crown OS;Contract OS;Access-Control OS",
"Partner governance;delegation;contracts;conflict management",
"Manage delegated authority, responsibilities, approvals, governance rights, accountability, and operating rules for high-responsibility partners.",
"Regency OS becomes formal partner and delegated-governance management."
),

"024": (
"AUTOMATION","Automation & Workflow","Operations Governance","P1","8","MEDIUM",
"KEEP","Loop OS;Projects;Repository OS",
"Task ownership;workflow permissions;change history",
"Automate recurring strategic sprints, work queues, prioritization, reminders, status synchronization, and operational follow-up.",
"Kiro OS remains a legitimate workflow and sprint automation capability."
),

"025": (
"AUTOMATION","Automation & Workflow","Automation Governance","P1","8","HIGH",
"REFRAME","Loop OS;Identity OS;Access-Control OS;Monitoring OS",
"Bounded autonomy;least privilege;timeouts;human override",
"Provide specialized software agents for repetitive, deterministic, authorized tasks with explicit scopes, observability, limits, and accountable ownership.",
"Servitor OS becomes bounded task agents rather than unrestricted autonomous executors."
),

"026": (
"SHARED_SERVICE","Developer Platform","Engineering Governance","P2","10","HIGH",
"REFRAME","Repository OS;Deployment OS;Security OS;Audit-Vigil OS",
"Code review;testing;dependency security;approval;rollback",
"Provide AI-assisted code generation, refactoring, review, testing, migration, and engineering automation under version control and human-approved deployment controls.",
"Autonomous programming is constrained by review, testing, security gates, and rollback."
),

"027": (
"SHARED_SERVICE","Developer Platform","Engineering Governance","P1","8","HIGH",
"KEEP","Identity OS;Access-Control OS;Audit-Vigil OS;Encryption OS",
"Repository access;branch protection;signing;secret scanning",
"Manage source repositories, permissions, branches, reviews, artifacts, release history, repository automation, and secure software-development records.",
"Repository OS directly supports governed source-control operations."
),

"028": (
"CORE","Infrastructure & Cloud","Platform Architecture","P0","5","CRITICAL",
"REFRAME","Deployment OS;Monitoring OS;Security OS;Load-Balance OS",
"Infrastructure policy;tenant isolation;resilience;cost controls",
"Manage compute, networking, storage, runtime infrastructure, provider abstraction, environment configuration, capacity, and cloud-resource lifecycle.",
"Cloud OS becomes provider-neutral infrastructure orchestration rather than dependency on named vendors."
),

"029": (
"CORE","Developer Platform","Platform Engineering","P0","5","CRITICAL",
"KEEP","Repository OS;Cloud-OS;Security OS;Monitoring OS",
"CI/CD policy;tests;approvals;artifact integrity;rollback",
"Provide controlled CI/CD, build, test, artifact, promotion, deployment, rollback, and release-management pipelines.",
"Deployment OS is a core developer-platform capability."
),

"030": (
"CORE","Infrastructure & Cloud","Platform Engineering","P1","5","HIGH",
"REFRAME","Cloud-OS;Deployment OS;Identity OS;Monitoring OS",
"Runtime isolation;secrets;resource limits;deployment policy",
"Provide secure low-latency serverless and edge execution where workloads materially benefit from regional or near-user execution.",
"Consumer-hive terminology is removed; edge execution is selected by latency, resilience, compliance, and cost."
),

"031": (
"CORE","Automation & Workflow","Platform Engineering","P1","5","HIGH",
"KEEP","Loop OS;Monitoring OS;Audit-Vigil OS",
"Scheduling;idempotency;timeouts;retry limits;ownership",
"Provide scheduled jobs and recurring execution with idempotency, bounded retries, observability, timeout controls, ownership, and failure handling.",
"Cron-Job OS becomes the BaaS scheduling primitive."
),

"032": (
"SHARED_SERVICE","Automation & Workflow","Platform Engineering","P2","8","HIGH",
"REFRAME","Integrations OS;Loop OS;Protocol OS;Monitoring OS",
"Schema validation;device authorization;event integrity",
"Provide governed event and data pipelines connecting authorized physical devices, sensors, integrations, applications, and digital services.",
"Automation-Pipe OS becomes general event and integration plumbing."
),

"033": (
"CORE","Infrastructure & Cloud","Reliability Engineering","P0","4","CRITICAL",
"KEEP","Cloud-OS;Security OS;Audit-Vigil OS",
"Telemetry;alert ownership;retention;incident response",
"Provide logs, metrics, traces, health checks, alerting, service-level monitoring, security telemetry, and operational visibility.",
"Monitoring OS is a foundational reliability capability."
),

"034": (
"AUTOMATION","Developer Platform","Engineering Governance","P1","8","HIGH",
"REFRAME","Monitoring OS;Repository OS;Programming-OS;Deployment OS",
"Change control;tests;approval;rollback;incident linkage",
"Detect software and configuration defects and assist diagnosis, remediation proposals, testing, and controlled repair workflows.",
"Automatic debugging may propose or test fixes but production changes remain governed."
),

"035": (
"SHARED_SERVICE","Infrastructure & Cloud","Platform Architecture","P2","8","HIGH",
"REFRAME","Monitoring OS;Load-Balance OS;Cloud-OS",
"Capacity policy;quotas;budgets;reliability thresholds",
"Manage capacity growth using measured demand, quotas, autoscaling policies, budgets, resilience requirements, and service objectives.",
"Scale OS becomes evidence-driven capacity management."
),

"036": (
"AUTOMATION","Infrastructure & Cloud","Platform Architecture","P2","8","HIGH",
"REFRAME","Monitoring OS;Scale-OS;Audit-Vigil OS",
"Performance budgets;change control;measurement;rollback",
"Continuously identify and prioritize measurable improvements in performance, reliability, cost, resource efficiency, and developer experience.",
"Optimization is evidence-driven and must not mutate production systems without governed change control."
),

"037": (
"CORE","Infrastructure & Cloud","Platform Engineering","P1","5","CRITICAL",
"KEEP","Cloud-OS;Monitoring OS;Security OS",
"Availability;health checks;tenant isolation;failover",
"Distribute network and application traffic across healthy capacity using load balancing, health checks, failover, rate controls, and geographic policies.",
"Load-Balance OS is a core infrastructure primitive."
),

"038": (
"CORE","Identity & Security","Security Architecture","P0","4","CRITICAL",
"REFRAME","Identity OS;Access-Control OS;Encryption OS;Monitoring OS",
"Zero trust;least privilege;incident response;secure defaults",
"Provide platform-wide security architecture including identity controls, authorization, secure defaults, threat controls, monitoring, incident response, and tenant isolation.",
"Security OS becomes the umbrella security capability."
),

"039": (
"CORE","Identity & Security","Security Engineering","P0","5","CRITICAL",
"REFRAME","Security OS;Monitoring OS;Cloud-OS",
"Network security;WAF;DDoS protection;rate limits;logging",
"Protect platform boundaries using network segmentation, firewalls, WAF controls, filtering, rate limiting, DDoS protections, detection, and incident response.",
"Firewall OS protects against threats without offensive action against competitors or external actors."
),

"040": (
"CORE","Identity & Security","Security Architecture","P0","4","CRITICAL",
"REFRAME","Security OS;Identity OS;Vault-OS",
"Cryptographic standards;key rotation;secret management;crypto agility",
"Provide encryption in transit and at rest, key management, secret management, signing, rotation, certificate lifecycle, and cryptographic agility.",
"Specific lattice cryptography is not mandatory until standardized, justified, and interoperable."
),

"041": (
"CORE","Developer Platform","Platform Architecture","P0","4","HIGH",
"KEEP","Identity OS;Access-Control OS;Audit-Vigil OS",
"API contracts;schemas;versioning;compatibility",
"Define versioned service contracts, schemas, communication protocols, error semantics, compatibility rules, and interface standards across platform layers.",
"Protocol OS provides deterministic interoperability between platform components."
),

"042": (
"CORE","Identity & Security","Identity Platform","P0","4","CRITICAL",
"REFRAME","Security OS;Encryption OS;Audit-Vigil OS",
"Authentication;session security;MFA;passkeys;identity lifecycle",
"Manage users, organizations, service identities, authentication factors, sessions, credentials, identity lifecycle, and verified account attributes.",
"Imperial Personas become governed human and service identities."
),

"043": (
"CORE","Identity & Security","Identity Platform","P0","4","CRITICAL",
"KEEP","Identity OS;Pillars OS;Audit-Vigil OS",
"RBAC;least privilege;tenant boundaries;policy evaluation",
"Provide granular authorization, RBAC, scoped permissions, service roles, tenant isolation, policy enforcement, and privileged-access controls.",
"Access-Control OS is a foundational kernel capability."
),

"044": (
"RETIRED_REFRAMED","Identity & Security","Security Governance","P2","8","HIGH",
"REFRAME","Security OS;Encryption OS;Protocol OS",
"Privacy;traffic protection;lawful accountability",
"Protect sensitive network metadata and communications through encryption, private networking, traffic minimization, authenticated tunnels, and operational security where lawful.",
"Stealth OS must not conceal activity from lawful oversight or enable deceptive or evasive operations."
),

"045": (
"SHARED_SERVICE","Legal & Compliance","Legal & Compliance","P2","14","CRITICAL",
"REFRAME","Compliance OS;Cloud-OS;Records OS",
"Data residency;cross-border transfer;licensing;contractual restrictions",
"Evaluate jurisdictional requirements and route or locate data and services according to lawful residency, privacy, licensing, contractual, and operational constraints.",
"Jurisdiction OS supports lawful regional architecture, not regulatory evasion."
),

"046": (
"SHARED_SERVICE","Governance & Audit","Legal & Compliance","P1","8","CRITICAL",
"REFRAME","Pillars OS;Records OS;Audit-Vigil OS;Jurisdiction OS",
"Compliance controls;evidence;regulatory mapping;exceptions",
"Map applicable requirements to controls, evaluate compliance evidence, track exceptions, generate reports, and support authorized remediation workflows.",
"Compliance OS automates evidence and control evaluation while preserving professional and legal review."
),

"047": (
"SHARED_SERVICE","Legal & Compliance","Legal Governance","P2","10","CRITICAL",
"REFRAME","Contract OS;Compliance OS;Records OS;Identity OS",
"Human approval;legal privilege;filing authorization;document integrity",
"Assist authorized users with drafting, reviewing, classifying, assembling, and submitting legal documents and regulatory forms under required professional and human approval.",
"Legal-Bot OS may assist legal work but cannot independently practice law or make unauthorized filings."
),

"048": (
"SHARED_SERVICE","Legal & Compliance","Legal Governance","P1","8","CRITICAL",
"KEEP","Identity OS;Access-Control OS;Records OS;Audit-Vigil OS",
"Contract authority;signatures;retention;obligations;remedies",
"Manage contract drafting, negotiation state, approval, signatures, obligations, renewals, notices, amendments, evidence, remedies, and lifecycle records.",
"Contract OS becomes the governed contract lifecycle capability."
),

"049": (
"POLICY","Governance & Audit","Pillars OS","P0","3","CRITICAL",
"REFRAME","Pillars OS;Protocol OS;Audit-Vigil OS",
"Constitutional policy;exceptions;appeals;audit",
"Provide the application-facing governance adapter through which canonical Operating Systems request constitutional policy decisions and record enforcement evidence.",
"Governance OS does not duplicate Pillars OS; it exposes Pillars OS policy enforcement to platform capabilities."
),

"050": (
"AUTOMATION","Automation & Workflow","Executive Governance","P1","3","CRITICAL",
"REFRAME","Crown OS;Architect OS;Pillars OS;Loop OS;Audit-Vigil OS",
"Authorization;policy checks;approval thresholds;rollback;kill switch",
"Execute explicitly authorized strategic and operational actions only after identity, permission, constitutional policy, approval, safety, and audit checks succeed.",
"Executive-Action OS becomes a bounded execution trigger; harmful or unauthorized strategic action is prohibited."
),
}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid OS review ledger")

expected = {f"{i:03d}" for i in range(21, 51)}
found = set()

for row in rows:
    pid = row["canonical_id"]

    if pid not in D:
        continue

    (
        impl_type, domain, owner, priority, phase, security,
        disposition, dependencies, policies, canonical, notes
    ) = D[pid]

    row["review_status"] = "CLASSIFIED"
    row["domain"] = domain
    row["owner"] = owner
    row["priority"] = priority
    row["implementation_type"] = impl_type
    row["dependencies"] = dependencies

    row["inputs"] = (
        "Authorized requests, events, policies, configuration, "
        "identity context, telemetry, and governed platform data"
    )

    row["outputs"] = (
        "Governed decisions, actions, events, records, alerts, "
        "deployments, reports, or audit evidence"
    )

    row["policies"] = policies
    row["events"] = f"os.{pid}.evaluated"
    row["apis"] = "Internal versioned API; external exposure only where approved"

    row["data_requirements"] = (
        "Tenant-scoped data; provenance; authorization context; "
        "retention; immutable audit metadata"
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
        "ERROR: missing Cluster B OS entries: "
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

lines = [
    "# Operating Systems Cluster B Reconciliation",
    "",
    "## Scope",
    "",
    "OS-021 through OS-050 — Command, Control & Automation.",
    "",
    "Original source statements remain unchanged.",
    "",
    "## Classification Summary",
    "",
]

for key in sorted(counts):
    lines.append(f"- {key}: {counts[key]}")

lines.extend(["", "## Decisions", ""])

for row in cluster:
    lines.extend([
        f"### OS-{row['canonical_id']} — {row['name']}",
        "",
        f"**Type:** {row['implementation_type']}",
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

Cluster B classified.

## Completed Canonical Range

OS-001 → OS-050

## Next Work

OS-051 → OS-100 — Intelligence, Strategy & Influence.

## Governing Rule

Source statements remain preserved.

Canonical implementation decisions are recorded separately from source history.
""",
encoding="utf-8",
)

print("OK: OS Cluster B 021-050 classified.")
print(f"Canonical classification: {classified}/269")

for key in sorted(counts):
    print(f"{key}: {counts[key]}")
