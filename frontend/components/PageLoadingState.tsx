export function PageLoadingState({
  title = "Loading workspace",
  rows = 5
}: {
  title?: string;
  rows?: number;
}) {
  return (
    <div className="shell loading-shell" aria-live="polite" aria-busy="true">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">SOC</span>
          <div className="loading-brand-copy">
            <span className="skeleton skeleton-eyebrow" />
            <span className="skeleton skeleton-title-small" />
          </div>
        </div>
        <div className="nav">
          <span className="skeleton skeleton-nav" />
          <span className="skeleton skeleton-nav" />
          <span className="skeleton skeleton-nav" />
          <span className="skeleton skeleton-nav" />
        </div>
        <span className="skeleton skeleton-note" />
      </aside>

      <main className="content">
        <div className="loading-header">
          <div>
            <span className="skeleton skeleton-eyebrow" />
            <span className="skeleton skeleton-title" />
          </div>
          <span className="skeleton skeleton-button" />
        </div>
        <p className="sr-only">{title}</p>
        <section className="panel stack">
          <div className="loading-grid">
            <span className="skeleton skeleton-card" />
            <span className="skeleton skeleton-card" />
            <span className="skeleton skeleton-card" />
          </div>
          <div className="loading-table">
            {Array.from({ length: rows }).map((_, index) => (
              <span key={index} className="skeleton skeleton-row" />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
