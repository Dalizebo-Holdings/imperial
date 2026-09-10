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

export default function Phase10Page() {
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
          <h1 className="page-title">Phase 10</h1>
          <p className="page-subtitle">
            AI & Intelligence
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Phase Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Phase 10 — AI & Intelligence</h3>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
                <span className="status-badge active">ACTIVE</span>
              </div>
              <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", lineHeight: 1.6 }}>
                Phase 9 modules implemented. Phase 10 development began with AI primitives and service layer.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Phase 10 Modules</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">AI Assistant</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Natural language interface</li>
                <li>Context-aware chatbot</li>
                <li>Integration with platform data</li>
                <li>Action execution via AI</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Intelligence Dashboards</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Pre-built insight dashboards</li>
                <li>Custom dashboard builder</li>
                <li>Real-time data visualizations</li>
                <li>Export and sharing capabilities</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Analysis</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Data analysis and processing</li>
                <li>Predictive modeling</li>
                <li>Statistical computations</li>
                <li>Trend and anomaly detection</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Recommendations</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Suggestive actions based on data</li>
                <li>Next best step recommendations</li>
                <li>Personalized user guidance</li>
                <li>Automated workflow triggers</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Architecture Constraints</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">AI Authority</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>✓ Kernel remains authoritative for AI primitives</li>
                <li>✓ No duplicate model storage</li>
                <li>✓ AI services extend without replacing core</li>
                <li>✓ Tenant isolation for AI resources</li>
                <li>✓ Idempotency on all AI mutations</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Integration Requirements</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>AI models versioned and tracked</li>
                <li>Prompt templating system</li>
                <li>Inference and embedding pipelines</li>
                <li>Audit trail for AI decisions</li>
                <li>Shared domain contracts with other modules</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Acceptance Criteria</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">AI Adoption</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Organizations use AI assistant</li>
                <li>□ Intelligence dashboards drive decisions</li>
                <li>□ Analysis improves operational metrics</li>
                <li>□ Recommendations increase conversion</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Target Metrics</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ 25%+ orgs use AI features</li>
                <li>□ AI reduces manual effort by 20%</li>
                <li>□ Recommendation acceptance rate >15%</li>
                <li>□ Forecast accuracy improvement >10%</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}