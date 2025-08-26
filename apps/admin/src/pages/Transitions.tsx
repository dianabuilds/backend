import { useState } from "react";
import { useSearchParams } from "react-router-dom";

import { createTransition, updateTransition } from "../api/transitions";

export default function Transitions() {
  const [searchParams] = useSearchParams();
  const [from, setFrom] = useState(() => searchParams.get("from_slug") || "");
  const [to, setTo] = useState(() => searchParams.get("to_slug") || "");
  const [label, setLabel] = useState("");
  const [weight, setWeight] = useState("");
  const [enableId, setEnableId] = useState("");
  const [disableId, setDisableId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Transitions</h1>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      {message && <div className="text-green-600 mb-2">{message}</div>}

      <section className="mb-6">
        <h2 className="font-semibold mb-2">Add transition</h2>
        <form onSubmit={handleAdd} className="flex flex-wrap items-center gap-2">
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

      <section className="mb-6">
        <h2 className="font-semibold mb-2">Enable transition</h2>
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

      <section>
        <h2 className="font-semibold mb-2">Disable transition</h2>
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
    </div>
  );
}

