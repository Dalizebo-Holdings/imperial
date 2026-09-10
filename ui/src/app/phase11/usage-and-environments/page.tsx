"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";

export default function UsageAndEnvironmentsPage() {
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
          <h1 className="page-title">Usage & Environments</h1>
          <p className="page-subtitle">
            Monitor usage, manage environments, and track resource consumption
          </p>
        </header>

        <section className="section">
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Usage Overview</h3>
              <p>
                Track API usage, compute resources, storage, and other metrics
                across your projects and environments.
              </p>
            </div>

            <div className="card">
              <h3 className="card-title">Usage Actions</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>View real-time and historical usage</li>
                <li>Set usage alerts and budgets</li>
                <li>Export usage reports</li>
                <li>Integrate with billing systems</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Environments</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Environment Management</h3>
              <p>
                Provision, configure, and manage isolated environments for
                development, testing, and production.
              </p>
            </div>

            <div className="card">
              <h3 className="card-title">Environment Types</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Development</li>
                <li>Testing</li>
                <li>Staging</li>
                <li>Production</li>
                <li>Preview/Branch environments</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Resource Isolation</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Isolation & Security</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Tenant and project isolation</li>
                <li>Environment-level resource quotas</li>
                <li>Network segmentation and security groups</li>
                <li>Secrets and configuration management</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Compliance</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Data residency controls</li>
                <li>Audit logging and access controls</li>
                <li>Encryption at rest and in transit</li>
                <li>Regular security assessments</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}