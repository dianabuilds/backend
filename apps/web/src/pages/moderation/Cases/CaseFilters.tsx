import React from 'react';
import { Button, Collapse, Input, Select } from '@ui';
import { CASE_PRIORITY_OPTIONS, CASE_SEVERITY_OPTIONS, CASE_STATUS_OPTIONS, CASE_TYPE_OPTIONS } from './constants';
import { CaseFiltersState } from './types';

type Props = {
  filters: CaseFiltersState;
  onChange: (next: Partial<CaseFiltersState>) => void;
  onReset: () => void;
  loading?: boolean;
  stats?: { total: number; open: number; unassigned: number };
};

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

export function CaseFilters({ filters, onChange, onReset, loading, stats }: Props) {
  const [expanded, setExpanded] = React.useState(true);

  const emit = (key: keyof CaseFiltersState, value: any) => {
    onChange({ [key]: value } as Partial<CaseFiltersState>);
  };

  const handleSelect = (key: keyof CaseFiltersState, value: string) => {
    emit(key, value ? [value] : []);
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold">Moderation cases</h1>
          <Button size="sm" variant="ghost" color="neutral" onClick={() => setExpanded((prev) => !prev)}>
            {expanded ? 'Hide filters' : 'Show filters'}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            color="neutral"
            onClick={onReset}
            disabled={filtersAreEmpty(filters)}
          >
            Reset filters
          </Button>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          {stats && (
            <>
              <span>Total: {stats.total}</span>
              <span className="hidden sm:inline">| Open: {stats.open}</span>
              <span className="hidden sm:inline">| Unassigned: {stats.unassigned}</span>
            </>
          )}
          {loading && <span className="text-primary-600">Loading...</span>}
        </div>
      </div>

      <Collapse open={expanded}>
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              className="w-full min-w-[220px] flex-1"
              placeholder="Search id / title / subject"
              value={filters.query}
              onChange={(e) => emit('query', e.target.value)}
            />
            <Input
              className="w-40"
              placeholder="Assignee"
              value={filters.assignee}
              onChange={(e) => emit('assignee', e.target.value)}
            />
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <Select
              label="Statuses"
              value={filters.statuses[0] ?? ''}
              onChange={(e) => handleSelect('statuses', e.target.value)}
            >
              <option value="">All statuses</option>
              {CASE_STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </Select>
            <Select
              label="Types"
              value={filters.types[0] ?? ''}
              onChange={(e) => handleSelect('types', e.target.value)}
            >
              <option value="">All types</option>
              {CASE_TYPE_OPTIONS.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </Select>
            <Select
              label="Severity"
              value={filters.severities[0] ?? ''}
              onChange={(e) => handleSelect('severities', e.target.value)}
            >
              <option value="">All severities</option>
              {CASE_SEVERITY_OPTIONS.map((severity) => (
                <option key={severity} value={severity}>
                  {severity}
                </option>
              ))}
            </Select>
            <Select
              label="Priority"
              value={filters.priorities[0] ?? ''}
              onChange={(e) => handleSelect('priorities', e.target.value)}
            >
              <option value="">All priorities</option>
              {CASE_PRIORITY_OPTIONS.map((priority) => (
                <option key={priority} value={priority}>
                  {priority}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </Collapse>
    </div>
  );
}

export default CaseFilters;
