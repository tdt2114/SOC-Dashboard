import { ReactNode } from "react";

import { AuthUser } from "@/lib/types";
import { NotificationBell } from "@/components/NotificationBell";
import { SidebarNavLink } from "@/components/SidebarNavLink";
import { ThemeToggle } from "@/components/ThemeToggle";
import { UserDropdown } from "@/components/UserDropdown";

type NavItem = {
  href: string;
  label: string;
};

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
  const canUseAnalystWorkflow =
    currentUser?.is_superuser || currentUser?.roles.some((role) => role === "admin" || role === "analyst");
  const navSections: Array<{ title: string; items: NavItem[] }> = [
    {
      title: "Operations",
      items: [
        { href: "/dashboard", label: "Dashboard" },
        { href: "/alerts", label: "Alerts" },
        { href: "/agents", label: "Agents" }
      ]
    }
  ];

  if (canUseAnalystWorkflow) {
    navSections.push({
      title: "Workflow",
      items: [{ href: "/cases", label: "Cases" }]
    });
  }

  if (currentUser?.is_superuser) {
    navSections.push({
      title: "Administration",
      items: [
        { href: "/users", label: "Users" },
        { href: "/audit-logs", label: "Audit Logs" },
        { href: "/settings", label: "Settings" }
      ]
    });
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">SOC</span>
          <div>
            <p className="eyebrow">Repo B Operations</p>
            <h1>soc-dashboard</h1>
          </div>
        </div>
        <nav className="nav">
          {navSections.map((section) => (
            <div className="nav-section" key={section.title}>
              <p className="nav-section-title">{section.title}</p>
              {section.items.map((item) => (
                <SidebarNavLink
                  key={item.href}
                  href={item.href}
                  label={item.label}
                />
              ))}
            </div>
          ))}
        </nav>
        <p className="sidebar-note">
          Live SOC workspace with Indexer search, Wazuh agent context, cases, exports, and admin audit controls.
        </p>
      </aside>

      <main className="content">
        <header className="top-header">
          <div className="page-header">
            <p className="eyebrow">{eyebrow}</p>
            <h2>{title}</h2>
          </div>
          <div className="header-actions">
            {currentUser ? <NotificationBell /> : null}
            <ThemeToggle />
            {currentUser ? <UserDropdown currentUser={currentUser} /> : null}
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
