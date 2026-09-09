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

export default function POSPage() {
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
            const isPending = [
              "/backend",
              "/operations",
              "/validation",
              "/settings",
            ].includes(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${isActive ? "active" : ""} ${
                  isPending ? "pending" : ""
                }`}
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
          <h1 className="page-title">POS</h1>
          <p className="page-subtitle">
            Branches, staff, product search, barcode/SKU, cart, payments, receipts, returns, daily summaries
          </p>
        </header>

        <div className="grid">
          <div className="card">
            <h3 className="card-title">Branches & Staff</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Multi-branch management with staff roles and permissions.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Branches: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Staff: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Roles: PENDING
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">POS Terminal</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Product search, barcode/SKU lookup, cart, and checkout.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Product Search: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Barcode/SKU: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Cart: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Payments: PENDING
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Receipts & Returns</h3>
            <p style={{ opacity: 0.7, fontSize: "14px", marginBottom: "16px" }}>
              Receipt generation, return processing, and daily summaries.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Receipts: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Returns: PENDING
              </button>
              <button className="status-badge pending" style={{ cursor: "default" }}>
                Daily Summaries: PENDING
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Integration Status</h3>
            <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
              <li>
                <strong>Kernel:</strong> Commerce P0 complete
              </li>
              <li>
                <strong>BaaS:</strong> Events, Webhooks, Jobs, Audit, Logging complete
              </li>
              <li>
                <strong>SaaS:</strong> POS P0 complete (Phase 6)
              </li>
              <li>
                <strong>UI:</strong> <strong>PENDING</strong> — Next.js implementation
              </li>
            </ul>
          </div>
        </div>

        <section className="section">
          <h2 className="section-title">Implementation Plan</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Phase 1: Branch & Staff Setup</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>Branch list and creation</li>
                <li>Staff management with roles</li>
                <li>Branch-specific settings</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Phase 2: POS Terminal</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>Product search with barcode/SKU</li>
                <li>Cart with quantity controls</li>
                <li>Payment method selection</li>
                <li>Receipt preview/print</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Phase 3: Returns & Reporting</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>Return initiation from history</li>
                <li>Daily summary dashboard</li>
                <li>Branch performance comparison</li>
                <li>Shift handoff</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}