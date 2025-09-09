import type { ChangeEvent } from 'react';

export interface TraceFilterValues {
  from: string;
  to: string;
  userId: string;
  source: string;
  channel: string;
  dateFrom: string;
  dateTo: string;
  type?: string;
}

interface TraceFiltersProps {
  values: TraceFilterValues;
  onChange: (patch: Partial<TraceFilterValues>) => void;
  showType?: boolean;
  className?: string;
}

export function TraceFilters({ values, onChange, showType = false, className = '' }: TraceFiltersProps) {
  const handle = (key: keyof TraceFilterValues) => (e: ChangeEvent<HTMLInputElement>) => {
    onChange({ [key]: e.target.value });
  };

  return (
    <div className={`mb-3 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-2 ${className}`.trim()}>
      <input
        value={values.from}
        onChange={handle('from')}
        placeholder="Откуда (slug)"
        className="border rounded px-2 py-1"
      />
      <input
        value={values.to}
        onChange={handle('to')}
        placeholder="Куда (slug)"
        className="border rounded px-2 py-1"
      />
      <input
        value={values.userId}
        onChange={handle('userId')}
        placeholder="Пользователь ID"
        className="border rounded px-2 py-1"
      />
      <input
        value={values.source}
        onChange={handle('source')}
        placeholder="Источник"
        className="border rounded px-2 py-1"
      />
      <input
        value={values.channel}
        onChange={handle('channel')}
        placeholder="Канал"
        className="border rounded px-2 py-1"
      />
      {showType && (
        <input
          value={values.type || ''}
          onChange={handle('type')}
          placeholder="Тип"
          className="border rounded px-2 py-1"
        />
      )}
      <input
        value={values.dateFrom}
        onChange={handle('dateFrom')}
        type="datetime-local"
        placeholder="С даты"
        className="border rounded px-2 py-1"
      />
      <input
        value={values.dateTo}
        onChange={handle('dateTo')}
        type="datetime-local"
        placeholder="По дату"
        className="border rounded px-2 py-1"
      />
    </div>
  );
}

