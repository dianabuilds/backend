import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import { PlanEditorDrawer } from '../PlanEditorDrawer';
import { DEFAULT_PLAN_FORM } from '../helpers';

const onSave = vi.fn();
const onClose = vi.fn();
const onLoadHistory = vi.fn();
const onChangeSpy = vi.fn();

vi.mock('@ui', () => {
  const Button = ({ children, ...props }: any) => (
    <button type="button" {...props}>
      {children}
    </button>
  );

  const Tabs = ({ items, value, onChange }: any) => (
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
  );

  return {
    Badge: ({ children }: any) => <span>{children}</span>,
    Button,
    Card: ({ children }: any) => <div>{children}</div>,
    Drawer: ({ open, title, children, footer }: any) =>
      open ? (
        <div>
          <div role="heading" aria-level={2}>
            {title}
          </div>
          <div>{children}</div>
          <div>{footer}</div>
        </div>
      ) : null,
    Input: ({ label, value, onChange, ...props }: any) => (
      <label>
        {label}
        <input aria-label={label} value={value} onChange={onChange} {...props} />
      </label>
    ),
    Select: ({ label, value, onChange, children }: any) => (
      <label>
        {label}
        <select aria-label={label} value={value} onChange={onChange}>
          {children}
        </select>
      </label>
    ),
    Spinner: () => <div data-testid="spinner">loading</div>,
    Tabs,
    Textarea: ({ label, value, onChange }: any) => (
      <label>
        {label}
        <textarea aria-label={label} value={value} onChange={onChange} />
      </label>
    ),
  };
});

describe('PlanEditorDrawer', () => {
  beforeEach(() => {
    onSave.mockReset();
    onClose.mockReset();
    onLoadHistory.mockReset();
    onChangeSpy.mockReset();
  });

  const renderDrawer = (overrides?: {
    form?: Partial<typeof DEFAULT_PLAN_FORM>;
    error?: string | null;
    history?: any[];
    historyLoading?: boolean;
  }) => {
    const Wrapper: React.FC = () => {
      const [form, setForm] = React.useState({
        ...DEFAULT_PLAN_FORM,
        slug: 'starter',
        title: 'Starter',
        description: 'Base plan',
        price_cents: '999',
        price_token: 'USDC',
        monthly_limits: {
          ...DEFAULT_PLAN_FORM.monthly_limits,
          api_quota: '1000',
        },
        features: {
          ...DEFAULT_PLAN_FORM.features,
          status: 'active',
          audience: 'all',
        },
        ...(overrides?.form ?? {}),
      });

      const handleChange = (updater: (state: typeof form) => typeof form) => {
        onChangeSpy(updater);
        setForm((prev) => updater(prev));
      };

      return (
        <PlanEditorDrawer
          open
          saving={false}
          form={form}
          error={overrides?.error ?? null}
          history={overrides?.history ?? []}
          historyLoading={overrides?.historyLoading ?? false}
          onClose={onClose}
          onChange={handleChange}
          onSave={onSave}
          onLoadHistory={onLoadHistory}
        />
      );
    };

    return render(<Wrapper />);
  };

  it('allows editing general fields', () => {
    renderDrawer();

    const slugInput = screen.getByLabelText('Slug*') as HTMLInputElement;
    expect(slugInput.value).toBe('starter');

    fireEvent.change(slugInput, { target: { value: 'pro' } });
    expect(slugInput.value).toBe('pro');
    expect(onChangeSpy).toHaveBeenCalled();
  });

  it('loads history when switching to history tab', async () => {
    renderDrawer();

    fireEvent.click(screen.getByRole('button', { name: 'История' }));
    await waitFor(() => expect(onLoadHistory).toHaveBeenCalled());
  });

  it('renders history entries when provided', async () => {
    renderDrawer({
      history: [
        { id: 'h1', action: 'update', actor: 'admin', created_at: '2024-01-01', payload: {} },
      ],
    });

    fireEvent.click(screen.getByRole('button', { name: 'История' }));
    expect(await screen.findByText('admin')).toBeInTheDocument();
  });

  it('shows backend error and triggers save', () => {
    renderDrawer({ error: 'backend failed' });

    expect(screen.getByText('backend failed')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }));
    expect(onSave).toHaveBeenCalled();
  });
});
