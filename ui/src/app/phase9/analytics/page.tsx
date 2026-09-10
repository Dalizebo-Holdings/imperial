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

export default function AnalyticsPage() {
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
          <h1 className="page-title">Analytics</h1>
          <p className="page-subtitle">
            Cross-product operational and commercial intelligence
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Analytics Overview</h2>
          <div className="card">
            <p>
              The Analytics module provides insights across all platform modules,
              enabling data-driven decision making through metrics, dashboards,
              reports, and exports.
            </p>
            <p className="status-badge pending">
              PENDING IMPLEMENTATION
            </p>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Features</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Metrics</h3>
              <p>Define and compute key performance indicators across modules.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Dashboards</h3>
              <p>Pre-built and custom dashboards for visualizing metrics.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Reports</h3>
              <p>Scheduled and ad-hoc reports for deeper analysis.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Exports</h3>
              <p>Export reports in various formats (CSV, JSON, PDF).</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}