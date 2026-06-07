"use client";

import {
  Activity,
  Bell,
  FileSearch,
  LayoutDashboard,
  Settings,
  Shield,
  Siren
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type NavItem = {
  label: string;
  href: string;
  icon: ReactNode;
  badge?: string;
  disabled?: boolean;
};

const MENU: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: <LayoutDashboard /> },
  { label: "Incidents", href: "/incidents", icon: <Siren /> },
  { label: "Evidence", href: "/evidence", icon: <FileSearch />, disabled: true },
  { label: "Alerts", href: "/alerts", icon: <Bell />, disabled: true },
  { label: "Traces", href: "/traces", icon: <Activity />, disabled: true },
  { label: "Modes", href: "/modes", icon: <Shield />, disabled: true },
  { label: "Settings", href: "/settings", icon: <Settings />, disabled: true }
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sb">
      <Link href="/" className="brand" aria-label="Halo — home">
        <span className="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <title>Halo</title>
            <ellipse cx="12" cy="9.5" rx="8" ry="3.4" stroke="currentColor" strokeWidth="2.1" />
            <path
              d="M5 13.5c1.4 2.1 4 3.5 7 3.5s5.6-1.4 7-3.5"
              stroke="currentColor"
              strokeWidth="2.1"
              strokeLinecap="round"
              opacity={0.55}
            />
          </svg>
        </span>
        <span className="brand-name">Halo</span>
      </Link>

      <div className="sb-section">Menu</div>
      <nav className="sb-nav">
        {MENU.map((item) => {
          if (item.disabled) {
            return (
              <span
                key={item.label}
                className="sb-link disabled"
                aria-disabled="true"
                title="Coming soon"
              >
                {item.icon}
                {item.label}
                <span className="sb-badge soon">soon</span>
              </span>
            );
          }
          const active =
            item.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.label}
              className={active ? "sb-link active" : "sb-link"}
              href={item.href}
            >
              {item.icon}
              {item.label}
              {item.badge ? <span className="sb-badge">{item.badge}</span> : null}
            </Link>
          );
        })}
      </nav>

      <div className="sb-spacer" />
    </aside>
  );
}
