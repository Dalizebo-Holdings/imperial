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

export default function DeskPage() {
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
          <h1 className="page-title">Desk</h1>
          <p className="page-subtitle">
            Customer Support and Service Management
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Desk Overview</h2>
          <div className="card">
            <p>
              The Desk module provides customer support, ticketing, knowledge base,
              and service level agreement management. It helps teams manage customer
              inquiries, track issues, and deliver timely resolutions.
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
              <h3 className="card-title">Tickets</h3>
              <p>Create, assign, and track customer support tickets with SLAs.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Queues</h3>
              <p>Route tickets to the right teams based on skills, workload, or priority.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Knowledge Base</h3>
              <p>Create and share articles to help customers and agents find answers quickly.</p>
            </div>
            <div className="card">
              <h3 className="card-title">SLAs</h3>
              <p>Define and monitor service level agreements for response and resolution times.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Reports</h3>
              <p>Track ticket volume, agent performance, and customer satisfaction.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}