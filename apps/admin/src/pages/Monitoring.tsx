import { Card } from "../components/ui/card";
import AuditLogTab from "../features/monitoring/AuditLogTab";
import CacheTab from "../features/monitoring/CacheTab";
import JobsTab from "../features/monitoring/JobsTab";
import RateLimitsTab from "../features/monitoring/RateLimitsTab";
import RumTab from "../features/monitoring/RumTab";

export default function Monitoring() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="sticky top-0 z-20 bg-white border-b px-6 py-3">
        <h1 className="font-bold text-xl">Monitoring</h1>
      </header>
      <main className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card>
            <RumTab />
          </Card>
          <Card>
            <RateLimitsTab />
          </Card>
          <Card>
            <CacheTab />
          </Card>
          <Card>
            <AuditLogTab />
          </Card>
          <Card>
            <JobsTab />
          </Card>
        </div>
      </main>
    </div>
  );
}

