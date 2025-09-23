import React from 'react';
import ReactApexChart from 'react-apexcharts';
import type { ApexOptions } from 'apexcharts';

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

export function ApexChart({ options, series, type, height = 280, width = '100%' }: ChartProps) {
  const merged = { ...baseOptions, ...(options || {}) } as ApexOptions;
  return <ReactApexChart options={merged} series={series as any} type={type as any} height={height} width={width} />;
}
