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
  { href: "/realtime", label: "Realtime", exact: false },
];

export default function Phase11Page() {
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
          <h1 className="page-title">Phase 11</h1>
          <p className="page-subtitle">
            Developer Cloud
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Phase Status</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Phase 11 — Developer Cloud</h3>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
                <span className="status-badge active">ACTIVE</span>
              </div>
              <p style={{ color: "var(--color-text-secondary)", fontSize: "14px", lineHeight: 1.6 }}>
                Developer Cloud modules are currently under development. This includes developer portal,
                API management, SDK/API documentation, and usage/projects/environments tracking.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Phase 11 Modules</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Developer Portal</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Central hub for developers</li>
                <li>Project and environment management</li>
                <li>API key generation and management</li>
                <li>Access to SDKs and documentation</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">API Management</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>API discovery and documentation</li>
                <li>Rate limiting and quota management</li>
                <li>API versioning and lifecycle</li>
                <li>Developer analytics and usage metrics</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">SDK/API Documentation</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Auto-generated SDKs for multiple languages</li>
                <li>Interactive API documentation</li>
                <li>Code samples and tutorials</li>
                <li>SDK versioning and distribution</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Usage and Projects/Environments</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Project creation and organization</li>
                <li>Environment provisioning (dev, test, prod)</li>
                <li>Usage tracking and billing integration</li>
                <li>Resource isolation and security</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Architecture Constraints</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Developer Authority</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>✓ Kernel remains authoritative for Developer Cloud primitives</li>
                <li>✓ No duplicate project/environment storage</li>
                <li>✓ Services extend without replacing core</li>
                <li>✓ Tenant isolation for developer resources</li>
                <li>✓ Idempotency on all Developer Cloud mutations</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Integration Requirements</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Projects and environments versioned and tracked</li>
                <li>SDK generation pipeline</li>
                <li>Documentation management system</li>
                <li>Audit trail for developer actions</li>
                <li>Shared domain contracts with other modules</li>
                <li>Events emitted via outbox for developer activities</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Acceptance Criteria</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Developer Adoption</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ Developers use the portal to manage projects</li>
                <li>□ SDKs are generated and consumed by external developers</li>
                <li>□ API management drives internal and external API usage</li>
                <li>□ Usage tracking informs billing and resource allocation</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Target Metrics</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>□ 50+ active developer projects</li>
                <li>□ SDK adoption by 25% of projects</li>
                <li>□ API management reduces integration time by 30%</li>
                <li>□ Usage tracking accuracy >95%</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}