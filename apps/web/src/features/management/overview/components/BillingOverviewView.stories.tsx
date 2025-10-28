import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import { BillingOverviewView } from './BillingOverviewView';

const meta: Meta<typeof BillingOverviewView> = {
  title: 'Management/Billing/Overview',
  component: BillingOverviewView,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;

type Story = StoryObj<typeof BillingOverviewView>;

const overviewResponse = {
  kpi: {
    success: 32,
    errors: 4,
    pending: 6,
    volume_cents: 245000,
    avg_confirm_ms: 120,
    contracts: {
      total: 5,
      enabled: 4,
      disabled: 1,
      testnet: 1,
      mainnet: 4,
    },
  },
  subscriptions: {
    active_subs: 120,
    mrr: 480000,
    arpu: 4000,
    churn_30d: 0.06,
    tokens: [
      { token: 'USDC', total: 70, mrr_usd: 320000 },
      { token: 'DAI', total: 20, mrr_usd: 80000 },
    ],
    networks: [
      { network: 'polygon', chain_id: '137', total: 48 },
      { network: 'ethereum', chain_id: '1', total: 12 },
    ],
  },
  revenue: [
    { day: '2024-01-01', amount: 1200 },
    { day: '2024-01-02', amount: 1400 },
    { day: '2024-01-03', amount: 1600 },
  ],
};

const payoutsResponse = {
  items: [
    { id: 'p-1', status: 'failed', gross_cents: 12000, created_at: '2024-01-03T10:00:00Z' },
    { id: 'p-2', status: 'pending', gross_cents: 8000, created_at: '2024-01-02T12:00:00Z' },
  ],
};

const MockedOverview: React.FC = () => {
  React.useEffect(() => {
    const originalFetch = window.fetch;

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;

      if (url.endsWith('/v1/billing/overview/dashboard')) {
        return new Response(JSON.stringify(overviewResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      if (url.includes('/v1/billing/overview/payouts')) {
        return new Response(JSON.stringify(payoutsResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      return originalFetch
        ? originalFetch(input as any, init)
        : Promise.resolve(new Response('null', { status: 200 }));
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  return <BillingOverviewView />;
};

export const Default: Story = {
  render: () => <MockedOverview />,
};

