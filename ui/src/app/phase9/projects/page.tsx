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

export default function ProjectsPage() {
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
          <h1 className="page-title">Projects</h1>
          <p className="page-subtitle">
            Project and Task Management
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Projects Overview</h2>
          <div className="card">
            <p>
              The Projects module enables project and task management across the Dalizebo Platform.
              It provides tools for planning, tracking, and collaborating on projects, tasks, and teams.
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
              <h3 className="card-title">Projects</h3>
              <p>Create and manage projects with timelines, budgets, and ownership.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Tasks</h3>
              <p>Break down projects into tasks with assignments, dependencies, and progress tracking.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Teams</h3>
              <p>Organize team members and assign roles within projects.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Timeline</h3>
              <p>Visualize project schedules with Gantt charts and milestones.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Reports</h3>
              <p>Track project progress, team capacity, and resource utilization.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}