"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/components/Logo";

export default function DeveloperPortalPage() {
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
          {/* In a real app, this might be a separate sidebar or topnav */}
        </div>
      </nav>

      <main className="container">
        <header className="page-header">
          <h1 className="page-title">Developer Portal</h1>
          <p className="page-subtitle">
            Central hub for managing your Dalizebo Platform projects and resources
          </p>
        </header>

        <section className="section">
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Overview</h3>
              <p>
                The Developer Portal provides a unified interface to manage all aspects of your
                developer experience on the Dalizebo Platform. From here you can create and manage
                projects, provision environments, access SDKs and documentation, and monitor usage.
              </p>
            </div>

            <div className="card">
              <h3 className="card-title">Quick Start</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>
                  <Link href="/phase11/developer-portal/projects">Create your first project</Link>
                </li>
                <li>
                  <Link href="/phase11/developer-portal/environments">Set up a development environment</Link>
                </li>
                <li>
                  <Link href="/phase11/sdk-documentation">Get the SDK for your language</Link>
                </li>
                <li>
                  <Link href="/phase11/api-management">Explore and manage your APIs</Link>
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Projects</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Recent Projects</h3>
              {/* Placeholder for project list */}
              <p className="placeholder">No projects yet. <Link href="/phase11/developer-portal/projects/create">Create one</Link>.</p>
            </div>

            <div className="card">
              <h3 className="card-title">Project Actions</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Create new projects</li>
                <li>Archive or delete projects</li>
                <li>Manage project settings and members</li>
                <li>View project activity and logs</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Environments</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Environment Overview</h3>
              <p>
                Provision and manage isolated environments (development, testing, production) for
                each of your projects.
              </p>
            </div>

            <div className="card">
              <h3 className="card-title">Environment Actions</h3>
              <ul style={{ fontSize: "14px", lineHeight: 1.8, color: "var(--color-text-secondary)" }}>
                <li>Create new environments</li>
                <li>Start, stop, and restart environments</li>
                <li>Configure environment variables and secrets</li>
                <li>View resource usage and metrics</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}