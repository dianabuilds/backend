import React from 'react';
import type { ApexOptions } from 'apexcharts';

const LazyReactApexChart = React.lazy(() => import('react-apexcharts'));

export type ChartProps = {
  options?: ApexOptions;
  series: any;
  type: 'line' | 'area' | 'bar' | 'pie' | 'donut' | 'radar' | string;
  height?: number | string;
  width?: number | string;
};

const baseOptions: ApexOptions = {
  chart: { toolbar: { show: false }, parentHeightOffset: 0 },
  legend: { show: false },
  dataLabels: { enabled: false },
  grid: { strokeDashArray: 3 },
};

type ChartPlaceholderProps = {
  height: number | string;
  width: number | string;
};

function toCssSize(value: number | string): string {
  return typeof value === 'number' ? `${value}px` : value;
}

function ChartPlaceholder({ height, width }: ChartPlaceholderProps): React.ReactElement {
  const style: React.CSSProperties = {
    height: toCssSize(height),
    width: toCssSize(width),
  };

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex items-center justify-center rounded border border-dashed border-gray-200 text-xs text-gray-400 dark:border-dark-500 dark:text-dark-200"
      style={style}
    >
      Loading chart...
    </div>
  );
}

export function ApexChart({ options, series, type, height = 280, width = '100%' }: ChartProps) {
  const merged = { ...baseOptions, ...(options || {}) } as ApexOptions;

  if (typeof window === 'undefined') {
    return <ChartPlaceholder height={height} width={width} />;
  }

  return (
    <React.Suspense fallback={<ChartPlaceholder height={height} width={width} />}>
      <LazyReactApexChart
        options={merged}
        series={series as any}
        type={type as any}
        height={height}
        width={width}
      />
    </React.Suspense>
  );
}
