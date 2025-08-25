import React from "react";

interface EnvChipProps {
  mode?: string | null;
}

const ENV_INFO: Record<string, { label: string; className: string; title: string }> = {
  development: {
    label: "dev",
    className: "bg-gray-200 text-gray-800",
    title: "Development environment",
  },
  test: {
    label: "test",
    className: "bg-blue-200 text-blue-800",
    title: "Test environment",
  },
  staging: {
    label: "staging",
    className: "bg-yellow-200 text-yellow-800",
    title: "Staging environment",
  },
  production: {
    label: "prod",
    className: "bg-red-600 text-white",
    title: "Production environment",
  },
};

export default function EnvChip({ mode }: EnvChipProps) {
  if (!mode) return null;
  const info = ENV_INFO[mode] || {
    label: mode,
    className: "bg-gray-200 text-gray-800",
    title: mode,
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs ${info.className}`}
      title={info.title}
    >
      {info.label}
    </span>
  );
}

