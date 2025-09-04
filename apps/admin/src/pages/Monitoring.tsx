import TabRouter from "../components/TabRouter";
import AuditLogTab from "../features/monitoring/AuditLogTab";
import CacheTab from "../features/monitoring/CacheTab";
import JobsTab from "../features/monitoring/JobsTab";
import RateLimitsTab from "../features/monitoring/RateLimitsTab";
import RumTab from "../features/monitoring/RumTab";

export default function Monitoring() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 flex flex-col">
      <header className="sticky top-0 z-20 bg-white border-b px-6 py-3">
        <h1 className="font-bold text-xl">Monitoring</h1>
      </header>
      <main className="flex-1">
        <TabRouter
          plugins={[
            { name: "Telemetry", render: () => <RumTab /> },
            { name: "Rate limits", render: () => <RateLimitsTab /> },
            { name: "Cache", render: () => <CacheTab /> },
            { name: "Audit log", render: () => <AuditLogTab /> },
            { name: "Jobs", render: () => <JobsTab /> },
          ]}
        />
      </main>
    </div>
  );
}

