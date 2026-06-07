import "../theme.css";
import "../dashboard.css";
import "../halo.css";
import "../halo-theme.css";

import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";

export const dynamic = "force-dynamic";

export default function ShellLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="halo-dashboard">
      <div className="shell">
        <Sidebar />
        <div className="main">
          <Topbar />
          <div className="page">{children}</div>
        </div>
      </div>
    </div>
  );
}
