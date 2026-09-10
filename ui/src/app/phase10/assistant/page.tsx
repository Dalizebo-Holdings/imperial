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

export default function AIAssistantPage() {
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
          <h1 className="page-title">AI Assistant</h1>
          <p className="page-subtitle">
            Natural Language Interface for the Dalizebo Platform
          </p>
        </header>

        <section className="section">
          <h2 className="section-title">AI Assistant Overview</h2>
          <div className="card">
            <p>
              The AI Assistant provides a natural language interface to interact with the Dalizebo Platform.
              Users can ask questions, execute commands, and retrieve information through conversational AI.
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
              <h3 className="card-title">Conversational Interface</h3>
              <p>Chat-based interaction with context awareness and memory.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Command Execution</h3>
              <p>Execute platform operations via natural language commands.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Data Retrieval</h3>
              <p>Fetch and analyze data from Commerce, CRM, Analytics, and other modules.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Action Suggestions</h3>
              <p>Get proactive suggestions based on user behavior and platform data.</p>
            </div>
            <div className="card">
              <h3 className="card-title">Integration</h3>
              <p>Seamless integration with existing platform services and workflows.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}