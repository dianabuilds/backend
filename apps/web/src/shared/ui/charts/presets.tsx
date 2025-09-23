import React from 'react';
import type { ApexOptions } from 'apexcharts';
import { ApexChart } from './ApexChart';

type PresetProps = {
  series: any;
  height?: number | string;
  width?: number | string;
  options?: ApexOptions;
};

const base: ApexOptions = {
  chart: { toolbar: { show: false }, parentHeightOffset: 0 },
  legend: { show: false },
  dataLabels: { enabled: false },
  grid: { padding: { left: 0, right: 0, top: 0, bottom: 0 } },
};

export function BarChart({ series, height = 280, width = '100%', options }: PresetProps) {
  const opts: ApexOptions = {
    ...base,
    plotOptions: { bar: { borderRadius: 4, columnWidth: '35%' } },
    stroke: { show: true, width: 3, colors: ['transparent'] },
    ...options,
  };
  return <ApexChart type="bar" series={series} height={height} width={width} options={opts} />;
}

export function LineChart({ series, height = 280, width = '100%', options }: PresetProps) {
  const opts: ApexOptions = {
    ...base,
    stroke: { width: 3, curve: 'smooth' },
    markers: { size: 2 },
    ...options,
  };
  return <ApexChart type="line" series={series} height={height} width={width} options={opts} />;
}

export function PieChart({ series, height = 280, width = '100%', options }: PresetProps) {
  const opts: ApexOptions = {
    ...base,
    legend: { show: true },
    labels: (options as any)?.labels || [],
    ...options,
  };
  return <ApexChart type="pie" series={series} height={height} width={width} options={opts} />;
}

