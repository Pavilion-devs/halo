"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Info, List } from "lucide-react";

export type TocItem = { id: string; label: string };

export function Callout({ children }: { children: ReactNode }) {
  return (
    <div className="doc-callout">
      <Info size={20} />
      <div>{children}</div>
    </div>
  );
}

export function DocPage({
  eyebrow,
  title,
  description,
  toc,
  children
}: {
  eyebrow: string;
  title: string;
  description?: string;
  toc: TocItem[];
  children: ReactNode;
}) {
  const [active, setActive] = useState<string | undefined>(toc[0]?.id);

  useEffect(() => {
    const headings = toc
      .map((t) => document.getElementById(t.id))
      .filter((el): el is HTMLElement => el !== null);

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActive(visible[0].target.id);
      },
      { rootMargin: "-80px 0px -70% 0px", threshold: 0 }
    );

    headings.forEach((h) => observer.observe(h));
    return () => observer.disconnect();
  }, [toc]);

  return (
    <div className="docs-page">
      <article className="doc-prose">
        <p className="doc-eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        {description && <p className="doc-lead">{description}</p>}
        {children}
      </article>

      <aside className="docs-toc">
        <p className="docs-toc-title">
          <List size={16} />
          On this page
        </p>
        <nav className="docs-toc-list">
          {toc.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className="doc-toc-link"
              data-active={active === item.id}
            >
              {item.label}
            </a>
          ))}
        </nav>
      </aside>
    </div>
  );
}
