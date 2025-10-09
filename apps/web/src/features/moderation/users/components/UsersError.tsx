import * as React from 'react';

import { Button } from '@ui';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

type UsersErrorProps = {
  message: string;
  onRetry: () => void;
};

export function UsersError({ message, onRetry }: UsersErrorProps): JSX.Element {
  return (
    <div className="px-1" data-testid="moderation-users-error">
      <div className="flex flex-col gap-3 rounded-3xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700 shadow-[0_10px_30px_-28px_rgba(225,29,72,0.8)] dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200">
        <div className="flex items-center gap-2 font-medium">
          <ExclamationTriangleIcon className="size-5" aria-hidden="true" />
          {message}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant="outlined" color="error" onClick={onRetry}>
            Try again
          </Button>
        </div>
      </div>
    </div>
  );
}
