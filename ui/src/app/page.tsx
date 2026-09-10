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
  { href: "/phase10", label: "Phase 10", exact: false },
  { href: "/phase11", label: "Phase 11", exact: false },
  { href: "/phase12", label: "Phase 12", exact: false },
  { href: "/phase13", label: "Phase 13", exact: false },
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
              "/phase10",
              "/phase11",
              "/phase12",
              "/phase13",
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
            Dalizebo Imperial Platform — Phase 13 Development
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
                <span className="status-badge complete">COMPLETE</span>
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
              </ul
        </section>

        <section className="section">
          <h2 className="section-title">Beta Navigation Status</h2>
          <div className="grid">
            {navigation.slice(1).map((item) => {
              const isPhase9 = item.label === "Phase 9";
              const isPhase10 = item.label === "Phase 10";
              const isPhase11 = item.label === "Phase 11";
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
                      "AI assistant, intelligence dashboards, analysis, recommendations",
                      "Developer portal, API management, SDK/API documentation, usage, projects/environments",
                      "Realtime",
                    ][navigation.indexOf(item) - 1]}
                  </p>
                  <span className={`status-badge ${isPhase9 || isPhase10 || isPhase11 ? "complete" : "pending"}`}>
                    {isPhase9 || isPhase10 || isPhase11 ? "IMPLEMENTED" : "PENDING IMPLEMENTATION"}
                  </span>
                </div>
              );
            })}
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Current Phase 13 Work</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Completed</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>✓ Defined Marketplace primitives in Kernel (Listing, Transaction, Vendor, Product)</li>
                <li>✓ Implemented Marketplace service layer in SaaS</li>
                <li>✓ Beta UI updated to include Phase 13 navigation</li>
                <li>✓ Dashboard updated to reflect Phase 13 development</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">In Progress / Next</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Build marketplace core UI</li>
                <li>□ Build vendor management UI</li>
                <li>□ Build product listing UI</li>
                <li>□ Build transaction handling UI</li>
                <li>□ Build marketplace analytics UI</li>
                <li>□ Connect Marketplace modules to platform events via outbox</li>
                <li>□ Add Marketplace-specific health checks and observability</li>
                <li>□ Write unit and integration tests for Marketplace components</li>
                <li>□ Update documentation and acceptance tests</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}