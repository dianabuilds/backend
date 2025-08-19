import React, { useMemo } from "react";

export type Condition =
  | { type: "event_count"; event: string; count: number }
  | { type: "tag_interaction"; tag: string; count: number }
  | { type: "premium_status"; value: boolean }
  | { type: "first_action"; event: string }
  | { type: "quest_complete"; quest_id: string }
  | { type: "nodes_created"; count: number }
  | { type: "views_count"; count: number }
  | { type: string; [k: string]: any }; // fallback на будущее

export interface ConditionEditorProps {
  value?: any;
  onChange: (val: Condition) => void;
  className?: string;
  compact?: boolean;
}

const COMMON_EVENTS = ["quest_complete", "login", "tag_interaction", "node_create"];

// Нормализация входного значения к поддерживаемым полям
function asCondition(v?: any): Condition {
  const t = (v && v.type) || "event_count";
  switch (t) {
    case "event_count":
      return { type: "event_count", event: (v?.event ?? "some_event"), count: Number(v?.count ?? 1) };
    case "tag_interaction":
      return { type: "tag_interaction", tag: (v?.tag ?? ""), count: Number(v?.count ?? 1) };
    case "premium_status":
      return { type: "premium_status", value: Boolean(v?.value) };
    case "first_action":
      return { type: "first_action", event: (v?.event ?? "some_event") };
    case "quest_complete":
      return { type: "quest_complete", quest_id: (v?.quest_id ?? "") };
    case "nodes_created":
      return { type: "nodes_created", count: Number(v?.count ?? 1) };
    case "views_count":
      return { type: "views_count", count: Number(v?.count ?? 1) };
    default:
      return { type: String(t), ...(v || {}) };
  }
}

export default function ConditionEditor({ value, onChange, className }: ConditionEditorProps) {
  const cond = useMemo(() => asCondition(value), [value]);

  // UI-тип: если это event_count с событием premium_month — показываем как premium_duration
  const uiType = useMemo(() => {
    if (cond.type === "event_count" && (cond as any).event === "premium_month") return "premium_duration";
    return cond.type;
  }, [cond]);

  const setType = (type: string) => {
    // При смене типа подставляем разумные значения по умолчанию
    switch (type) {
      case "premium_duration":
        onChange({ type: "event_count", event: "premium_month", count: 1 });
        break;
      case "event_count":
        onChange({ type, event: "some_event", count: 1 });
        break;
      case "tag_interaction":
        onChange({ type, tag: "", count: 1 } as any);
        break;
      case "premium_status":
        onChange({ type, value: false } as any);
        break;
      case "first_action":
        onChange({ type, event: "some_event" } as any);
        break;
      case "quest_complete":
        onChange({ type, quest_id: "" } as any);
        break;
      case "nodes_created":
        onChange({ type, count: 1 } as any);
        break;
      case "views_count":
        onChange({ type, count: 100 } as any);
        break;
      default:
        onChange({ type } as any);
    }
  };

  return (
    <div className={className}>
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <label className="text-sm text-gray-600">Type</label>
        <select
          value={uiType}
          onChange={(e) => setType(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="event_count">event_count</option>
          <option value="premium_duration">premium_duration (months)</option>
          <option value="tag_interaction">tag_interaction</option>
          <option value="premium_status">premium_status</option>
          <option value="first_action">first_action</option>
          <option value="quest_complete">quest_complete</option>
          <option value="nodes_created">nodes_created</option>
          <option value="views_count">views_count</option>
        </select>
      </div>

      {uiType === "premium_duration" && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Months</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number((cond as any).count ?? 1)}
            onChange={(e) =>
              onChange({ type: "event_count", event: "premium_month", count: Math.max(1, Number(e.target.value) || 1) })
            }
          />
          <div className="flex items-center gap-1">
            {[1, 3, 6, 12, 24, 36].map((m) => (
              <button
                key={m}
                type="button"
                className="px-2 py-1 rounded border text-xs"
                onClick={() => onChange({ type: "event_count", event: "premium_month", count: m } as any)}
              >
                {m}m
              </button>
            ))}
          </div>
          <span className="text-xs text-gray-500">Maps to event_count(event="premium_month")</span>
        </div>
      )}

      {uiType === "event_count" && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Event</label>
          <select
            className="border rounded px-2 py-1"
            value={COMMON_EVENTS.includes((cond as any).event) ? (cond as any).event : "__custom__"}
            onChange={(e) => {
              const v = e.target.value;
              if (v === "__custom__") {
                onChange({ ...(cond as any), event: "" });
              } else {
                onChange({ ...(cond as any), event: v });
              }
            }}
          >
            {COMMON_EVENTS.map((ev) => (
              <option key={ev} value={ev}>{ev}</option>
            ))}
            <option value="__custom__">custom…</option>
          </select>
          {!COMMON_EVENTS.includes((cond as any).event) && (
            <input
              className="border rounded px-2 py-1"
              placeholder="custom event key"
              value={(cond as any).event || ""}
              onChange={(e) => onChange({ ...(cond as any), event: e.target.value })}
            />
          )}
          <label className="text-sm text-gray-600">Count</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number((cond as any).count ?? 1)}
            onChange={(e) => onChange({ ...(cond as any), count: Math.max(1, Number(e.target.value) || 1) })}
          />
        </div>
      )}

      {uiType === "tag_interaction" && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Tag</label>
          <input
            className="border rounded px-2 py-1"
            placeholder="tag slug"
            value={(cond as any).tag || ""}
            onChange={(e) => onChange({ ...(cond as any), tag: e.target.value })}
          />
          <label className="text-sm text-gray-600">Count</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number((cond as any).count ?? 1)}
            onChange={(e) => onChange({ ...(cond as any), count: Math.max(1, Number(e.target.value) || 1) })}
          />
        </div>
      )}

      {uiType === "premium_status" && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Premium required</label>
          <input
            type="checkbox"
            checked={Boolean((cond as any).value)}
            onChange={(e) => onChange({ ...(cond as any), value: e.target.checked })}
          />
        </div>
      )}

      {uiType === "first_action" && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Event</label>
          <select
            className="border rounded px-2 py-1"
            value={COMMON_EVENTS.includes((cond as any).event) ? (cond as any).event : "__custom__"}
            onChange={(e) => {
              const v = e.target.value;
              if (v === "__custom__") onChange({ ...(cond as any), event: "" });
              else onChange({ ...(cond as any), event: v });
            }}
          >
            {COMMON_EVENTS.map((ev) => (<option key={ev} value={ev}>{ev}</option>))}
            <option value="__custom__">custom…</option>
          </select>
          {!COMMON_EVENTS.includes((cond as any).event) && (
            <input
              className="border rounded px-2 py-1"
              placeholder="custom event key"
              value={(cond as any).event || ""}
              onChange={(e) => onChange({ ...(cond as any), event: e.target.value })}
            />
          )}
        </div>
      )}

      {uiType === "quest_complete" && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Quest ID</label>
          <input
            className="border rounded px-2 py-1 w-96 font-mono"
            placeholder="00000000-0000-0000-0000-000000000000"
            value={(cond as any).quest_id || ""}
            onChange={(e) => onChange({ ...(cond as any), quest_id: e.target.value })}
          />
        </div>
      )}

      {uiType === "nodes_created" && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Count</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number((cond as any).count ?? 1)}
            onChange={(e) => onChange({ ...(cond as any), count: Math.max(1, Number(e.target.value) || 1) })}
          />
        </div>
      )}

      {uiType === "views_count" && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Views</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number((cond as any).count ?? 100)}
            onChange={(e) => onChange({ ...(cond as any), count: Math.max(1, Number(e.target.value) || 1) })}
          />
        </div>
      )}
    </div>
  );
}
