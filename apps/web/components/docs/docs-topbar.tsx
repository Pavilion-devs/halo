import Link from "next/link";
import { Search, Github, ArrowUpRight } from "lucide-react";
import { DOCS_GITHUB_URL } from "./nav";

export function DocsTopbar() {
  return (
    <header className="docs-topbar">
      <div className="docs-topbar-inner">
        <Link href="/" className="docs-logo" aria-label="Halo">
          <span className="docs-logo-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
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
          <span className="docs-logo-name">Halo</span>
        </Link>

        <div className="docs-search">
          <Search size={16} />
          <span>Search…</span>
          <kbd>⌘K</kbd>
        </div>

        <nav className="docs-topbar-nav">
          <a
            href={DOCS_GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="docs-github-btn"
          >
            <Github size={16} />
            <span>View on GitHub</span>
            <ArrowUpRight size={14} className="docs-github-btn-arrow" />
          </a>
        </nav>
      </div>
    </header>
  );
}
