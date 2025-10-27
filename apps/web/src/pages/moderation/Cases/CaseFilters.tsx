import React from 'react';
import { Button, Input, Select, Switch, Badge, Skeleton } from '@ui';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import {
  CASE_PRIORITY_OPTIONS,
  CASE_SEVERITY_OPTIONS,
  CASE_STATUS_OPTIONS,
  CASE_TYPE_OPTIONS,
} from './constants';
import type { CaseFiltersState } from './types';

type Stats = { total: number; open: number; unassigned: number };

const STORAGE_KEY = 'moderation:cases:saved-filters';

type SavedFilter = {
  id: string;
  label: string;
  payload: Partial<CaseFiltersState>;
};

const PRESETS: SavedFilter[] = [
  { id: 'preset-open', label: 'Open', payload: { statuses: ['open'] } },
  { id: 'preset-escalated', label: 'Escalated', payload: { statuses: ['escalated'] } },
  { id: 'preset-unassigned', label: 'Unassigned', payload: { assignee: '' } },
];

function filtersAreEmpty(filters: CaseFiltersState) {
  return (
    !filters.query &&
    !filters.assignee &&
    filters.statuses.length === 0 &&
    filters.types.length === 0 &&
    filters.severities.length === 0 &&
    filters.priorities.length === 0 &&
    filters.queues.length === 0 &&
    filters.tags.length === 0
  );
}

function readSavedFilters(): SavedFilter[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item) => item && typeof item.id === 'string' && item.payload).slice(0, 6);
  } catch {
    return [];
  }
}

function persistSavedFilters(filters: SavedFilter[]) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
  } catch {
    // ignore persistence errors
  }
}

function generateFilterLabel(filters: CaseFiltersState, fallbackIndex: number): string {
  const segments: string[] = [];
  if (filters.statuses.length) segments.push(filters.statuses.map((status) => toTitle(status)).join('/'));
  if (filters.types.length) segments.push(filters.types.map((type) => toTitle(type)).join('/'));
  if (filters.priorities.length) segments.push(`Priority ${filters.priorities.map(toTitle).join('/')}`);
  if (filters.severities.length) segments.push(`Severity ${filters.severities.map(toTitle).join('/')}`);
  if (filters.assignee) segments.push(`Assignee ${filters.assignee}`);
  if (!segments.length && filters.query) segments.push(`Search "${filters.query}"`);
  return segments.length ? segments.join(' / ') : `Preset ${fallbackIndex}`;
}

function toTitle(value: string): string {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ');
}

type Props = {
  filters: CaseFiltersState;
  onChange: (next: Partial<CaseFiltersState>) => void;
  onReset: () => void;
  stats?: Stats;
  loading?: boolean;
  autoRefresh: boolean;
  onAutoRefreshChange: (value: boolean) => void;
};

export function CaseFilters({
  filters,
  onChange,
  onReset,
  stats,
  loading,
  autoRefresh,
  onAutoRefreshChange,
}: Props) {
  const [savedFilters, setSavedFilters] = React.useState<SavedFilter[]>(() => readSavedFilters());
  const presets = React.useMemo(() => [...PRESETS, ...savedFilters], [savedFilters]);
  const filtersEmpty = filtersAreEmpty(filters);
  const canSaveFilter = !filtersEmpty;

  const handleQueryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ query: event.target.value });
  };

  const handleAssigneeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ assignee: event.target.value });
  };

  const handleSelect = (key: keyof CaseFiltersState) => (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    onChange({ [key]: value ? [value] : [] } as Partial<CaseFiltersState>);
  };

  const handlePresetApply = (preset: SavedFilter) => {
    onChange(preset.payload);
  };

  const handleSaveFilter = () => {
    if (!canSaveFilter) return;
    const next: SavedFilter = {
      id: `saved-${Date.now()}`,
      label: generateFilterLabel(filters, savedFilters.length + 1),
      payload: { ...filters },
    };
    const updated = [...savedFilters, next].slice(0, 6);
    setSavedFilters(updated);
    persistSavedFilters(updated);
  };

  const handleRemoveSaved = (id: string) => {
    const updated = savedFilters.filter((item) => item.id !== id);
    setSavedFilters(updated);
    persistSavedFilters(updated);
  };

  const handleMyCasesToggle = (checked: boolean) => {
    onChange({ assignee: checked ? 'me' : '' });
  };

  return (
    <div className="rounded-2xl border border-gray-200 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-900/94">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex min-w-[240px] flex-1 items-center gap-2">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input
              value={filters.query}
              onChange={handleQueryChange}
              placeholder="Search id / title / subject"
              className="pl-9"
            />
          </div>
          <Input
            className="w-48"
            placeholder="Assignee"
            value={filters.assignee}
            onChange={handleAssigneeChange}
          />
        </div>

        <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-dark-200/80">
          {loading ? <Skeleton aria-hidden className="h-3 w-16 rounded" /> : null}
          {stats ? (
            <div className="flex flex-wrap items-center gap-2">
              <Badge color="neutral" variant="soft" className="text-[11px]">
                Total: {stats.total}
              </Badge>
              <Badge color="warning" variant="soft" className="text-[11px]">
                Open: {stats.open}
              </Badge>
              <Badge color="info" variant="soft" className="text-[11px]">
                Unassigned: {stats.unassigned}
              </Badge>
            </div>
          ) : null}
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs font-medium text-gray-600 dark:text-dark-200/80">
            <Switch
              name="my-cases"
              checked={filters.assignee === 'me'}
              onChange={(event) => handleMyCasesToggle(event.target.checked)}
            />
            <span>My cases</span>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-gray-600 dark:text-dark-200/80">
            <Switch
              name="auto-refresh"
              checked={autoRefresh}
              onChange={(event) => onAutoRefreshChange(event.target.checked)}
            />
            <span>Auto refresh</span>
          </div>
          <Button
            size="sm"
            variant="ghost"
            color="neutral"
            onClick={handleSaveFilter}
            disabled={!canSaveFilter}
          >
            Save filter
          </Button>
          <Button
            size="sm"
            variant="ghost"
            color="neutral"
            onClick={onReset}
            disabled={filtersEmpty}
          >
            Clear
          </Button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {presets.map((preset) => {
          const isActive = Object.entries(preset.payload).every(([key, value]) => {
            const current = (filters as any)[key];
            if (Array.isArray(value)) {
              if (!Array.isArray(current)) return value.length === 0;
              if (current.length !== value.length) return false;
              return value.every((entry, index) => current[index] === entry);
            }
            return current === value;
          });

          return (
            <Button
              key={preset.id}
              size="sm"
              variant={isActive ? 'outlined' : 'ghost'}
              color="neutral"
              className={isActive ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-200' : undefined}
              onClick={() => handlePresetApply(preset)}
            >
              {preset.label}
              {savedFilters.some((item) => item.id === preset.id) ? (
                <span
                  role="button"
                  tabIndex={0}
                  className="ml-2 cursor-pointer text-xs text-gray-400 hover:text-rose-500"
                  onClick={(event) => {
                    event.stopPropagation();
                    handleRemoveSaved(preset.id);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      handleRemoveSaved(preset.id);
                    }
                  }}
                >
                  ×
                </span>
              ) : null}
            </Button>
          );
        })}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <Select
          label="Status"
          value={filters.statuses[0] ?? ''}
          onChange={handleSelect('statuses')}
        >
          <option value="">All statuses</option>
          {CASE_STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>
              {toTitle(status)}
            </option>
          ))}
        </Select>
        <Select label="Type" value={filters.types[0] ?? ''} onChange={handleSelect('types')}>
          <option value="">All types</option>
          {CASE_TYPE_OPTIONS.map((type) => (
            <option key={type} value={type}>
              {toTitle(type)}
            </option>
          ))}
        </Select>
        <Select
          label="Severity"
          value={filters.severities[0] ?? ''}
          onChange={handleSelect('severities')}
        >
          <option value="">All severities</option>
          {CASE_SEVERITY_OPTIONS.map((severity) => (
            <option key={severity} value={severity}>
              {toTitle(severity)}
            </option>
          ))}
        </Select>
        <Select
          label="Priority"
          value={filters.priorities[0] ?? ''}
          onChange={handleSelect('priorities')}
        >
          <option value="">All priorities</option>
          {CASE_PRIORITY_OPTIONS.map((priority) => (
            <option key={priority} value={priority}>
              {toTitle(priority)}
            </option>
          ))}
        </Select>
      </div>
    </div>
  );
}

export default CaseFilters;
