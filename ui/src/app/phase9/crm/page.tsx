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

export default function CRMPage() {
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
          <h1 className="page-title">CRM</h1>
          <p className="page-subtitle">
            Customer Relationship Management
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">CRM Overview</h2>
          <div className="card">
            <p>
              The CRM module manages customer relationships, interactions, and data.
              It integrates with Commerce and POS to provide a unified customer view.
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
              <h3 className="card-title">Customers</h3>
              <p>Manage customer profiles, contact information, and segmentation.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Contacts</h3>
              <p>Track individual contacts within customer accounts.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Activities</h3>
              <p>Log calls, meetings, emails, and notes related to customers and deals.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Pipeline</h3>
              <p>Manage sales stages, deals, and forecasting.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}