import React from 'react';
import { ApexChart, Card, Table } from '@ui';
import type { UsageRow } from '../types';

type UsageSectionProps = {
  usageRows: UsageRow[];
};

export function UsageSection({ usageRows }: UsageSectionProps) {
  const hasUsageData = usageRows.length > 0;
  const chartCategories = usageRows.map((row) => row.key);
  const chartSeries = React.useMemo(
    () => [
      { name: 'calls', data: usageRows.map((row) => row.calls) },
      { name: 'errors', data: usageRows.map((row) => row.errors) },
    ],
    [usageRows],
  );

  return (
    <Card
      skin="none"
      className="rounded-2xl border border-white/50 bg-white/70 px-0 py-0 shadow-lg shadow-indigo-100/40 backdrop-blur-sm dark:border-slate-800 dark:bg-slate-900/70 dark:shadow-none"
    >
      <div className="space-y-6 p-6 lg:p-8">
        <div>
          <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">Нагрузка и ошибки</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Аналитика по вызовам LLM за последние 24 часа. Помогает увидеть проблемные провайдеры и оценить стоимость.
          </p>
        </div>

        {hasUsageData ? (
          <>
            <div className="overflow-hidden rounded-2xl border border-white/60 bg-white/60 shadow-inner dark:border-slate-800 dark:bg-slate-900/60">
              <ApexChart
                type="bar"
                height={280}
                series={chartSeries}
                options={{
                  chart: { stacked: false, toolbar: { show: false } },
                  xaxis: {
                    categories: chartCategories,
                    labels: { rotate: -40, style: { fontSize: '11px' } },
                  },
                  dataLabels: { enabled: false },
                  legend: { position: 'top' },
                  colors: ['#6366F1', '#F97316'],
                  grid: { strokeDashArray: 5 },
                }}
              />
            </div>

            <div className="overflow-hidden rounded-2xl border border-white/60 bg-white/60 shadow-inner dark:border-slate-800 dark:bg-slate-900/60">
              <Table.Table className="min-w-full text-sm">
                <Table.THead>
                  <Table.TR>
                    {['Провайдер', 'Модель', 'Вызовы', 'Ошибки', 'Токены', 'Latency', 'Стоимость, $'].map((label) => (
                      <Table.TH
                        key={label}
                        className="px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 first:pl-6 last:pr-6 dark:text-slate-400"
                      >
                        {label}
                      </Table.TH>
                    ))}
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {usageRows.slice(0, 12).map((row) => (
                    <Table.TR
                      key={row.key}
                      className="border-t border-white/60 bg-white/70 transition-colors hover:bg-primary-50/60 first:border-t-0 dark:border-slate-800 dark:bg-slate-900/60 dark:hover:bg-slate-800/60"
                    >
                      <Table.TD className="px-4 py-4 first:pl-6">{row.provider}</Table.TD>
                      <Table.TD className="px-4 py-4">{row.model}</Table.TD>
                      <Table.TD className="px-4 py-4">{row.calls}</Table.TD>
                      <Table.TD className={`px-4 py-4 ${row.errors ? 'font-medium text-rose-600 dark:text-rose-400' : ''}`}>
                        {row.errors}
                      </Table.TD>
                      <Table.TD className="px-4 py-4">{row.promptTokens + row.completionTokens}</Table.TD>
                      <Table.TD className="px-4 py-4">{row.latencyMs != null ? `${row.latencyMs} мс` : '—'}</Table.TD>
                      <Table.TD className="px-4 py-4 last:pr-6">${row.costUsd.toFixed(4)}</Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
            </div>
          </>
        ) : (
          <div className="rounded-2xl border border-dashed border-indigo-200/70 bg-white/50 p-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900/50">
            Метрики по вызовам пока не поступали. Как только появятся запросы к LLM, здесь появится статистика.
          </div>
        )}
      </div>
    </Card>
  );
}
