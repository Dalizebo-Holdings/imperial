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

export default function OperationsPage() {
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
            const isPending = ["/validation", "/settings"].includes(item.href);

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
          <h1 className="page-title">Operations</h1>
          <p className="page-subtitle">
            Logs, metrics, audit, correlation traces, outbox, retries, dead letters, health
          </p>
        </header>

        <div className="grid">
          <div className="card">
            <h3 className="card-title">Observability</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Structured logs, metrics, and distributed traces.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Logs: COMPLETE
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Metrics: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Traces: PENDING
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Audit & Compliance</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Kernel-authoritative audit trail with tamper evidence.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Audit: COMPLETE
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Compliance: PENDING
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Outbox Operations</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Transactional outbox monitoring and debugging.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Outbox: COMPLETE
              </button>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Retries: COMPLETE
              </button>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Dead Letters: COMPLETE
              </button>
              <button className="status-badge complete" style={{ cursor: "default" }}>
                Rate Limits: COMPLETE
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">System Health</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Health checks, capacity, and operational readiness.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Health: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Capacity: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                DR: PENDING
              </button>
            </div>
          </div>
        </div>

        <section className="section">
          <h2 className="section-title">Phase 8 Outbox Operations Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Implemented & Validated</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>✓ Kernel outbox event state authoritative</li>
                <li>✓ Committed-only publish handoff</li>
                <li>✓ FOR UPDATE SKIP LOCKED worker leasing</li>
                <li>✓ Lease ownership + expiry</li>
                <li>✓ Atomic claim semantics</li>
                <li>✓ Exponential retry scheduling</li>
                <li>✓ Durable publish acknowledgement</li>
                <li>✓ DEAD_LETTER terminal persistence</li>
                <li>✓ Crash/expired-lease recovery</li>
                <li>✓ Tenant/correlation preservation</li>
                <li>✓ Concurrency validation</li>
                <li>✓ PostgreSQL integration validation</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Observability Implemented</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>✓ Structured log contract</li>
                <li>✓ Claim/lease/refresh/release events</li>
                <li>✓ Delivery published/retry/dead-letter events</li>
                <li>✓ Emitter identity binding</li>
                <li>✓ Signed source-service allowlist</li>
                <li>✓ Leaked-payload guardrails</li>
                <li>✓ Delivery rate-limit envelope</li>
                <li>✓ Kernel redaction preservation</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Deferred</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>□ Production outbox worker scheduler</li>
                <li>□ Operational observability pipeline</li>
                <li>□ Real-time outbox dashboard</li>
                <li>□ Alerting on dead-letter accumulation</li>
                <li>□ Automated retry/backoff tuning</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}