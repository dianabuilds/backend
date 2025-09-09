import React from 'react';

type Entry = [string, string];

interface Props {
  entries: Entry[];
  onChange: (key: string, value: string) => void;
  onSave: (key: string) => void;
  saving?: Record<string, boolean>;
  renderLabel?: (key: string) => React.ReactNode;
}

export default function RateLimitRulesEditor({ entries, onChange, onSave, saving, renderLabel }: Props) {
  return (
    <section className="space-y-2">
      {entries.map(([key, value]) => (
        <div key={key} className="flex items-center gap-2">
          <label className="w-40 text-sm text-gray-600">
            {renderLabel ? renderLabel(key) : key}
          </label>
          <input
            className="border rounded px-2 py-1 w-40"
            value={value}
            onChange={(e) => onChange(key, e.target.value)}
            placeholder="5/min, 10/sec"
          />
          <button
            className="px-3 py-1 rounded border"
            onClick={() => onSave(key)}
            disabled={Boolean(saving?.[key])}
          >
            {saving?.[key] ? 'Saving...' : 'Save'}
          </button>
        </div>
      ))}
    </section>
  );
}

