import * as React from 'react';

import { Button, Surface } from '@ui';
import { UsersIcon } from '@heroicons/react/24/outline';

type UsersEmptyStateProps = {
  variant: 'desktop' | 'mobile';
  onResetFilters: () => void;
  onRefresh?: () => void;
};

export function UsersEmptyState({ variant, onResetFilters, onRefresh }: UsersEmptyStateProps): JSX.Element {
  if (variant === 'mobile') {
    return (
      <Surface variant="soft" className="space-y-3 p-6 text-center" data-testid="moderation-users-empty-mobile">
        <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-primary-500/10 text-primary-600">
          <UsersIcon className="size-6" aria-hidden="true" />
        </div>
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">No users match the filters</h3>
        <p className="text-sm text-gray-500 dark:text-dark-200/80">Adjust filters or clear them to explore the full directory.</p>
        <div className="flex justify-center">
          <Button size="sm" variant="outlined" onClick={onResetFilters}>
            Clear filters
          </Button>
        </div>
      </Surface>
    );
  }

  return (
    <Surface variant="soft" className="space-y-4 p-8 text-center" data-testid="moderation-users-empty-state">
      <div className="mx-auto flex size-14 items-center justify-center rounded-full bg-primary-500/10 text-primary-600">
        <UsersIcon className="size-7" aria-hidden="true" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">No users found</h3>
      <p className="text-sm text-gray-500 dark:text-dark-200/80">Try broadening the filters or reset to see the full moderation roster.</p>
      <div className="flex justify-center gap-2">
        <Button size="sm" variant="filled" onClick={onResetFilters}>
          Reset filters
        </Button>
        {onRefresh ? (
          <Button size="sm" variant="ghost" onClick={onRefresh}>
            Refresh data
          </Button>
        ) : null}
      </div>
    </Surface>
  );
}
