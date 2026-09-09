"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { href: "/", label: "Dashboard", exact: true },
  { href: "/commerce", label: "Commerce", exact: false },
  { href: "/pos", label: "POS", exact: false },
  { href: "/backend", label: "Backend", exact: false },
  { href: "/operations", label: "Operations", exact: false },
  { href: "/validation", label: "Validation", exact: false },
  { href: "/settings", label: "Settings", exact: false },
];

export default function BackendPage() {
  const pathname = usePathname();

  return (
    <div className="min-h-screen">
      <nav className="nav" role="navigation" aria-label="Main navigation">
        <div className="nav-brand">
          <Link href="/" style={{ textDecoration: "none" }}>
            Dalizebo Platform <span className="beta-badge">Beta 0.1</span>
          </Link>
        </div>
        <div className="nav-links">
          {navigation.map((item) => {
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);
            const isPending = ["/operations", "/validation", "/settings"].includes(item.href);

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
          <h1 className="page-title">Backend</h1>
          <p className="page-subtitle">
            Database, storage, functions, API gateway, events, webhooks, jobs, secrets, backups, usage, billing
          </p>
        </header>

        <div className="grid">
          <div className="card">
            <h3 className="card-title">Data & Storage</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              PostgreSQL databases, object storage, and data management.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Database: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Storage: PENDING
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Compute & API</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Serverless functions, API gateway, and API management.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Functions: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                API Gateway: PENDING
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Events & Integration</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Event streams, webhooks, background jobs, and integrations.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Events: COMPLETE
              </button>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Webhooks: COMPLETE
              </button>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Jobs: COMPLETE
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Integrations: PENDING
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Security & Operations</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Secrets management, backups, usage metering, and billing.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Secrets: COMPLETE
              </button>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Backups: COMPLETE
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Usage: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Billing: PENDING
              </button>
            </div>
          </div>
        </div>

        <section className="section">
          <h2 className="section-title">BaaS P0 Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Complete Services</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>✓ PostgreSQL Database BaaS</li>
                <li>✓ Object Storage</li>
                <li>✓ Serverless Functions</li>
                <li>✓ API Gateway</li>
                <li>✓ Events (with outbox)</li>
                <li>✓ Webhooks (HMAC-SHA256)</li>
                <li>✓ Background Jobs</li>
                <li>✓ Audit (Kernel-authoritative)</li>
                <li>✓ Logging (Kernel-structured)</li>
                <li>✓ Subscription Billing</li>
                <li>✓ Payment Abstraction</li>
                <li>✓ Currency Conversion</li>
                <li>✓ Secrets</li>
                <li>✓ Backups</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Deferred</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>□ Usage Metering</li>
                <li>□ Realtime subscriptions</li>
                <li>□ Disaster recovery procedures</li>
                <li>□ External BaaS readiness</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}