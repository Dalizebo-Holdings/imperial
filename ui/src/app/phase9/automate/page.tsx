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

export default function AutomatePage() {
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
          <h1 className="page-title">Automate</h1>
          <p className="page-subtitle">
            Workflow Automation and Orchestration
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Automate Overview</h2>
          <div className="card">
            <p>
              The Automate module enables workflow automation, triggering, and orchestration
              across the Dalizebo Platform. It provides a scalable engine for building automated
              workflows that respond to events, schedules, and webhooks.
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
              <h3 className="card-title">Triggers</h3>
              <p>Start workflows based on events, schedules, or webhooks.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Workflows</h3>
              <p>Define workflow logic using DAG structures with conditional branching.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Actions</h3>
              <p>Perform operations like API calls, function executions, and notifications.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Runs</h3>
              <p>Execute, monitor, and manage workflow executions with retry and observability.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Templates</h3>
              <p>Reuse workflow patterns across teams and organizations.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}