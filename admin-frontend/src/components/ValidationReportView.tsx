type Item = { level: "error" | "warning"; code: string; message: string; node?: string | null };

type Props = {
  report: { errors: number; warnings: number; items: Item[] } | null | undefined;
};

export default function ValidationReportView({ report }: Props) {
  if (!report) return null;
  return (
    <div className="mt-2 border rounded p-3">
      <div className="text-sm mb-2">
        Ошибки: <b>{report.errors}</b>, предупреждения: <b>{report.warnings}</b>
      </div>
      <ul className="space-y-1">
        {(report.items || []).map((it, idx) => (
          <li key={idx} className={it.level === "error" ? "text-red-700" : "text-yellow-700"}>
            <span className="inline-block min-w-[80px] px-2 py-0.5 rounded text-xs mr-2 bg-gray-100">{it.level}</span>
            <span className="font-mono text-xs mr-2">{it.code}</span>
            <span>{it.message}</span>
            {it.node ? <span className="ml-2 text-gray-500">node: {it.node}</span> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
