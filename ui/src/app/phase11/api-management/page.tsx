"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";

export default function ApiManagementPage() {
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
          {/* We'll reuse the same navigation as the dashboard for consistency */}
        </div>
      </nav>

      <main className="container">
        <header className="page-header">
          <h1 className="page-title">API Management</h1>
          <p className="page-subtitle">
            Discover, manage, and monitor your Dalizebo Platform APIs
          </p>
        </header>

        <section className="section">
          <div className="grid">
            <div className="card">
              <h3 className="card-title">API Discovery</h3>
              <p>
                Browse and search all available APIs in the Dalizebo Platform. Each API is versioned,
                documented, and ready for consumption.
              </p>
            </div>

            <div className="card">
              <h3 className="card-title">API Actions</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>View API documentation and specifications</li>
                <li>Test API endpoints interactively</li>
                <li>Manage API versions and lifecycles</li>
                <li>Set rate limits and quotas</li>
                <li>Monitor API usage and performance</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">API Lifecycle</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Stages</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Design and prototyping</li>
                <li>Development and testing</li>
                <li>Staging and validation</li>
                <li>Production and deprecation</li>
                <li>Retirement and sunset</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Governance</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>API versioning policies</li>
                <li>Backward compatibility guarantees</li>
                <li>Deprecation and migration guidance</li>
                <li>Security and compliance checks</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}