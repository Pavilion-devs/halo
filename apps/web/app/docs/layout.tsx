import "./docs.css";

import { DocsTopbar } from "@/components/docs/docs-topbar";
import { DocsSidebar } from "@/components/docs/docs-sidebar";

export default function DocsLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="halo-docs">
      <DocsTopbar />
      <div className="docs-body">
        <DocsSidebar />
        <main className="docs-main">{children}</main>
      </div>
    </div>
  );
}
