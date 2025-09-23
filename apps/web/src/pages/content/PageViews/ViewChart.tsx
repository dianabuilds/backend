import type { ApexOptions } from 'apexcharts';
import { BarChart } from '@ui';

const series = [
  { name: 'Прошлый период', data: [14, 25, 20, 25, 12, 20, 15, 20, 14, 25, 20, 25] },
  { name: 'Текущий период', data: [28, 45, 35, 50, 32, 55, 23, 60, 28, 45, 35, 50] },
];

const options: ApexOptions = {
  colors: ['#FF9800', '#4C4EE7'],
  chart: { parentHeightOffset: 0, toolbar: { show: false } },
  stroke: { show: true, width: 3, colors: ['transparent'] },
  dataLabels: { enabled: false },
  plotOptions: { bar: { borderRadius: 4, barHeight: '90%', columnWidth: '35%' } },
  legend: { show: false },
  xaxis: {
    categories: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
    axisBorder: { show: false },
    axisTicks: { show: false },
    labels: { hideOverlappingLabels: false },
    tooltip: { enabled: false },
  },
  grid: { padding: { left: 0, right: 0, top: 0, bottom: -10 } },
  yaxis: { show: false, axisBorder: { show: false }, axisTicks: { show: false }, labels: { show: false } },
  responsive: [{ breakpoint: 1024, options: { plotOptions: { bar: { columnWidth: '55%' } } } }],
};

export function ViewChart() {
  return (
    <div className="ax-transparent-gridline col-span-12 px-2 sm:col-span-6 lg:col-span-8">
      <BarChart options={options} series={series} height={280} />
    </div>
  );
}

