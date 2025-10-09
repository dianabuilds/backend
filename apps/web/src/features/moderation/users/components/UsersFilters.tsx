import * as React from 'react';

import { Button, Input, Select, Surface } from '@ui';
import { FunnelIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

import { RISK_FILTERS, ROLE_FILTERS, STATUS_FILTERS } from '../constants';
import type { FilterState, RiskFilterValue, RoleFilterValue, StatusFilterValue } from '../types';

type UsersFiltersProps = {
  filters: FilterState;
  search: string;
  advancedOpen: boolean;
  advancedActiveCount: number;
  onFilterChange: (patch: Partial<FilterState>) => void;
  onSearchChange: (value: string) => void;
  onToggleAdvanced: () => void;
  onReset: () => void;
};

export function UsersFilters({
  filters,
  search,
  advancedOpen,
  advancedActiveCount,
  onFilterChange,
  onSearchChange,
  onToggleAdvanced,
  onReset,
}: UsersFiltersProps): JSX.Element {
  return (
    <Surface
      variant="soft"
      className="space-y-4 px-5 py-5"
      data-testid="moderation-users-filters"
      data-analytics="moderation:users:filters"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="grid flex-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <Select
            label="Status"
            value={filters.status}
            onChange={(event) => onFilterChange({ status: event.target.value as StatusFilterValue })}
            data-testid="moderation-users-filter-status"
            data-analytics="moderation:users:filter:status"
          >
            {STATUS_FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Select
            label="Role"
            value={filters.role}
            onChange={(event) => onFilterChange({ role: event.target.value as RoleFilterValue })}
            data-testid="moderation-users-filter-role"
            data-analytics="moderation:users:filter:role"
          >
            {ROLE_FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Input
            label="Search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Email, username, or ID"
            prefix={<MagnifyingGlassIcon className="size-4" aria-hidden="true" />}
            data-testid="moderation-users-filter-search"
            data-analytics="moderation:users:filter:search"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={onToggleAdvanced}
            data-testid="moderation-users-toggle-advanced"
          >
            <FunnelIcon className="size-4" aria-hidden="true" />
            Advanced filters
            {advancedActiveCount > 0 ? (
              <span className="ml-2 rounded-full bg-primary-600/10 px-2 text-xs font-semibold text-primary-600">
                {advancedActiveCount}
              </span>
            ) : null}
          </Button>
          <Button size="sm" variant="ghost" onClick={onReset} data-testid="moderation-users-filter-reset">
            Reset
          </Button>
        </div>
      </div>

      {advancedOpen ? (
        <div
          className="grid gap-4 border-t border-white/30 pt-4 sm:grid-cols-2 lg:grid-cols-3"
          data-testid="moderation-users-advanced"
          data-analytics="moderation:users:filter:advanced"
        >
          <Select
            label="Risk level"
            value={filters.risk}
            onChange={(event) => onFilterChange({ risk: event.target.value as RiskFilterValue })}
            data-testid="moderation-users-filter-risk"
          >
            {RISK_FILTERS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Input
            label="Registered from"
            type="date"
            value={filters.registrationFrom}
            onChange={(event) => onFilterChange({ registrationFrom: event.target.value })}
            data-testid="moderation-users-filter-registered-from"
          />
          <Input
            label="Registered to"
            type="date"
            value={filters.registrationTo}
            onChange={(event) => onFilterChange({ registrationTo: event.target.value })}
            data-testid="moderation-users-filter-registered-to"
          />
        </div>
      ) : null}
    </Surface>
  );
}
