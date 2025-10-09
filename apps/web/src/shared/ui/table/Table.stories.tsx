import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { Table } from './index';

const meta: Meta<typeof Table> = {
  title: 'Shared/Table',
  component: Table,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof Table>;

const sampleRows = [
  { id: 'AR-1024', owner: 'Nodes cluster', updated: '2025-10-04T08:32:00' },
  { id: 'AR-1042', owner: 'Content pipeline', updated: '2025-10-05T11:12:00' },
  { id: 'AR-1067', owner: 'Moderation service', updated: '2025-10-06T18:48:00' },
];

export const BasePreset: Story = {
  render: () => (
    <div className="max-w-4xl rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <Table preset="base" actions={<button className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-500">Add record</button>} headerSticky>
        <Table.Actions />
        <Table.THead>
          <Table.TR>
            <Table.TH className="w-32">ID</Table.TH>
            <Table.TH>Owner</Table.TH>
            <Table.TH className="w-48">Updated</Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          {sampleRows.map((row) => (
            <Table.TR key={row.id}>
              <Table.TD>{row.id}</Table.TD>
              <Table.TD>{row.owner}</Table.TD>
              <Table.TD>{new Date(row.updated).toLocaleString('ru-RU')}</Table.TD>
            </Table.TR>
          ))}
        </Table.TBody>
      </Table>
      <div className="border-t border-gray-200 pt-4">
        <Table.Pagination
          page={1}
          pageSize={10}
          currentCount={3}
          totalItems={48}
          onPageChange={() => {}}
          onPageSizeChange={() => {}}
        />
      </div>
    </div>
  ),
};

export const SurfacePreset: Story = {
  render: () => (
    <div className="max-w-4xl rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <Table preset="surface" hover zebra>
        <Table.THead>
          <Table.TR>
            <Table.TH>Team</Table.TH>
            <Table.TH>Status</Table.TH>
            <Table.TH>Last sync</Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          <Table.TR>
            <Table.TD>Live operations</Table.TD>
            <Table.TD>
              <span className="inline-flex items-center gap-2 text-sm font-medium text-green-600">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                Healthy
              </span>
            </Table.TD>
            <Table.TD>2025-10-07 09:25</Table.TD>
          </Table.TR>
          <Table.TR>
            <Table.TD>Creator workflows</Table.TD>
            <Table.TD>
              <span className="inline-flex items-center gap-2 text-sm font-medium text-amber-600">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                Degraded
              </span>
            </Table.TD>
            <Table.TD>2025-10-07 08:17</Table.TD>
          </Table.TR>
        </Table.TBody>
      </Table>
    </div>
  ),
};

export const EmptyState: Story = {
  render: () => (
    <div className="max-w-4xl rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <Table preset="management">
        <Table.THead>
          <Table.TR>
            <Table.TH>Name</Table.TH>
            <Table.TH>Owner</Table.TH>
            <Table.TH>Updated</Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          <Table.Empty
            colSpan={3}
            title="No reports for this period"
            description="Adjust filters or create a new scheduled report to populate this view."
            action={
              <button className="rounded-md border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-800">
                Clear filters
              </button>
            }
          />
        </Table.TBody>
      </Table>
    </div>
  ),
};

export const ErrorState: Story = {
  render: () => (
    <div className="max-w-4xl rounded-2xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      <Table preset="base">
        <Table.THead>
          <Table.TR>
            <Table.TH>Destination</Table.TH>
            <Table.TH>Type</Table.TH>
            <Table.TH>Last sync</Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          <Table.Error
            colSpan={3}
            title="Failed to load integrations"
            description="We could not reach the integrations service. Please retry or check the platform status."
            onRetry={() => console.log('retry integrations')}
          />
        </Table.TBody>
      </Table>
    </div>
  ),
};export const AnalyticsPreset: Story = {
  render: () => (
    <div className="max-w-4xl rounded-3xl bg-slate-900/95 p-6 text-slate-100 shadow-xl">
      <Table preset="analytics" zebra hover>
        <Table.THead>
          <Table.TR>
            <Table.TH>Метрика</Table.TH>
            <Table.TH>Значение</Table.TH>
            <Table.TH>Изменение</Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          <Table.TR>
            <Table.TD>Время отклика API</Table.TD>
            <Table.TD>142&nbsp;мс</Table.TD>
            <Table.TD className="text-emerald-300">-8%</Table.TD>
          </Table.TR>
          <Table.TR>
            <Table.TD>Ошибки 5xx</Table.TD>
            <Table.TD>0.3%</Table.TD>
            <Table.TD className="text-amber-200">+0.1 п.п.</Table.TD>
          </Table.TR>
          <Table.TR>
            <Table.TD>Генерации LLM</Table.TD>
            <Table.TD>12&nbsp;480</Table.TD>
            <Table.TD className="text-emerald-300">+6%</Table.TD>
          </Table.TR>
        </Table.TBody>
      </Table>
    </div>
  ),
};
