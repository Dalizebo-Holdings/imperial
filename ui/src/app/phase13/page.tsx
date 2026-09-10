import Link from "next/link";

export default function MarketplacePage() {
  return (
    <div className="min-h-screen bg-background">
      <nav className="navbar">
        <Link href="/" className="navbar-brand">
          Dalizebo Platform
        </Link>
        <div className="navbar-links">
          <Link href="/commerce" className="navbar-link">Commerce</Link>
          <Link href="/pos" className="navbar-link">POS</Link>
          <Link href="/backend" className="navbar-link">Backend</Link>
          <Link href="/operations" className="navbar-link">Operations</Link>
          <Link href="/validation" className="navbar-link">Validation</Link>
          <Link href="/settings" className="navbar-link">Settings</Link>
          <Link href="/phase9" className="navbar-link">Phase 9</Link>
          <Link href="/phase10" className="navbar-link">Phase 10</Link>
          <Link href="/phase11" className="navbar-link">Phase 11</Link>
          <Link href="/phase12" className="navbar-link">Phase 12</Link>
          <Link href="/phase13" className="navbar-link active">Marketplace</Link>
          <Link href="/realtime" className="navbar-link">Realtime</Link>
        </div>
      </nav>

      <main className="container">
        <header className="page-header">
          <h1 className="page-title">Marketplace</h1>
          <p className="page-subtitle">
            Buy, sell, and manage products and services within the Dalizebo ecosystem
          </p>
        </header>

        <section className="section">
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Marketplace Overview</h3>
              <p className="card-description">
                The marketplace enables vendors to list products and services,
                customers to discover and purchase items, and administrators to
                monitor transactions and vendor performance.
              </p>
              <div className="status-indicator">
                <span className="status-badge pending">FEATURE_IN_DEVELOPMENT</span>
              </div>
            </div>

            <div className="card">
              <h3 className="card-title">Core Features</h3>
              <ul className="feature-list">
                <li>Product catalog management</li>
                <li>Vendor onboarding and verification</li>
                <li>Secure transaction processing</li>
                <li>Inventory tracking</li>
                <li>Order management</li>
                <li>Review and rating system</li>
                <li>Marketplace analytics</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="section">
          <h2 className="section-title">Coming Soon</h2>
          <div className="grid">
            <div className="card">
              <h3 className="card-title">Vendor Dashboard</h3>
              <p className="card-description">
                Manage your product listings, track sales, and analyze performance
              </p>
            </div>
            <div className="card">
              <h3 className="card-title">Customer Experience</h3>
              <p className="card-description">
                Browse products, make purchases, and track order history
              </p>
            </div>
            <div className="card">
              <h3 className="card-title">Admin Controls</h3>
              <p className="card-description">
                Monitor transactions, manage vendors, and ensure marketplace integrity
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}