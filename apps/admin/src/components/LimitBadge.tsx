import { useEffect, useState } from "react";

import { api } from "../api/client";

interface Props {
  limitKey: string;
}

// internal state shared across instances
let limits: Record<string, number> = {};
let messages: Record<string, string> = {};
const listeners = new Set<() => void>();

async function fetchLimits(clearMessages = true) {
  try {
    const res = await api.get<Record<string, number>>("/admin/ops/limits");
    limits = res.data || {};
    if (clearMessages) messages = {};
  } catch {
    // ignore
  }
  listeners.forEach((cb) => cb());
}

export async function refreshLimits() {
  await fetchLimits(true);
}

export async function handleLimit429(limitKey: string, retryAfter?: number) {
  const seconds = typeof retryAfter === "number" && retryAfter > 0 ? retryAfter : undefined;
  messages[limitKey] = seconds ? `try again in ${seconds}s` : "rate limited";
  listeners.forEach((cb) => cb());
  await fetchLimits(false);
}

export default function LimitBadge({ limitKey }: Props) {
  const [value, setValue] = useState<number | null>(limits[limitKey] ?? null);
  const [msg, setMsg] = useState<string | undefined>(messages[limitKey]);

  useEffect(() => {
    const listener = () => {
      setValue(limits[limitKey] ?? null);
      setMsg(messages[limitKey]);
    };
    listeners.add(listener);
    if (typeof limits[limitKey] === "undefined") {
      fetchLimits(true);
    }
    return () => listeners.delete(listener);
  }, [limitKey]);

  const title = msg || undefined;
  const cls = msg ? "bg-red-200 text-red-800" : "bg-gray-200 text-gray-800";

  return (
    <span
      className={`ml-2 px-2 py-0.5 rounded text-xs ${cls}`}
      title={title}
      data-testid={`limit-${limitKey}`}
    >
      {value ?? "-"}
    </span>
  );
}

