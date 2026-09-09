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

export default function RealtimePage() {
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
          <h1 className="page-title">Realtime</h1>
          <p className="page-subtitle">
            Database change subscriptions, inventory updates, order updates, presence, application events
          </p>
        </header>

        <div className="grid">
          <div className="card">
            <h3 className="card-title">Subscription Types</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Real-time event subscriptions with filtering and cursor-based pagination.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge complete">Database Changes: COMPLETE</span>
              <span className="status-badge complete">Inventory Updates: COMPLETE</span>
              <span className="status-badge complete">Order Updates: COMPLETE</span>
              <span className="status-badge complete">Presence: COMPLETE</span>
              <span className="status-badge complete">Application Events: COMPLETE</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Filter Operators</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Rich filtering for precise event selection.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge complete">EQUALS</span>
              <span className="status-badge complete">NOT_EQUALS</span>
              <span className="status-badge complete">IN</span>
              <span className="status-badge complete">NOT_IN</span>
              <span className="status-badge complete">GT</span>
              <span className="status-badge complete">GTE</span>
              <span className="status-badge complete">LT</span>
              <span className="status-badge complete">LTE</span>
              <span className="status-badge complete">LIKE</span>
              <span className="status-badge complete">ILIKE</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Advanced Features</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Cursor-based pagination and connection lifecycle.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge complete">Cursor Filtering</span>
              <span className="status-badge complete">Connection Lifecycle</span>
              <span className="status-badge complete">Tenant Isolation</span>
              <span className="status-badge complete">Kernel Auth</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Integration Status</h3>
            <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
              <li><strong>Kernel:</strong> Authorization evidence required</li>
              <li><strong>BaaS:</strong> Events, Webhooks, Jobs, Audit, Logging complete</li>
              <li><strong>Realtime:</strong> <strong style={{ color: "var(--color-status-complete)" }}>COMPLETE</strong> (Phase 8)</li>
              <li><strong>UI:</strong> <strong style={{ color: "var(--color-status-pending)" }}>PENDING</strong> — Next.js implementation</li>
            </ul>
          </div>
        </div>

        <section className="section">
          <h2 className="section-title">Implementation Summary</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Subscription Management</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Create subscriptions with kind, resource_type, filters, cursor</li>
                <li>Delete subscriptions (cleans up connections)</li>
                <li>List subscriptions (tenant-scoped)</li>
                <li>Get subscription details</li>
                <li>Connection stats</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Connection Lifecycle</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Connect to subscription (one connection per subscription)</li>
                <li>Duplicate connection rejection</li>
                <li>Disconnect</li>
                <li>Auto-cleanup on subscription deletion</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Broadcast & Filtering</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Broadcast to matching subscriptions by kind + resource_type</li>
                <li>Field-level filters (10 operators)</li>
                <li>Cursor-based filtering (only newer events)</li>
                <li>Cross-tenant isolation enforced</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Security</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Kernel authorization evidence required (kernel_auth_*)</li>
                <li>Tenant isolation at subscription, connection, broadcast levels</li>
                <li>Cross-tenant access denied at all levels</li>
                <li>Filter operator validation</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}