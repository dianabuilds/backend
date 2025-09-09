import { useMemo } from 'react';

export type ChartPoint = { ts: number; value: number };
export type ChartSeries = { points: ChartPoint[] };

export function StackedBars({
  series,
  height = 80,
  highlight = [],
  onSelect,
}: {
  series: ChartSeries[];
  height?: number;
  highlight?: boolean[];
  onSelect?: (ts: number) => void;
}) {
  const buckets =
    series[0]?.points.map((p, i) => {
      const sum = series.reduce((acc, s) => acc + (s.points[i]?.value || 0), 0);
      return { ts: p.ts, sum };
    }) || [];
  const max = Math.max(1, ...buckets.map((b) => b.sum));
  return (
    <div className="flex items-end gap-[2px]" style={{ height }}>
      {buckets.map((b, i) => {
        const totals = series.map((s) => s.points[i]?.value || 0);
        const heights = totals.map((v) => Math.round((v / max) * height));
        const colors = ['#10b981', '#f59e0b', '#ef4444'];
        const isHighlight = highlight[i];
        return (
          <div
            key={b.ts}
            data-testid={`bar-${i}`}
            onClick={() => onSelect?.(b.ts)}
            className={`w-[6px] flex flex-col justify-end cursor-pointer ${
              isHighlight ? 'outline outline-1 outline-red-500' : ''
            }`}
          >
            {heights.map((h, j) => (
              <div key={j} style={{ height: h, backgroundColor: colors[j] }} />
            ))}
          </div>
        );
      })}
    </div>
  );
}

export function LineChart({
  points,
  height = 80,
  highlight = [],
  onSelect,
}: {
  points: ChartPoint[];
  height?: number;
  highlight?: boolean[];
  onSelect?: (ts: number) => void;
}) {
  const max = Math.max(1, ...points.map((p) => p.value));
  const path = useMemo(() => {
    if (points.length === 0) return '';
    return points
      .map((p, i) => {
        const x = i * 8 + 4;
        const y = height - Math.round((p.value / max) * height);
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  }, [points, height, max]);
  const width = points.length * 8 + 4;
  return (
    <svg width={width} height={height}>
      <path d={path} fill="none" stroke="#3b82f6" strokeWidth="2" />
      {points.map((p, i) => {
        const x = i * 8 + 4;
        const y = height - Math.round((p.value / max) * height);
        return (
          <g
            key={i}
            data-testid={`point-${i}`}
            onClick={() => onSelect?.(p.ts)}
            className="cursor-pointer"
          >
            <circle cx={x} cy={y} r={3} fill="transparent" />
            {highlight[i] ? <circle cx={x} cy={y} r={3} fill="#ef4444" /> : null}
          </g>
        );
      })}
    </svg>
  );
}
