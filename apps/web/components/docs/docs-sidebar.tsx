"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { DOCS_NAV } from "./nav";

export function DocsSidebar() {
  const pathname = usePathname();

  return (
    <aside className="docs-sidebar">
      <nav className="docs-side-nav">
        {DOCS_NAV.map((group) => (
          <div key={group.group}>
            <p className="docs-side-title">{group.group}</p>
            <div className="docs-side-links">
              {group.links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="doc-side-link"
                  data-active={pathname === link.href}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
