// React import not required for JSX

export interface PeriodStepSelectorProps {
  range: '1h' | '24h';
  step: 60 | 300;
  onRangeChange: (r: '1h' | '24h') => void;
  onStepChange: (s: 60 | 300) => void;
  className?: string;
}

export default function PeriodStepSelector({
  range,
  step,
  onRangeChange,
  onStepChange,
  className,
}: PeriodStepSelectorProps) {
  return (
    <div className={className ? className : 'flex items-center gap-2'}>
      <label className="text-sm">Range:</label>
      <select
        value={range}
        onChange={(e) => onRangeChange(e.target.value as '1h' | '24h')}
        className="border rounded px-2 py-1 text-sm"
      >
        <option value="1h">1h</option>
        <option value="24h">24h</option>
      </select>
      <label className="text-sm">Step:</label>
      <select
        value={step}
        onChange={(e) => onStepChange(Number(e.target.value) as 60 | 300)}
        className="border rounded px-2 py-1 text-sm"
      >
        <option value={60}>1m</option>
        <option value={300}>5m</option>
      </select>
    </div>
  );
}
