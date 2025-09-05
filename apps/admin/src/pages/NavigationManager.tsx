import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import * as Tabs from "@radix-ui/react-tabs";

import { api, ApiError } from "../api/client";
import { createTransition, updateTransition } from "../api/transitions";
import LimitBadge, { handleLimit429, refreshLimits } from "../components/LimitBadge";
import Tooltip from "../components/Tooltip";
import Simulation from "./Simulation";

interface RunResponse {
  transitions?: unknown[];
}

export default function NavigationManager() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [tab, setTab] = useState(searchParams.get("tab") || "manual");

  // Manual transitions state
  const [from, setFrom] = useState(() => searchParams.get("from_slug") || "");
  const [to, setTo] = useState(() => searchParams.get("to_slug") || "");
  const [label, setLabel] = useState("");
  const [weight, setWeight] = useState("");
  const [enableId, setEnableId] = useState("");
  const [disableId, setDisableId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Autogeneration state
  const [nodeSlug, setNodeSlug] = useState("");
  const [userId, setUserId] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState("");

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTransition({
        from_slug: from.trim(),
        to_slug: to.trim(),
        label: label.trim() || undefined,
        weight: weight.trim() ? Number(weight.trim()) : undefined,
        priority: weight.trim() ? Number(weight.trim()) : undefined,
        disabled: false,
      });
      setMessage("Transition created");
      setFrom("");
      setTo("");
      setLabel("");
      setWeight("");
    } catch (e: any) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleEnable = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateTransition(enableId.trim(), { disabled: false });
      setMessage("Transition enabled");
      setEnableId("");
    } catch (e: any) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleDisable = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateTransition(disableId.trim(), { disabled: true });
      setMessage("Transition disabled");
      setDisableId("");
    } catch (e: any) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const run = async () => {
    setRunning(true);
    setResult("");
    try {
      const payload: Record<string, unknown> = { node_slug: nodeSlug.trim() };
      if (userId.trim()) payload.user_id = userId.trim();
      const res = await api.post<RunResponse>("/admin/navigation/run", payload);
      const count = Array.isArray(res.data?.transitions)
        ? (res.data?.transitions as unknown[]).length
        : 0;
      setResult(`Generated transitions: ${count}`);
      await refreshLimits();
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 429) {
        const retry = Number(e.headers?.get("Retry-After") || 0);
        await handleLimit429("compass_calls", retry);
        setResult("Rate limit exceeded");
      } else {
        setResult(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setRunning(false);
    }
  };

  const changeTab = (value: string) => {
    setTab(value);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("tab", value);
      return next;
    });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Navigation manager</h1>
      <Tabs.Root value={tab} onValueChange={changeTab}>
        <Tabs.List className="flex border-b mb-4 gap-4">
          <Tabs.Trigger
            value="manual"
            className="px-3 py-2 text-sm data-[state=active]:border-b-2 data-[state=active]:border-blue-500"
          >
            Manual transitions
          </Tabs.Trigger>
          <Tabs.Trigger
            value="auto"
            className="px-3 py-2 text-sm data-[state=active]:border-b-2 data-[state=active]:border-blue-500"
          >
            Autogeneration
          </Tabs.Trigger>
          <Tabs.Trigger
            value="sim"
            className="px-3 py-2 text-sm data-[state=active]:border-b-2 data-[state=active]:border-blue-500"
          >
            Simulation
          </Tabs.Trigger>
        </Tabs.List>

        <Tabs.Content value="manual" className="space-y-6">
          {error && <div className="text-red-600">{error}</div>}
          {message && <div className="text-green-600">{message}</div>}

          <section className="space-y-2">
            <h2 className="font-semibold">Add transition</h2>
            <form
              onSubmit={handleAdd}
              className="flex flex-wrap items-center gap-2"
            >
              <input
                value={from}
                onChange={(e) => setFrom(e.target.value)}
                placeholder="from slug"
                className="border rounded px-2 py-1"
              />
              <input
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="to slug"
                className="border rounded px-2 py-1"
              />
              <input
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                placeholder="label (optional)"
                className="border rounded px-2 py-1 w-48"
              />
              <input
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                placeholder="weight"
                className="border rounded px-2 py-1 w-24"
              />
              <button type="submit" className="px-3 py-1 rounded border">
                Add
              </button>
            </form>
          </section>

          <section className="space-y-2">
            <h2 className="font-semibold">Enable transition</h2>
            <form onSubmit={handleEnable} className="flex items-center gap-2">
              <input
                value={enableId}
                onChange={(e) => setEnableId(e.target.value)}
                placeholder="transition id"
                className="border rounded px-2 py-1"
              />
              <button type="submit" className="px-3 py-1 rounded border">
                Enable
              </button>
            </form>
          </section>

          <section className="space-y-2">
            <h2 className="font-semibold">Disable transition</h2>
            <form onSubmit={handleDisable} className="flex items-center gap-2">
              <input
                value={disableId}
                onChange={(e) => setDisableId(e.target.value)}
                placeholder="transition id"
                className="border rounded px-2 py-1"
              />
              <button type="submit" className="px-3 py-1 rounded border">
                Disable
              </button>
            </form>
          </section>
        </Tabs.Content>

        <Tabs.Content value="auto" className="space-y-4">
          <div className="flex flex-col gap-2 max-w-xl">
            <label className="flex flex-col gap-1">
              <span className="text-sm text-gray-600">
                Node slug <Tooltip text="Slug of the starting node" />
              </span>
              <input
                value={nodeSlug}
                onChange={(e) => setNodeSlug(e.target.value)}
                className="border rounded px-2 py-1"
                placeholder="node-slug"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-sm text-gray-600">
                User ID (optional) <Tooltip text="UUID of user; leave empty for anonymous" />
              </span>
              <input
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                className="border rounded px-2 py-1"
                placeholder="uuid or empty for anon"
              />
            </label>
            <div className="flex items-center gap-2">
              <button
                disabled={!nodeSlug || running}
                onClick={run}
                className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
              >
                {running ? "Running..." : "Run generation"}
              </button>
              <LimitBadge limitKey="compass_calls" />
            </div>
            {result && <div className="text-sm mt-2">{result}</div>}
          </div>
        </Tabs.Content>

        <Tabs.Content value="sim">
          <Simulation />
        </Tabs.Content>
      </Tabs.Root>
    </div>
  );
}

