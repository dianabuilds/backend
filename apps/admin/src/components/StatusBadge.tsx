interface Props {
  status: string;
  reused?: boolean;
}

export default function StatusBadge({ status, reused }: Props) {
  const map: Record<string, string> = {
    draft: "bg-gray-200 text-gray-800",
    published: "bg-green-200 text-green-800",
    archived: "bg-red-200 text-red-800",
  };
  return (
    <span className="inline-flex items-center gap-2">
      <span className={`px-2 py-0.5 rounded text-xs ${map[status] || "bg-gray-200"}`}>{status}</span>
      {reused ? <span className="px-2 py-0.5 rounded text-xs bg-purple-200 text-purple-800">cache</span> : null}
    </span>
  );
}
