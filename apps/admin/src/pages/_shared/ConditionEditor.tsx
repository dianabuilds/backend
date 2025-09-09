// @ts-nocheck
import { useMemo } from 'react';

export type Condition =
  | { type: 'event_count'; event: string; count: number }
  | { type: 'tag_interaction'; tag: string; count: number }
  | { type: 'premium_status'; value: boolean }
  | { type: 'first_action'; event: string }
  | { type: 'quest_complete'; quest_id: string }
  | { type: 'nodes_created'; count: number }
  | { type: 'views_count'; count: number }
  | { type: string; [k: string]: unknown }; // fallback на будущее

export interface ConditionEditorProps {
  value?: unknown;
  onChange: (val: Condition) => void;
  className?: string;
  compact?: boolean;
}

const COMMON_EVENTS = ['quest_complete', 'login', 'tag_interaction', 'node_create'];

// Нормализация входного значения к поддерживаемым полям
function asCondition(v?: unknown): Condition {
  const t = (v && typeof v === 'object' && (v as Record<string, unknown>).type) || 'event_count';
  switch (t) {
    case 'event_count':
      return {
        type: 'event_count',
        event: (v as { event?: string })?.event ?? 'some_event',
        count: Number((v as { count?: number })?.count ?? 1),
      };
    case 'tag_interaction':
      return {
        type: 'tag_interaction',
        tag: (v as { tag?: string })?.tag ?? '',
        count: Number((v as { count?: number })?.count ?? 1),
      };
    case 'premium_status':
      return { type: 'premium_status', value: Boolean((v as { value?: boolean })?.value) };
    case 'first_action':
      return { type: 'first_action', event: (v as { event?: string })?.event ?? 'some_event' };
    case 'quest_complete':
      return { type: 'quest_complete', quest_id: (v as { quest_id?: string })?.quest_id ?? '' };
    case 'nodes_created':
      return { type: 'nodes_created', count: Number((v as { count?: number })?.count ?? 1) };
    case 'views_count':
      return { type: 'views_count', count: Number((v as { count?: number })?.count ?? 1) };
    default:
      return { type: String(t), ...(v as object) };
  }
}

export default function ConditionEditor({ value, onChange, className }: ConditionEditorProps) {
  const cond = useMemo(() => asCondition(value), [value]);

  // UI-тип: если это event_count с событием premium_month — показываем как premium_duration
  const uiType = useMemo(() => {
    if (cond.type === 'event_count' && cond.event === 'premium_month') return 'premium_duration';
    return cond.type;
  }, [cond]);

  const setType = (type: string) => {
    // При смене типа подставляем разумные значения по умолчанию
    switch (type) {
      case 'premium_duration':
        onChange({ type: 'event_count', event: 'premium_month', count: 1 });
        break;
      case 'event_count':
        onChange({ type, event: 'some_event', count: 1 });
        break;
      case 'tag_interaction':
        onChange({ type: 'tag_interaction', tag: '', count: 1 });
        break;
      case 'premium_status':
        onChange({ type: 'premium_status', value: false });
        break;
      case 'first_action':
        onChange({ type: 'first_action', event: 'some_event' });
        break;
      case 'quest_complete':
        onChange({ type: 'quest_complete', quest_id: '' });
        break;
      case 'nodes_created':
        onChange({ type: 'nodes_created', count: 1 });
        break;
      case 'views_count':
        onChange({ type: 'views_count', count: 100 });
        break;
      default:
        onChange({ type });
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

      {uiType === 'premium_duration' && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Months</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number(cond.type === 'event_count' ? (cond.count ?? 1) : 1)}
            onChange={(e) =>
              onChange({
                type: 'event_count',
                event: 'premium_month',
                count: Math.max(1, Number(e.target.value) || 1),
              })
            }
          />
          <div className="flex items-center gap-1">
            {[1, 3, 6, 12, 24, 36].map((m) => (
              <button
                key={m}
                type="button"
                className="px-2 py-1 rounded border text-xs"
                onClick={() => onChange({ type: 'event_count', event: 'premium_month', count: m })}
              >
                {m}m
              </button>
            ))}
          </div>
          <span className="text-xs text-gray-500">Maps to event_count(event="premium_month")</span>
        </div>
      )}

      {uiType === 'event_count' && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Event</label>
          <select
            className="border rounded px-2 py-1"
            value={
              cond.type === 'event_count' && COMMON_EVENTS.includes(cond.event)
                ? cond.event
                : '__custom__'
            }
            onChange={(e) => {
              const v = e.target.value;
              if (v === '__custom__') {
                if (cond.type === 'event_count') onChange({ ...cond, event: '' });
              } else {
                if (cond.type === 'event_count') onChange({ ...cond, event: v });
              }
            }}
          >
            {COMMON_EVENTS.map((ev) => (
              <option key={ev} value={ev}>
                {ev}
              </option>
            ))}
            <option value="__custom__">custom…</option>
          </select>
          {cond.type === 'event_count' && !COMMON_EVENTS.includes(cond.event) && (
            <input
              className="border rounded px-2 py-1"
              placeholder="custom event key"
              value={cond.event || ''}
              onChange={(e) => onChange({ ...cond, event: e.target.value })}
            />
          )}
          <label className="text-sm text-gray-600">Count</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number(cond.type === 'event_count' ? (cond.count ?? 1) : 1)}
            onChange={(e) =>
              cond.type === 'event_count' &&
              onChange({ ...cond, count: Math.max(1, Number(e.target.value) || 1) })
            }
          />
        </div>
      )}

      {uiType === 'tag_interaction' && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Tag</label>
          <input
            className="border rounded px-2 py-1"
            placeholder="tag slug"
            value={cond.type === 'tag_interaction' ? cond.tag : ''}
            onChange={(e) =>
              cond.type === 'tag_interaction' && onChange({ ...cond, tag: e.target.value })
            }
          />
          <label className="text-sm text-gray-600">Count</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number(cond.type === 'tag_interaction' ? (cond.count ?? 1) : 1)}
            onChange={(e) =>
              cond.type === 'tag_interaction' &&
              onChange({ ...cond, count: Math.max(1, Number(e.target.value) || 1) })
            }
          />
        </div>
      )}

      {uiType === 'premium_status' && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Premium required</label>
          <input
            type="checkbox"
            checked={cond.type === 'premium_status' ? Boolean(cond.value) : false}
            onChange={(e) =>
              cond.type === 'premium_status' && onChange({ ...cond, value: e.target.checked })
            }
          />
        </div>
      )}

      {uiType === 'first_action' && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Event</label>
          <select
            className="border rounded px-2 py-1"
            value={
              cond.type === 'first_action' && COMMON_EVENTS.includes(cond.event)
                ? cond.event
                : '__custom__'
            }
            onChange={(e) => {
              const v = e.target.value;
              if (cond.type !== 'first_action') return;
              if (v === '__custom__') onChange({ ...cond, event: '' });
              else onChange({ ...cond, event: v });
            }}
          >
            {COMMON_EVENTS.map((ev) => (
              <option key={ev} value={ev}>
                {ev}
              </option>
            ))}
            <option value="__custom__">custom…</option>
          </select>
          {cond.type === 'first_action' && !COMMON_EVENTS.includes(cond.event) && (
            <input
              className="border rounded px-2 py-1"
              placeholder="custom event key"
              value={cond.event || ''}
              onChange={(e) => onChange({ ...cond, event: e.target.value })}
            />
          )}
        </div>
      )}

      {uiType === 'quest_complete' && (
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm text-gray-600">Quest ID</label>
          <input
            className="border rounded px-2 py-1 w-96 font-mono"
            placeholder="00000000-0000-0000-0000-000000000000"
            value={cond.type === 'quest_complete' ? cond.quest_id || '' : ''}
            onChange={(e) =>
              cond.type === 'quest_complete' && onChange({ ...cond, quest_id: e.target.value })
            }
          />
        </div>
      )}

      {uiType === 'nodes_created' && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Count</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number(cond.type === 'nodes_created' ? (cond.count ?? 1) : 1)}
            onChange={(e) =>
              cond.type === 'nodes_created' &&
              onChange({ ...cond, count: Math.max(1, Number(e.target.value) || 1) })
            }
          />
        </div>
      )}

      {uiType === 'views_count' && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Views</label>
          <input
            type="number"
            min={1}
            className="border rounded px-2 py-1 w-24"
            value={Number(cond.type === 'views_count' ? (cond.count ?? 100) : 100)}
            onChange={(e) =>
              cond.type === 'views_count' &&
              onChange({ ...cond, count: Math.max(1, Number(e.target.value) || 1) })
            }
          />
        </div>
      )}
    </div>
  );
}

