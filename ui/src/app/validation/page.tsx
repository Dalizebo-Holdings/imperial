"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";

const navigation = [
  { href: "/", label: "Dashboard", exact: true },
  { href: "/commerce", label: "Commerce", exact: false },
  { href: "/pos", label: "POS", exact: false },
  { href: "/backend", label: "Backend", exact: false },
  { href: "/operations", label: "Operations", exact: false },
  { href: "/validation", label: "Validation", exact: false },
  { href: "/settings", label: "Settings", exact: false },
  { href: "/phase9", label: "Phase 9", exact: false },
];

export default function ValidationPage() {
  const pathname = usePathname();

  return (
    <div className="min-h-screen animate-fade-in">
      <nav className="nav" role="navigation" aria-label="Main navigation">
        <div className="nav-brand">
          <Link href="/" className="nav-brand-link" aria-label="Dalizebo Platform Home">
            <Logo size="medium" />
            <span className="beta-badge">Beta 0.1</span>
          </Link>
        </div>
        <div className="nav-links">
          {navigation.map((item) => {
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);
            const isPending = ["/settings", "/phase9"].includes(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${isActive ? "active" : ""} ${isPending ? "pending" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
                {isPending && " (pending)"}
              </Link>
            );
          })}
        </div>
      </nav>

      <main className="container">
        <header className="page-header">
          <h1 className="page-title">Validation</h1>
          <p className="page-subtitle">
            Phase 7 status, evidence inbox, ledger, discovery, pilot, release gates, PMF decision
          </p>
        </header>

        <section className="section" style={{ marginBottom: "16px" }}>
          <div
            style={{
              background: "var(--color-brand-primary-light)",
              border: "2px solid var(--color-brand-primary)",
              borderRadius: "12px",
              padding: "24px",
            }}
          >
            <div
              style={{
                display: "flex",
                gap: "12px",
                flexWrap: "wrap",
                alignItems: "center",
                marginBottom: "16px",
              }}
            >
              <span className="status-badge complete" style={{ fontSize: "14px" }}>
                PHASE7_IMPLEMENTATION_COMPLETE
              </span>
              <span className="status-badge pending" style={{ fontSize: "14px" }}>
                EXTERNAL_EVIDENCE_PENDING
              </span>
              <span className="status-badge blocked" style={{ fontSize: "14px" }}>
                PRODUCTION_AUTHORIZATION_BLOCKED
              </span>
            </div>
            <p style={{ color: "var(--color-text-secondary)", lineHeight: 1.6 }}>
              <strong>Repository engineering is complete.</strong> All evidence ingestion,
              append-only ledger, evidence-chain verification, evidence voiding, Discovery
              Gate derivation, Release Gate 1/2/3 derivations, Pilot Exit derivation,
              operational readiness evaluation, Public MVP evaluation, final PMF decision
              evaluator, PASS-only proof generation, and explicit blocker reporting are
              implemented and pass technical validators.
            </p>
            <p style={{ color: "var(--color-text-secondary)", lineHeight: 1.6, marginTop: "12px" }}>
              <strong>Canonical closure requires external evidence:</strong> discovery
              interviews, design partners, active pilot merchants, multi-week pilot
              metrics, willingness-to-pay evidence, customer references, production
              reliability metrics, payment reconciliation, inventory accuracy, commercial
              evidence, support/incident evidence, Public MVP first-90-day evidence, and
              external regulatory/payment-scope confirmation. No category is waived or
              replaced by test fixtures.
            </p>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Phase 7 Gates Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Discovery Gate</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">PENDING</span>
              </div>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Target: 20 interviews + 80% confirmation</li>
                <li>5 design partner commitments required</li>
                <li>3 active pilot merchants required</li>
                <li>TEST_FIXTURE evidence excluded</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Release Gate 1</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">BLOCKED (Discovery)</span>
              </div>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Requires Discovery Gate PASS</li>
                <li>REAL_OPERATIONAL attestations only</li>
                <li>PASS-only proof emission</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Release Gate 2</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">BLOCKED (Gate 1)</span>
              </div>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Requires Gate 1 PASS</li>
                <li>Pilot onboarding evidence required</li>
                <li>PASS-only proof emission</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Pilot Exit / Gate 3</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">DEFERRED</span>
              </div>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Requires real pilot evidence</li>
                <li>Capacity: 100/250/10,000 merchants</li>
                <li>Canonical KPI thresholds enforced</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Operational Readiness</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">PENDING EVIDENCE</span>
              </div>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Feedback classification P0-P3</li>
                <li>P1 <=1 business day response</li>
                <li>Incident ownership/recovery</li>
                <li>Tenant-isolation defects block</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Public MVP Evaluation</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">DEFERRED</span>
              </div>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>90-day launch criteria</li>
                <li>Strict churn/latency boundaries</li>
                <li>Append-only evidence ledger</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">PMF Decision</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">CONTINUE_VALIDATION</span>
              </div>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Requires all gates PASS</li>
                <li>Complete non-fixture proofs</li>
                <li>Fail-closed until satisfied</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Evidence Infrastructure</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Evidence Inbox</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Private template library</li>
                <li>Placeholder templates isolated</li>
                <li>New record creation with validation</li>
                <li>Preflight validation</li>
                <li>Overwrite rejection</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Durable Ledger</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>0600 file permissions</li>
                <li>Locked fsync append</li>
                <li>SHA-256 chain verification</li>
                <li>Verified ledger export</li>
                <li>TEST_FIXTURE exclusion</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Evidence Voiding</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Append-only void records</li>
                <li>Target event/envelope/digest binding</li>
                <li>Gate 3 exclusion of voided evidence</li>
                <li>Immutable ledger semantics</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Discovery & Onboarding</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Merchant interview execution</li>
                <li>Design partner eligibility triage</li>
                <li>Pilot onboarding start</li>
                <li>Opaque merchant references</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Technical Validation</h2>
          <p style={{ color: "var(--color-text-secondary)", marginBottom: "16px" }}>
            All <code>scripts/validate-validation-phase7-*.py</code> validators pass:
          </p>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Core Validators</h3>
              <ul style={{ fontSize: "13px", lineHeight: 1.7, color: "var(--color-text-secondary)" }}>
                <li>✓ validate-validation-phase7-foundation</li>
                <li>✓ validate-validation-phase7-inbox-workflow</li>
                <li>✓ validate-validation-phase7-evidence-ops</li>
                <li>✓ validate-validation-phase7-evidence-void</li>
                <li>✓ validate-validation-phase7-discovery-gate-derivation</li>
                <li>✓ validate-validation-phase7-release-gate-derivation</li>
                <li>✓ validate-validation-phase7-pilot</li>
                <li>✓ validate-validation-phase7-pilot-status-transitions</li>
                <li>✓ validate-validation-phase7-release-gate3-derivation</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Operations & Decision</h3>
              <ul style={{ fontSize: "13px", lineHeight: 1.7, color: "var(--color-text-secondary)" }}>
                <li>✓ validate-validation-phase7-operations</li>
                <li>✓ validate-validation-phase7-technical-attestation-execution</li>
                <li>✓ validate-validation-phase7-decision</li>
                <li>✓ validate-validation-phase7-collection</li>
                <li>✓ validate-validation-phase7-onboarding-event-evidence</li>
                <li>✓ validate-validation-phase7-discovery-execution</li>
                <li>✓ validate-validation-phase7-design-partner-triage</li>
                <li>✓ validate-validation-phase7-parallel-design-partner</li>
                <li>✓ validate-validation-phase7-pilot-onboarding-start</li>
                <li>✓ validate-validation-phase7-release-readiness-dashboard</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">External Evidence Categories (Pending)</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Discovery & Partners</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Discovery interviews</li>
                <li>□ Design partner commitments</li>
                <li>□ Active pilot merchants</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Pilot & Metrics</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Multi-week pilot metrics</li>
                <li>□ Willingness-to-pay evidence</li>
                <li>□ Customer references</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Operational & Commercial</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Production reliability metrics</li>
                <li>□ Payment reconciliation metrics</li>
                <li>□ Inventory-accuracy metrics</li>
                <li>□ Commercial evidence</li>
                <li>□ Support/incident evidence</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Regulatory & Launch</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Public MVP first-90-day evidence</li>
                <li>□ External regulatory confirmation</li>
                <li>□ Payment-scope confirmation</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}