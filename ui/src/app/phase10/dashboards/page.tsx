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
  { href: "/realtime", label: "Realtime", exact: false },
];

export default function IntelligenceDashboardsPage() {
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
          <h1 className="page-title">Intelligence Dashboards</h1>
          <p className="page-subtitle">
            Visualize Data and Gain Insights
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Intelligence Dashboards Overview</h2>
          <div className="card">
            <p>
              The Intelligence Dashboards module provides pre-built and customizable dashboards
              to visualize data from across the Dalizebo Platform. Users can gain insights into
              their operations, customer behavior, and business performance.
            </p>
            <p className="status-badge complete">
              IMPLEMENTED
            </p>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Features</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Pre-built Dashboards</h3>
              <p>Ready-to-use dashboards for sales, marketing, support, and more.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Custom Dashboard Builder</h3>
              <p>Drag-and-drop interface to create personalized dashboards.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Real-time Data</h3>
              <p>Dashboards update in real-time as data flows through the platform.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Export and Sharing</h3>
              <p>Export dashboards as PDF or PNG, and share with team members.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Drill-down Capabilities</h3>
              <p>Click on visualizations to explore underlying data and details.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}