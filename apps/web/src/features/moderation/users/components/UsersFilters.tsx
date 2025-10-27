import * as React from 'react';

import { Button, Input, Select } from '@ui';
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

const riskAnyOption = RISK_FILTERS.find((option) => option.value === 'any');
const riskChipOptions = RISK_FILTERS.filter((option) => option.value !== 'any');

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
  const handleRiskClick = React.useCallback(
    (value: RiskFilterValue) => {
      const nextRisk: RiskFilterValue = filters.risk === value ? 'any' : value;
      onFilterChange({ risk: nextRisk });
    },
    [filters.risk, onFilterChange],
  );

  return (
    <div
      className="rounded-2xl border border-gray-200 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-900/94"
      data-testid="moderation-users-filters"
      data-analytics="moderation:users:filters"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="grid flex-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <Input
            label="Search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Email, username, or ID"
            prefix={<MagnifyingGlassIcon className="size-4" aria-hidden="true" />}
            data-testid="moderation-users-filter-search"
            data-analytics="moderation:users:filter:search"
          />
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
            Clear
          </Button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/80">
          Risk
        </span>
        {riskAnyOption ? (
          <Button
            size="xs"
            variant={filters.risk === 'any' ? 'filled' : 'ghost'}
            color={filters.risk === 'any' ? 'primary' : 'neutral'}
            onClick={() => handleRiskClick('any')}
          >
            {riskAnyOption.label}
          </Button>
        ) : null}
        {riskChipOptions.map((option) => (
          <Button
            key={option.value}
            size="xs"
            variant={filters.risk === option.value ? 'filled' : 'ghost'}
            color={filters.risk === option.value ? 'primary' : 'neutral'}
            onClick={() => handleRiskClick(option.value as RiskFilterValue)}
            data-analytics={`moderation:users:filter:risk:${option.value}`}
          >
            {option.label}
          </Button>
        ))}
      </div>

      {advancedOpen ? (
        <div
          className="mt-4 grid gap-4 border-t border-gray-100/80 pt-4 dark:border-dark-700/60 sm:grid-cols-2 lg:grid-cols-3"
          data-testid="moderation-users-advanced"
          data-analytics="moderation:users:filter:advanced"
        >
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
    </div>
  );
}
