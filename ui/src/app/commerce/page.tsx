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

export default function CommercePage() {
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
          <h1 className="page-title">Commerce</h1>
          <p className="page-subtitle">
            Products, variants, inventory, customers, cart, checkout, orders, refunds
          </p>
        </header>

        <div className="grid">
          <div className="card">
            <h3 className="card-title">Products & Variants</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Manage product catalogue with variants, pricing, and attributes.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge pending">Products: PENDING</span>
              <span className="status-badge pending">Variants: PENDING</span>
              <span className="status-badge pending">Inventory: PENDING</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Customers & Cart</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Customer profiles, shopping cart, and session management.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge pending">Customers: PENDING</span>
              <span className="status-badge pending">Cart: PENDING</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Checkout & Orders</h3>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Checkout flow, order management, and fulfillment tracking.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <span className="status-badge pending">Checkout: PENDING</span>
              <span className="status-badge pending">Orders: PENDING</span>
              <span className="status-badge pending">Refunds: PENDING</span>
            </div>
          </div>

          <div className="card">
            <h3 className="card-title">Integration Status</h3>
            <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
              <li><strong>Kernel:</strong> Commerce P0 complete</li>
              <li><strong>BaaS:</strong> Events, Webhooks, Jobs, Audit, Logging complete</li>
              <li><strong>SaaS:</strong> Commerce P0 complete (Phase 6)</li>
              <li><strong>UI:</strong> <strong style={{ color: "var(--color-status-pending)" }}>PENDING</strong> — Next.js implementation</li>
            </ul>
          </div>
        </div>

        <section className="section">
          <h2 className="section-title">Implementation Plan</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Phase 1: Core Commerce UI</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Product list with search/filter</li>
                <li>Product detail with variants</li>
                <li>Inventory display</li>
                <li>Customer list and detail</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Phase 2: Cart & Checkout</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Cart drawer/sidebar</li>
                <li>Multi-step checkout</li>
                <li>Payment integration (sandbox)</li>
                <li>Order confirmation</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Phase 3: Orders & Refunds</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Order list with status</li>
                <li>Order detail timeline</li>
                <li>Refund initiation</li>
                <li>Refund tracking</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}