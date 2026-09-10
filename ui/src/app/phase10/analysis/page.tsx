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

export default function AnalysisPage() {
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
          <h1 className="page-title">Analysis</h1>
          <p className="page-subtitle">
            Data Analysis and Predictive Modeling
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Analysis Overview</h2>
          <div className="card">
            <p>
              The Analysis module provides data analysis, statistical computations, and predictive modeling
              capabilities. Users can analyze data from across the platform to uncover trends, patterns, and insights.
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
              <h3 className="card-title">Data Processing</h3>
              <p>Clean, transform, and aggregate data from multiple sources.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Statistical Analysis</h3>
              <p>Descriptive statistics, hypothesis testing, and correlation analysis.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Predictive Modeling</h3>
              <p>Build and deploy machine learning models for forecasting and classification.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Trend and Anomaly Detection</h3>
              <p>Identify trends, seasonal patterns, and outliers in data.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Integration</h3>
              <p>Seamless integration with Analytics, CRM, Commerce, and other modules.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}