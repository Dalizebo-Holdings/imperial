"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";

export default function SdkDocumentationPage() {
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
          <h1 className="page-title">SDK & API Documentation</h1>
          <p className="page-subtitle">
            Access SDKs, interactive documentation, and code samples for the Dalizebo Platform
          </p>
        </header>

        <section className="section">
          <div className="grid">
            <div className="card">
              <h3 className="card-title">SDKs</h3>
              <p>
                Download or install officially supported SDKs for your preferred programming language.
                Our SDKs are generated from our API specifications and kept up to date.
              </p>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Python SDK</li>
                <li>JavaScript/TypeScript SDK</li>
                <li>Java SDK</li>
                <li>Go SDK</li>
                <li>.NET SDK</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Documentation</h3>
              <p>
                Interactive API documentation, guides, tutorials, and reference materials.
                Try out API endpoints directly from the documentation.
              </p>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Interactive API Explorer</li>
                <li>Getting Started guides</li>
                <li>Authentication and authorization</li>
                <li>Error handling and troubleshooting</li>
                <li>Best practices and examples</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Code Samples</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Popular Examples</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Creating a project via API</li>
                <li>Managing environments and deployments</li>
                <li>Processing webhook events</li>
                <li>Using the platform's AI services</li>
                <li>Integrating with commerce and POS modules</li>
              </ul>
            </div>

            <div className="card">
              <h3 className="card-title">Language-Specific Samples</h3>
              <p>
                Select your language to see idiomatic code samples and best practices.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}