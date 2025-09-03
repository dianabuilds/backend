import { useState } from "react";

import RumTab from "../features/monitoring/RumTab";
import RateLimitsTab from "../features/monitoring/RateLimitsTab";
import CacheTab from "../features/monitoring/CacheTab";
import AuditLogTab from "../features/monitoring/AuditLogTab";
import Jobs from "./Jobs";

const tabs = [
  { id: "rum", label: "RUM", component: <RumTab /> },
  { id: "rate-limits", label: "Rate limits", component: <RateLimitsTab /> },
  { id: "cache", label: "Cache", component: <CacheTab /> },
  { id: "audit-log", label: "Audit log", component: <AuditLogTab /> },
  { id: "jobs", label: "Jobs", component: <Jobs /> },
] as const;

type TabId = (typeof tabs)[number]["id"];

export default function Monitoring() {
  const [active, setActive] = useState<TabId>("rum");

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-lg font-semibold">Monitoring</h1>
      <div
        role="tablist"
        aria-label="Monitoring sections"
        className="flex gap-2 border-b"
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            id={`${tab.id}-tab`}
            role="tab"
            aria-selected={active === tab.id}
            aria-controls={`${tab.id}-panel`}
            onClick={() => setActive(tab.id)}
            className={`px-3 py-1 text-sm border-b-2 ${
              active === tab.id ? "border-blue-500" : "border-transparent"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`${tab.id}-panel`}
          aria-labelledby={`${tab.id}-tab`}
          hidden={active !== tab.id}
          className="mt-4"
        >
          {active === tab.id ? tab.component : null}
        </div>
      ))}
    </div>
  );
}

