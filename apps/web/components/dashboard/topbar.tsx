import { Bell, Mail } from "lucide-react";

import { HaloSearch } from "@/components/dashboard/halo-search";

export function Topbar() {
  return (
    <header className="topbar">
      <HaloSearch />

      <div className="tb-right">
        <button className="icon-btn" type="button" aria-label="War room updates (coming soon)" title="Coming soon">
          <Mail />
        </button>
        <button className="icon-btn has-badge" type="button" aria-label="Alerts (coming soon)" title="Coming soon">
          <Bell />
          <span className="dot" />
        </button>
      </div>
    </header>
  );
}
