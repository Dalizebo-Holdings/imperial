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

export default function Phase9Page() {
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
              "/pos",
              "/backend",
              "/operations",
              "/validation",
              "/settings",
              "/phase9",
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
          <h1 className="page-title">Phase 9</h1>
          <p className="page-subtitle">
            CRM + Analytics + Automate + Desk + Projects
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Phase Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Phase 9 — CRM + Analytics + Automate + Desk + Projects</h3>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
                <span className="status-badge pending">PENDING</span>
              </div>
              <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", lineHeight: 1.6 }}>
                Phase 8 outbox hardening complete. Phase 9 implementation begins
                with five new product modules built on shared Kernel/BaaS authority.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Phase 9 Modules</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">CRM</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Customers (shared with Commerce)</li>
                <li>Contacts</li>
                <li>Activities (calls, meetings, emails, notes)</li>
                <li>Pipeline (deals, stages, forecasting)</li>
                <li>Campaigns</li>
                <li>Segments</li>
                <li>Reports</li>
                <li>Cross-product customer context</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Analytics</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Warehouse (shared data model)</li>
                <li>Metrics (definitions, computation)</li>
                <li>Dashboards (pre-built, custom)</li>
                <li>Reports (scheduled, ad-hoc)</li>
                <li>Exports</li>
                <li>Cross-product event ingestion</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Automate</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Triggers (event, schedule, webhook)</li>
                <li>Workflows (DAG, conditional logic)</li>
                <li>Actions (API, function, notification)</li>
                <li>Runs (execution, retry, observability)</li>
                <li>Templates</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Desk</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Tickets (creation, assignment, SLA)</li>
                <li>Queues (routing, prioritization)</li>
                <li>Knowledge (articles, search)</li>
                <li>Reports (volume, SLA, CSAT)</li>
                <li>Customer context integration</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Projects</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Projects (creation, hierarchy)</li>
                <li>Tasks (assignment, dependencies, timeline)</li>
                <li>Teams (membership, roles)</li>
                <li>Reports (progress, capacity)</li>
                <li>Timeline (Gantt, milestones)</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Architecture Constraints</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Authority Boundaries</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>✓ No duplicate customer authority</li>
                <li>✓ No duplicate order authority</li>
                <li>✓ No duplicate payment authority</li>
                <li>✓ Kernel remains authoritative</li>
                <li>✓ BaaS extends without replacing</li>
                <li>✓ SaaS modules share via events</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Integration Requirements</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>APIs remain versioned</li>
                <li>Cross-product events documented</li>
                <li>Audit context preserved</li>
                <li>Tenant isolation enforced</li>
                <li>Idempotency on all mutations</li>
                <li>Shared domain contracts</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Acceptance Criteria</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Product Adoption</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Customers use Commerce/POS with CRM</li>
                <li>□ Analytics reports across shared data</li>
                <li>□ Automate reacts to platform events</li>
                <li>□ Desk accesses customer context</li>
                <li>□ Projects reuse organization identity</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Target Metrics</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ 30%+ orgs use 2+ modules</li>
                <li>□ Cross-product event flow</li>
                <li>□ Shared customer 360 view</li>
                <li>□ Unified billing/usage</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Implementation Order</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">1. CRM Foundation</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Shared customer model with Commerce</li>
                <li>Contacts and activities</li>
                <li>Pipeline with deal stages</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">2. Analytics Warehouse</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Event ingestion from all modules</li>
                <li>Metrics computation engine</li>
                <li>Pre-built dashboards</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">3. Automate Engine</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Trigger system (events, schedules)</li>
                <li>Workflow DAG executor</li>
                <li>Action adapters</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">4. Desk + Projects</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Ticket queues with SLA</li>
                <li>Knowledge base</li>
                <li>Project/task management</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}