import '@testing-library/jest-dom';

import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AccountBranchProvider } from '../account/AccountContext';
import { getOverrideState } from '../shared/hooks';
import ScopeControls from './ScopeControls';

const queryData: { data: unknown[] } = { data: [] };
vi.mock('@tanstack/react-query', () => ({
  useQuery: () => queryData,
}));

describe('ScopeControls', () => {
  beforeEach(() => {
    queryData.data = [
      { id: 'ws1', name: 'One' },
      { id: 'ws2', name: 'Two' },
    ];
  });

  it('toggles override store', () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountBranchProvider>
          <ScopeControls
            scopeMode="member"
            onScopeModeChange={() => {}}
            roles={[]}
            onRolesChange={() => {}}
          />
        </AccountBranchProvider>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId('override-toggle'));
    expect(getOverrideState().enabled).toBe(true);
    fireEvent.change(screen.getByTestId('override-reason'), { target: { value: 'test' } });
    expect(getOverrideState().reason).toBe('test');
    fireEvent.click(screen.getByTestId('override-toggle'));
    expect(getOverrideState().enabled).toBe(false);
  });
});
