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

export default function SettingsPage() {
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

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-link ${isActive ? "active" : ""}`}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <main className="container">
        <header className="page-header">
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">
            Environment, tenant, billing, security, integrations
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Environment</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Current Environment</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge complete">LOCAL</span>
              </div>
              <p style={{ fontSize: "14px", opacity: 0.7 }}>
                Running in local development mode. Connects to local PostgreSQL
                and BaaS services.
              </p>
            </div>
            <div className="card">
              <h3 className="card-title">Available Environments</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>
                  <strong>local:</strong> Development with seeded demo data
                </li>
                <li>
                  <strong>staging:</strong> Pre-production validation (deferred)
                </li>
                <li>
                  <strong>beta:</strong> Limited external access (deferred)
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Tenant Configuration</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Current Tenant</h3>
              <p style={{ fontSize: "14px", opacity: 0.7 }}>
                Demo tenant: <code>demo-org</code> /
                <code>demo-workspace</code> /
                <code>demo-project</code> /
                <code>development</code>
              </p>
            </div>
            <div className="card">
              <h3 className="card-title">Tenant Scoping</h3>
              <p style={{ fontSize: "14px", opacity: 0.7 }}>
                All data operations are scoped to the current tenant.
                Cross-tenant access is blocked at the Kernel and BaaS layers.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Billing & Usage</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Subscription</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">SANDBOX</span>
              </div>
              <p style={{ fontSize: "14px", opacity: 0.7 }}>
                Running in sandbox mode. No real charges. Production billing
                adapters are feature-flagged.
              </p>
            </div>
            <div className="card">
              <h3 className="card-title">Usage Metering</h3>
              <div style={{ display: "flex", gap: "8px", marginBottom: "12px" }}>
                <span className="status-badge pending">DEFERRED</span>
              </div>
              <p style={{ fontSize: "14px", opacity: 0.7 }}>
                Usage metering implementation pending Phase 8 completion.
              </p>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Security</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Authentication</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>✓ Session lifecycle</li>
                <li>✓ API key management</li>
                <li>✓ Service account identity</li>
                <li>✓ Kernel authorization evidence required</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Secrets & Audit</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>✓ Secret references (Vault)</li>
                <li>✓ Kernel Audit authoritative</li>
                <li>✓ No plaintext credentials in code/logs</li>
                <li>✓ Tenant isolation enforced</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Integrations</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Configured</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>✓ Events (Kernel outbox)</li>
                <li>✓ Webhooks (HMAC-SHA256)</li>
                <li>✓ Background Jobs</li>
              </ul>
            </div>
            <div className="card">
              <h3 className="card-title">Deferred</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, opacity: 0.8 }}>
                <li>□ Realtime subscriptions</li>
                <li>□ External webhook endpoints</li>
                <li>□ Third-party integrations</li>
                <li>□ Developer portal</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Demo Data</h2>
          <div className="card">
            <p style={{ fontSize: "14px", opacity: 0.7, marginBottom: "16px" }}>
              Seeded demo data is clearly separated from evidence data. Evidence
              ingestion uses the private inbox workflow; demo fixtures are
              excluded from Phase 7 validation.
            </p>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button className="status-badge complete">Demo Data: SEEDED</button>
              <button className="status-badge complete">Evidence: ISOLATED</button>
              <button className="status-badge pending">Production: BLOCKED</button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}