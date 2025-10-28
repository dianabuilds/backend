import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

import { ProvidersTab } from '../tabs/ProvidersTab';

const mockProvider = {
  slug: 'stripe',
  type: 'stripe',
  enabled: true,
  priority: 10,
  config: { linked_contract: 'vault' },
  contract_slug: 'vault',
  networks: ['polygon'],
  supported_tokens: ['USDC'],
  default_network: 'polygon',
};

const mockContracts = [
  {
    id: 'ctr-1',
    slug: 'vault',
    title: 'Main Vault',
    chain: 'polygon',
    address: '0x123',
    type: 'ERC-20',
    enabled: true,
    testnet: false,
    methods: { list: [], roles: [] },
    status: 'active',
    abi_present: true,
    webhook_url: '',
  },
];

describe('ProvidersTab', () => {
  it('renders providers table with KPI cards', () => {
    render(
      <ProvidersTab
        loading={false}
        kpi={{
          success: 10,
          errors: 1,
          pending: 2,
          volume_cents: 123400,
          avg_confirm_ms: 90,
          contracts: { total: 1, enabled: 1, disabled: 0, testnet: 0, mainnet: 1 },
        }}
        providers={[mockProvider as any]}
        contracts={mockContracts as any}
        onSave={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText('Успешные')).toBeInTheDocument();
    expect(screen.getByText('Провайдеры')).toBeInTheDocument();
    expect(screen.getByText('stripe')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Новый провайдер' })).toBeEnabled();
  });

  it('opens drawer for editing', async () => {
    render(
      <ProvidersTab
        loading={false}
        kpi={{
          success: 0,
          errors: 0,
          pending: 0,
          volume_cents: 0,
          avg_confirm_ms: 0,
          contracts: { total: 0, enabled: 0, disabled: 0, testnet: 0, mainnet: 0 },
        }}
        providers={[mockProvider as any]}
        contracts={mockContracts as any}
        onSave={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText('Редактировать'));

    expect(await screen.findByLabelText('Slug*')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Slug*'), { target: { value: 'stripe-test' } });
    expect((screen.getByLabelText('Slug*') as HTMLInputElement).value).toBe('stripe-test');
  });
});
