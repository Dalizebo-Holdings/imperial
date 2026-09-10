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
  { href: "/realtime", label: "Realtime", exact: false },
];

export default function Phase12Page() {
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
          <h1 className="page-title">Phase 12</h1>
          <p className="page-subtitle">
            Multi-Product Platform + ERP Foundations
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Phase Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Phase 12 — Multi-Product Platform + ERP Foundations</h3>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
                <span className="status-badge active">ACTIVE</span>
              </div>
              <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", lineHeight: 1.6 }}">
                Multi-Product Platform and ERP Foundations modules are currently under development.
                This includes product catalog management, inventory synchronization, and unified commerce operations.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Phase 12 Modules</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Multi-Product Platform</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Product catalog management</li>
                <li>Variant and option management</li>
                <li>Inventory tracking and synchronization</li>
                <li>Unified product data model</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">ERP Foundations</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Financial management basics</li>
                <li>Supply chain coordination</li>
                <li>Procurement and purchasing</li>
                <li>Order management and fulfillment</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Unified Commerce Operations</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Centralized order processing</li>
                <li>Inventory availability across channels</li>
                <li>Consistent customer experience</li>
                <li>Real-time data synchronization</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Architecture Constraints</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Product Authority</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>✓ Kernel remains authoritative for product and inventory primitives</li>
                <li>✓ No duplicate product/storage data</li>
                <li>✓ Services extend without replacing core</li>
                <li>✓ Tenant isolation for product data</li>
                <li>✓ Idempotency on all product mutations</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Integration Requirements</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Products and variants versioned and tracked</li>
                <li>Inventory change events via outbox</li>
                <li>Product catalog synchronization</li>
                <li>Audit trail for product and inventory changes</li>
                <li>Shared domain contracts with commerce and POS modules</li>
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
                <li>□ Merchants manage multiple products in the platform</li>
                <li>□ Inventory is synchronized across sales channels</li>
                <li>□ Product catalogs are published to commerce and POS</li>
                <li>□ ERP foundations support core business operations</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Target Metrics</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ 100+ active products managed</li>
                <li>□ Inventory accuracy >98%</li>
                <li>□ Product catalog sync latency <5 seconds</li>
                <li>□ ERP processes automated by 40%</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}