import type { ReactNode } from "react";

interface Props {
  title: string;
  value: ReactNode;
  className?: string;
}

export default function KpiCard({ title, value, className }: Props) {
  return (
    <div
      className={`rounded bg-white p-4 shadow-sm dark:bg-gray-800 ${
        className ?? ""
      }`}
    >
      <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
      <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
    </div>
  );
}
