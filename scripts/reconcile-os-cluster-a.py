#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

REVIEW = ROOT / "operating-systems/reconciliation/review/os-review.csv"
REPORT = ROOT / "operating-systems/reconciliation/reports/CLUSTER_A.md"
STATUS = ROOT / "operating-systems/reconciliation/reports/STATUS.md"

D = {
"001": dict(
    domain="Finance & Capital",
    owner="Finance Platform",
    priority="P1",
    implementation_type="INTEGRATION",
    dependencies="Identity OS;Access-Control OS;Audit-Vigil OS",
    security_level="HIGH",
    roadmap_phase="8",
    disposition="REFRAME",
    policies="Banking API access;credential security;transaction authorization;AML/KYC where applicable",
    canonical="Provide governed integrations with approved commercial banking APIs for balances, transaction data, payment initiation where authorized, reconciliation, and treasury operations.",
    notes="Bank integrations must use regulated providers, least privilege, explicit authorization, audit, and applicable financial controls."
),

"002": dict(
    domain="Finance & Capital",
    owner="Treasury Governance",
    priority="P1",
    implementation_type="SHARED_SERVICE",
    dependencies="Security OS;Encryption OS;Audit-Vigil OS",
    security_level="CRITICAL",
    roadmap_phase="8",
    disposition="REFRAME",
    policies="Treasury custody;segregation of duties;key management;reserve controls",
    canonical="Provide secure treasury custody and reserve-management controls for approved financial, digital, and physical assets.",
    notes="The Vault is a governed treasury-security capability rather than an unrestricted war-chest mechanism."
),

"003": dict(
    domain="Finance & Capital",
    owner="Tax & Finance Governance",
    priority="P1",
    implementation_type="SHARED_SERVICE",
    dependencies="Compliance OS;Records OS;Banking OS",
    security_level="HIGH",
    roadmap_phase="8",
    disposition="REFRAME",
    policies="Tax compliance;record retention;jurisdiction rules;professional review",
    canonical="Support lawful tax calculation, reporting, filing preparation, recordkeeping, scenario analysis, and tax-efficient planning subject to applicable law and qualified review.",
    notes="Tax shielding is replaced by lawful tax compliance and legitimate tax planning."
),

"004": dict(
    domain="Payments & Billing",
    owner="Finance Governance",
    priority="R&D",
    implementation_type="R&D",
    dependencies="Compliance OS;Legal-Bot OS;Medici-Ledger OS",
    security_level="CRITICAL",
    roadmap_phase="18",
    disposition="R&D",
    policies="Payments regulation;consumer protection;AML/KYC;securities analysis;reserve governance",
    canonical="Research Dalizebo-native credit or settlement mechanisms only after legal, regulatory, accounting, consumer-protection, reserve, and payments architecture requirements are satisfied.",
    notes="DZC issuance is not a production capability until its regulatory classification and operating controls are approved."
),

"005": dict(
    domain="Finance & Capital",
    owner="Treasury Governance",
    priority="P2",
    implementation_type="AUTOMATION",
    dependencies="Capital-Allocation OS;Audit-Vigil OS;Liquidity-Pool OS",
    security_level="HIGH",
    roadmap_phase="12",
    disposition="REFRAME",
    policies="Treasury allocation;liquidity floors;risk limits;approval thresholds",
    canonical="Automate approved treasury allocation policies across reserves, operating capital, investment, and R&D while respecting liquidity requirements, risk limits, and authorized exceptions.",
    notes="The 40/40/20 model may be configurable policy, not an immutable automatic sweep."
),

"006": dict(
    domain="Governance & Audit",
    owner="Finance Governance",
    priority="P0",
    implementation_type="SHARED_SERVICE",
    dependencies="Medici-Ledger OS;Records OS;Monitoring OS",
    security_level="CRITICAL",
    roadmap_phase="5",
    disposition="KEEP",
    policies="Audit logging;financial reconciliation;tamper evidence;retention",
    canonical="Continuously monitor material financial flows, reconciliations, exceptions, authorizations, and audit evidence across Dalizebo financial systems.",
    notes="Directly supports financial control, reconciliation, fraud detection, and auditability."
),

"007": dict(
    domain="Finance & Capital",
    owner="Finance Governance",
    priority="P2",
    implementation_type="POLICY",
    dependencies="Capital-Allocation OS;Records OS;Audit-Vigil OS",
    security_level="HIGH",
    roadmap_phase="12",
    disposition="REFRAME",
    policies="Intercompany distributions;transfer pricing;solvency;minority rights;tax",
    canonical="Govern lawful movement of distributable profits and excess liquidity between Dalizebo entities according to solvency, tax, transfer-pricing, contractual, minority-interest, and capital-allocation requirements.",
    notes="Profit extraction becomes governed intercompany capital management."
),

"008": dict(
    domain="Finance & Capital",
    owner="Capital Allocation",
    priority="P1",
    implementation_type="SHARED_SERVICE",
    dependencies="Audit-Vigil OS;Investment-Sweep OS;Risk Governance",
    security_level="HIGH",
    roadmap_phase="8",
    disposition="KEEP",
    policies="Investment mandate;risk limits;approval thresholds;liquidity",
    canonical="Evaluate available capital against approved ROI, risk, liquidity, strategic-value, resilience, and time-horizon criteria to recommend authorized deployment.",
    notes="Capital allocation remains a core decision-support capability."
),

"009": dict(
    domain="Finance & Capital",
    owner="Corporate Governance",
    priority="P2",
    implementation_type="SHARED_SERVICE",
    dependencies="Contract OS;Records OS;Compliance OS",
    security_level="HIGH",
    roadmap_phase="12",
    disposition="REFRAME",
    policies="Company law;share registers;beneficial ownership;governance rights",
    canonical="Manage Dalizebo ownership structures, equity records, cap tables, shareholder rights, partner equity, corporate actions, and governance obligations.",
    notes="Equity capture becomes transparent corporate ownership and cap-table management."
),

"010": dict(
    domain="Finance & Capital",
    owner="Treasury Governance",
    priority="P2",
    implementation_type="SHARED_SERVICE",
    dependencies="Banking OS;Capital-Allocation OS;Audit-Vigil OS",
    security_level="CRITICAL",
    roadmap_phase="12",
    disposition="REFRAME",
    policies="Treasury policy;liquidity limits;intercompany funding;financial regulation",
    canonical="Manage internal treasury liquidity, reserves, approved intercompany funding, cash concentration, and short-term capital availability without representing Dalizebo as a bank unless properly licensed.",
    notes="The internal-bank concept is restricted to lawful corporate treasury operations."
),

"011": dict(
    domain="Finance & Capital",
    owner="Capital Allocation",
    priority="P3",
    implementation_type="POLICY",
    dependencies="Capital-Allocation OS;Records OS;Compliance OS",
    security_level="HIGH",
    roadmap_phase="15",
    disposition="REFRAME",
    policies="Investment due diligence;property law;mineral rights;environmental review",
    canonical="Evaluate conversion of retained capital into productive physical assets such as property, infrastructure, energy assets, or lawful mineral interests using approved investment criteria and due diligence.",
    notes="Asset hardening becomes governed physical-asset diversification."
),

"012": dict(
    domain="Finance & Capital",
    owner="Finance Governance",
    priority="P3",
    implementation_type="POLICY",
    dependencies="Tax-OS;Contract OS;Records OS",
    security_level="HIGH",
    roadmap_phase="15",
    disposition="REFRAME",
    policies="Tax law;company law;arm's-length terms;accounting;exchange control",
    canonical="Administer director and intercompany loans with documented terms, approvals, accounting treatment, repayment schedules, tax review, and legal compliance.",
    notes="No guaranteed tax-free treatment is assumed or engineered."
),

"013": dict(
    domain="Finance & Capital",
    owner="Legal & Finance Governance",
    priority="P3",
    implementation_type="POLICY",
    dependencies="Jurisdiction OS;Compliance OS;Tax-OS",
    security_level="CRITICAL",
    roadmap_phase="15",
    disposition="REFRAME",
    policies="Tax;AML;sanctions;exchange control;beneficial ownership;reporting",
    canonical="Support lawful geographic diversification of assets, infrastructure, banking relationships, and corporate structures for resilience where justified by legal, tax, regulatory, and operational analysis.",
    notes="Jurisdiction diversification must never function as concealment, sanctions evasion, tax evasion, or regulatory avoidance."
),

"014": dict(
    domain="Finance & Capital",
    owner="Treasury Governance",
    priority="P2",
    implementation_type="SHARED_SERVICE",
    dependencies="Banking OS;Capital-Allocation OS;Compliance OS",
    security_level="CRITICAL",
    roadmap_phase="12",
    disposition="REFRAME",
    policies="Treasury mandate;counterparty limits;market risk;regulated instruments",
    canonical="Measure and manage material currency exposure through approved hedging instruments, diversification, natural hedges, reserves, and regulated counterparties.",
    notes="Gold, stablecoins, derivatives, or other instruments require separate suitability, custody, regulatory, and risk approval."
),

"015": dict(
    domain="Finance & Capital",
    owner="Risk Governance",
    priority="P2",
    implementation_type="DATA_PRODUCT",
    dependencies="Banking OS;Records OS;Compliance OS",
    security_level="HIGH",
    roadmap_phase="12",
    disposition="REFRAME",
    policies="Privacy;credit regulation;data provenance;model governance;adverse-action review",
    canonical="Assess internal and external credit risk using lawful, relevant, explainable, and appropriately governed financial and operational data.",
    notes="Credit scoring must use authorized data and appropriate fairness, privacy, explainability, and regulatory controls."
),

"016": dict(
    domain="Finance & Capital",
    owner="Risk Governance",
    priority="P3",
    implementation_type="RETIRED_REFRAMED",
    dependencies="Capital-Allocation OS;Contract OS;Compliance OS",
    security_level="HIGH",
    roadmap_phase="15",
    disposition="REFRAME",
    policies="Debt policy;competition law;credit limits;solvency;board approval",
    canonical="Use debt and credit facilities as governed financing tools for approved investments, acquisitions, working capital, and infrastructure while maintaining solvency, risk limits, contractual compliance, and competition-law requirements.",
    notes="Weaponization and coercive chokepoint acquisition are not approved capabilities."
),

"017": dict(
    domain="Finance & Capital",
    owner="Platform Architecture",
    priority="P0",
    implementation_type="CORE",
    dependencies="Records OS;Audit-Vigil OS;Identity OS;Access-Control OS",
    security_level="CRITICAL",
    roadmap_phase="4",
    disposition="REFRAME",
    policies="Transaction integrity;append-only audit;authorization;retention;reconciliation",
    canonical="Provide the authoritative transaction and financial-event ledger with durable identifiers, immutable or tamper-evident history, reconciliation support, authorization evidence, and auditable state transitions.",
    notes="Blockchain is optional; integrity, auditability, reconciliation, and durability are mandatory."
),

"018": dict(
    domain="Finance & Capital",
    owner="Finance Governance",
    priority="P3",
    implementation_type="POLICY",
    dependencies="Capital-Allocation OS;Asset-Harden OS;Records OS",
    security_level="HIGH",
    roadmap_phase="15",
    disposition="KEEP",
    policies="Capital preservation;succession;diversification;risk limits",
    canonical="Establish long-horizon capital-preservation, diversification, succession, reserve, and ownership policies supporting institutional continuity.",
    notes="Implements the long-term wealth-preservation objective under governed risk management."
),

"019": dict(
    domain="Finance & Capital",
    owner="Risk Governance",
    priority="P3",
    implementation_type="DATA_PRODUCT",
    dependencies="Market data integrations;Capital-Allocation OS;Compliance OS",
    security_level="HIGH",
    roadmap_phase="15",
    disposition="REFRAME",
    policies="Market conduct;data licensing;risk limits;trading authorization",
    canonical="Detect lawful pricing, timing, funding, and market inefficiencies using licensed or authorized market data and surface them for governed decision-making.",
    notes="The capability must not manipulate markets, misuse confidential information, or automatically trade outside approved mandates."
),

"020": dict(
    domain="Finance & Capital",
    owner="Treasury Governance",
    priority="P1",
    implementation_type="SHARED_SERVICE",
    dependencies="Vault-OS;Audit-Vigil OS;Capital-Allocation OS",
    security_level="CRITICAL",
    roadmap_phase="8",
    disposition="REFRAME",
    policies="Reserve policy;segregation of duties;access control;liquidity;incident response",
    canonical="Maintain protected strategic reserves with defined liquidity floors, custody controls, authorization thresholds, reconciliation, contingency access, and risk limits.",
    notes="War-Chest terminology becomes governed strategic-reserve management."
),
}

with REVIEW.open(encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fields = reader.fieldnames
    rows = list(reader)

if not fields:
    raise SystemExit("ERROR: invalid OS review ledger")

expected = {f"{i:03d}" for i in range(1, 21)}
found = set()

for row in rows:
    pid = row["canonical_id"]

    if pid not in D:
        continue

    d = D[pid]

    row["review_status"] = "CLASSIFIED"
    row["domain"] = d["domain"]
    row["owner"] = d["owner"]
    row["priority"] = d["priority"]
    row["implementation_type"] = d["implementation_type"]
    row["dependencies"] = d["dependencies"]
    row["inputs"] = "Authorized financial, operational, contractual, market, and configuration data"
    row["outputs"] = "Governed decisions, records, recommendations, transactions, alerts, or audit evidence"
    row["policies"] = d["policies"]
    row["events"] = f"os.{pid}.evaluated"
    row["apis"] = "Internal API first; external API only where explicitly approved"
    row["data_requirements"] = "Tenant-scoped records; provenance; retention; audit metadata"
    row["security_level"] = d["security_level"]
    row["roadmap_phase"] = d["roadmap_phase"]
    row["disposition"] = d["disposition"]
    row["canonical_interpretation"] = d["canonical"]
    row["decision_notes"] = d["notes"]

    found.add(pid)

missing = expected - found

if missing:
    raise SystemExit(
        "ERROR: missing Cluster A OS entries: "
        + ", ".join(sorted(missing))
    )

tmp = REVIEW.with_suffix(".tmp")

with tmp.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

tmp.replace(REVIEW)

cluster = [r for r in rows if r["canonical_id"] in expected]
counts = Counter(r["implementation_type"] for r in cluster)

lines = [
    "# Operating Systems Cluster A Reconciliation",
    "",
    "## Scope",
    "",
    "OS-001 through OS-020 — Fiscal & Capital Weaponization.",
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
        f"**Owner:** {row['owner']}",
        "",
        f"**Security:** {row['security_level']}",
        "",
        "**Source Statement**",
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

REPORT.write_text("\n".join(lines), encoding="utf-8")

classified = sum(
    1 for r in rows
    if r["canonical_id"] and r["review_status"] == "CLASSIFIED"
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

Cluster A classified.

## Completed Canonical Range

OS-001 → OS-020

## Next Work

OS-021 → OS-050 — Command, Control & Automation.

## Governing Rule

Source statements remain preserved.

Canonical implementation decisions are recorded separately from source history.
""",
    encoding="utf-8",
)

print("OK: OS Cluster A 001-020 classified.")
print(f"Canonical classification: {classified}/269")
for key in sorted(counts):
    print(f"{key}: {counts[key]}")
