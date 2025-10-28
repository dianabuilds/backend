import type { Meta, StoryObj } from '@storybook/react';

import { ProvidersTab } from './ProvidersTab';

const meta: Meta<typeof ProvidersTab> = {
  title: 'Management/Billing/ProvidersTab',
  component: ProvidersTab,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;

type Story = StoryObj<typeof ProvidersTab>;

const providersSample = [
  {
    slug: 'stripe',
    type: 'stripe',
    enabled: true,
    priority: 10,
    contract_slug: 'main-vault',
    networks: ['polygon', 'ethereum'],
    supported_tokens: ['USDC', 'DAI'],
    default_network: 'polygon',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-05T00:00:00Z',
    config: { webhook_secret: '***' },
  },
  {
    slug: 'moonpay',
    type: 'moonpay',
    enabled: false,
    priority: 50,
    contract_slug: 'test-faucet',
    networks: ['base'],
    supported_tokens: ['USDC'],
    default_network: 'base',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-06T00:00:00Z',
    config: {},
  },
] as any;

const contractsSample = [
  {
    id: 'ctr-1',
    slug: 'main-vault',
    title: 'Main vault',
    chain: 'polygon',
    address: '0x123',
    type: 'ERC-20',
    enabled: true,
    testnet: false,
    methods: { list: ['deposit', 'refund'], roles: ['ops'] },
    status: 'active',
    abi_present: true,
    webhook_url: 'https://hooks.example.com/billing',
  },
] as any;

const kpiSample = {
  success: 126,
  errors: 5,
  pending: 8,
  volume_cents: 325000,
  avg_confirm_ms: 140,
  contracts: { total: 5, enabled: 4, disabled: 1, testnet: 1, mainnet: 4 },
};

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const Default: Story = {
  args: {
    loading: false,
    kpi: kpiSample as any,
    providers: providersSample,
    contracts: contractsSample,
    onSave: async () => {
      await wait(400);
    },
    onDelete: async () => {
      await wait(300);
    },
  },
};

