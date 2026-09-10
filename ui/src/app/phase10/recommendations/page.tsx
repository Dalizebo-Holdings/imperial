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
  { href: "/realtime", label: "Realtime", exact: false },
];

export default function RecommendationsPage() {
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
          <h1 className="page-title">Recommendations</h1>
          <p className="page-subtitle">
            Suggestive Actions and Next Best Steps
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">Recommendations Overview</h2>
          <div className="card">
            <p>
              The Recommendations module provides suggestive actions and next best steps based on user behavior,
              platform data, and AI models. It helps users make informed decisions and take proactive actions.
            </p>
            <p className="status-badge complete">
              IMPLEMENTED
            </p>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Features</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Next Best Step</h3>
              <p>AI-driven suggestions for the next best action to take.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Personalized Recommendations</h3>
              <p>Recommendations tailored to individual user preferences and history.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Action Triggers</h3>
              <p>Recommendations that can trigger automated workflows or notifications.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Integration</h3>
              <p>Seamless integration with CRM, Commerce, Analytics, and other modules.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}