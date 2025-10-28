import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';

const mockNavigate = vi.fn();
const mockHook = vi.fn();

vi.mock('../../hooks/useBillingOverview', () => ({
  useBillingOverview: () => mockHook(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

const mockToast = { pushToast: vi.fn() };

vi.mock('@ui', () => {
  const TableComponent: any = ({ children }: { children: React.ReactNode }) => (
    <table data-testid="table">{children}</table>
  );

  TableComponent.Table = TableComponent;
  TableComponent.THead = ({ children }: { children: React.ReactNode }) => <thead>{children}</thead>;
  TableComponent.TBody = ({ children }: { children: React.ReactNode }) => <tbody>{children}</tbody>;
  TableComponent.TR = ({ children }: { children: React.ReactNode }) => <tr>{children}</tr>;
  TableComponent.TH = ({ children }: { children: React.ReactNode }) => <th>{children}</th>;
  TableComponent.TD = ({ children }: { children: React.ReactNode }) => <td>{children}</td>;

  return {
    Accordion: ({ title, children }: any) => (
      <div>
        <div>{title}</div>
        <div>{children}</div>
      </div>
    ),
    Badge: ({ children }: any) => <span>{children}</span>,
    Button: ({ children, icon, ...props }: any) => (
      <button type="button" {...props}>
        {icon ? <span data-testid="icon">{icon}</span> : null}
        {children}
      </button>
    ),
    Card: ({ children }: any) => <div data-testid="card">{children}</div>,
    Skeleton: ({ children, ...props }: any) => (
      <div data-testid="skeleton" {...props}>
        {children}
      </div>
    ),
    Table: TableComponent,
    Tabs: ({ items, value, onChange }: any) => (
      <div>
        {items.map((item: any) => (
          <button
            key={item.key}
            type="button"
            data-active={item.key === value}
            onClick={() => onChange(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>
    ),
    useToast: () => mockToast,
    ApexChart: () => <div data-testid="chart" />,
  };
});

vi.mock('@icons', () => ({
  ArrowUpRight: () => <svg data-testid="arrow-icon" />,
  Download: () => <svg data-testid="download-icon" />,
  Wallet: () => <svg data-testid="wallet-icon" />,
  AlertTriangle: () => <svg data-testid="alert-icon" />,
  Activity: () => <svg data-testid="activity-icon" />,
}));

const baseOverview = {
  kpi: {
    success: 10,
    errors: 2,
    pending: 3,
    volume_cents: 123400,
    avg_confirm_ms: 80,
    contracts: { total: 4, enabled: 3, disabled: 1, testnet: 1, mainnet: 3 },
  },
  subscriptions: {
    active_subs: 50,
    mrr: 12000,
    arpu: 240,
    churn_30d: 0.05,
    tokens: [{ token: 'usdc', total: 30, mrr_usd: 8000 }],
    networks: [{ network: 'polygon', chain_id: '137', total: 20 }],
  },
  revenue: [{ day: '2024-01-01', amount: 100 }],
};

const previousOverview = {
  ...baseOverview,
  kpi: {
    ...baseOverview.kpi,
    success: 8,
    errors: 4,
    pending: 5,
    volume_cents: 100000,
  },
};

beforeEach(() => {
  mockNavigate.mockReset();
  mockHook.mockReset();
  mockToast.pushToast.mockReset();
});

const { BillingOverviewView } = await import('../BillingOverviewView');

describe('BillingOverviewView', () => {
  it('renders KPI cards and navigates on details click', () => {
    const refresh = vi.fn();
    const clearError = vi.fn();

    const hookValue = {
      loading: false,
      error: null,
      overview: baseOverview,
      previousOverview,
      payouts: [],
      refresh,
      clearError,
    };

    mockHook.mockImplementation(() => hookValue);

    render(<BillingOverviewView />);

    expect(mockHook).toHaveBeenCalled();
    expect(screen.getByText('Billing Overview')).toBeInTheDocument();

    const detailButtons = screen.getAllByRole('button', { name: 'Подробнее' });
    expect(detailButtons).toHaveLength(4);

    fireEvent.click(detailButtons[0]);
    expect(mockNavigate).toHaveBeenCalledWith(
      '/finance/billing/payments?tab=transactions&status=success',
    );

    fireEvent.click(screen.getByRole('button', { name: 'Обновить данные' }));
    expect(refresh).toHaveBeenCalled();
  });

  it('shows error banner and allows clearing it', () => {
    const refresh = vi.fn();
    const clearError = vi.fn();

    const hookValue = {
      loading: false,
      error: 'api error',
      overview: baseOverview,
      previousOverview,
      payouts: [],
      refresh,
      clearError,
    };

    mockHook.mockImplementation(() => hookValue);

    render(<BillingOverviewView />);

    expect(screen.getByText('api error')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Скрыть' }));
    expect(clearError).toHaveBeenCalled();
  });

  it('renders loading skeletons when loading is true', () => {
    const refresh = vi.fn();
    const clearError = vi.fn();

    mockHook.mockImplementation(() => ({
      loading: true,
      error: null,
      overview: baseOverview,
      previousOverview: null,
      payouts: [],
      refresh,
      clearError,
    }));

    render(<BillingOverviewView />);

    expect(screen.getAllByTestId('skeleton').length).toBeGreaterThan(0);
  });
});
