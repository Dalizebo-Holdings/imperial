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
  { href: "/realtime", label: "Realtime", exact: false },
];

export default function DashboardPage() {
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
            const isPending = [
              "/commerce",
              "/pos",
              "/backend",
              "/operations",
              "/validation",
              "/settings",
              "/phase9",
              "/realtime",
            ].includes(item.href);

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
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">
            Dalizebo Imperial Platform — Phase 8 Development
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Phase Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Phase 7 — Product-Market Validation</h3>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
                <span className="status-badge complete">
                  IMPLEMENTATION_COMPLETE
                </span>
                <span className="status-badge pending">
                  EXTERNAL_EVIDENCE_PENDING
                </span>
              </div>
              <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", lineHeight: 1.6 }}>
                Repository engineering complete. All evidence ingestion, ledger,
                gate derivations, and PMF evaluator implemented and validated.
                External evidence (discovery interviews, design partners, pilot
                metrics, willingness-to-pay, regulatory confirmation) required
                for canonical closure.
              </p>
            </div>
            <div className="card">
              <h3 className="card-title">Phase 8 — Platform Hardening</h3>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
                <span className="status-badge complete">ACTIVE</span>
              </div>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Transactional outbox durability: <strong>COMPLETE</strong></li>
                <li>Webhooks network policy: <strong>COMPLETE</strong></li>
                <li>Outbox observability guardrails: <strong>COMPLETE</strong></li>
                <li>Delivery rate-limit envelope: <strong>COMPLETE</strong></li>
                <li>Realtime: <strong>DEFERRED</strong></li>
                <li>Disaster recovery: <strong>DEFERRED</strong></li>
                <li>Usage billing: <strong>DEFERRED</strong></li>
                <li>External BaaS readiness: <strong>DEFERRED</strong></li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Beta Navigation Status</h2>
          <div className="grid">
            {navigation.slice(1).map((item) => {
              const isPhase9 = item.label === "Phase 9";
              return (
                <div key={item.href} className="card">
                  <h3 className="card-title">{item.label}</h3>
                  <p style={{ color: "var(--color-text-secondary)", fontSize: "14px" }}>
                    {[
                      "Products, variants, inventory, customers, cart, checkout, orders, refunds",
                      "Branches, staff, product search, barcode/SKU, cart, payments, receipts, returns, daily summaries",
                      "Database, storage, functions, API gateway, events, webhooks, jobs, secrets, backups, usage, billing",
                      "Logs, metrics, audit, correlation traces, outbox, retries, dead letters, health",
                      "Phase 7 status, evidence inbox, ledger, discovery, pilot, release gates, PMF decision",
                      "Environment, tenant, billing, security, integrations",
                      "CRM, Analytics, Automate, Desk, Projects",
                      "Realtime",
                    ][navigation.indexOf(item) - 1]}
                  </p>
                  <span className={`status-badge ${isPhase9 ? "complete" : "pending"}`}>
                    {isPhase9 ? "IMPLEMENTED" : "PENDING IMPLEMENTATION"}
                  </span>
                </div>
              );
            })}
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Current Phase 8 Work</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Completed</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>✓ Transactional outbox migration (kernel.outbox_events)</li>
                <li>✓ Committed-only publish handoff</li>
                <li>✓ FOR UPDATE SKIP LOCKED worker leasing</li>
                <li>✓ Lease ownership + expiry + crash recovery</li>
                <li>✓ Bounded exponential retry scheduling</li>
                <li>✓ Durable publish acknowledgement</li>
                <li>✓ DEAD_LETTER terminal persistence</li>
                <li>✓ Tenant/correlation context preservation</li>
                <li>✓ PostgreSQL integration validation</li>
                <li>✓ Outbox observability structured logging</li>
                <li>✓ Signed source-service allowlist</li>
                <li>✓ Leaked-payload guardrails</li>
                <li>✓ Delivery rate-limit envelope</li>
                <li>✓ Webhook DNS public-address policy</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">In Progress / Next</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Realtime subscriptions</li>
                <li>□ Disaster recovery procedures</li>
                <li>□ Usage metering implementation</li>
                <li>□ External BaaS readiness</li>
                <li>□ Beta UI implementation</li>
                <li>□ Commerce UI (products, inventory, orders)</li>
                <li>□ POS UI (branches, staff, payments)</li>
                <li>□ Backend UI (database, functions, webhooks)</li>
                <li>□ Operations UI (logs, metrics, outbox)</li>
                <li>□ Validation UI (Phase 7 gates, evidence)</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}