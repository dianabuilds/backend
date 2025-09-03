import AuditLogTab from "../features/monitoring/AuditLogTab";

export default function AuditLog() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Audit log</h1>
      <AuditLogTab />
    </div>
  );
}
