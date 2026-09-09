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

export default function BackendPage() {
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
            const isPending = ["/operations", "/validation", "/settings", "/phase9", "/realtime"].includes(item.href);

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
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              PostgreSQL databases, object storage, and data management.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge pending">Database: PENDING</span>
              <span className="status-badge pending">Storage: PENDING</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Compute & API</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Serverless functions, API gateway, and API management.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge pending">Functions: PENDING</span>
              <span className="status-badge pending">API Gateway: PENDING</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Events & Integration</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Event streams, webhooks, background jobs, and integrations.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge complete">Events: COMPLETE</span>
              <span className="status-badge complete">Webhooks: COMPLETE</span>
              <span className="status-badge complete">Jobs: COMPLETE</span>
              <span className="status-badge pending">Integrations: PENDING</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Security & Operations</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Secrets management, backups, usage metering, and billing.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge complete">Secrets: COMPLETE</span>
              <span className="status-badge complete">Backups: COMPLETE</span>
              <span className="status-badge pending">Usage: PENDING</span>
              <span className="status-badge pending">Billing: PENDING</span>
            </div>
          </div>
        </div>

        <section className="section">
          <h2 className="section-title">BaaS P0 Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Complete Services</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
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
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
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