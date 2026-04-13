import Link from "next/link";
import { ReactNode } from "react";

import { AuthUser } from "@/lib/types";
import { ThemeToggle } from "@/components/ThemeToggle";
import { UserDropdown } from "@/components/UserDropdown";

export function AppShell({
  title,
  eyebrow,
  children,
  currentUser
}: {
  title: string;
  eyebrow: string;
  children: ReactNode;
  currentUser: AuthUser | null;
}) {
  const navItems = [
    { href: "/alerts", label: "Alerts" },
    { href: "/agents", label: "Agents" }
  ];

  if (currentUser?.is_superuser) {
    navItems.push({ href: "/users", label: "Users" });
    navItems.push({ href: "/audit-logs", label: "Audit Logs" });
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">SOC</span>
          <div>
            <p className="eyebrow">Repo B MVP</p>
            <h1>soc-dashboard</h1>
          </div>
        </div>
        <nav className="nav">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="nav-link">
              {item.label}
            </Link>
          ))}
        </nav>
        <p className="sidebar-note">
          Indexer-first for alerts and search. API-assisted for agent inventory.
        </p>
      </aside>

      <main className="content">
        <header className="top-header">
          <div className="page-header">
            <p className="eyebrow">{eyebrow}</p>
            <h2>{title}</h2>
          </div>
          <div className="header-actions">
            <ThemeToggle />
            {currentUser ? <UserDropdown currentUser={currentUser} /> : null}
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
