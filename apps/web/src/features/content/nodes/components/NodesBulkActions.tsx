import React from 'react';

import { Button } from '@ui';

export type NodesBulkActionsProps = {
  selectedCount: number;
  onPublish: () => Promise<void> | void;
  onUnpublish: () => Promise<void> | void;
  onSchedulePublish: () => Promise<void> | void;
  onScheduleUnpublish: () => Promise<void> | void;
  onArchive: () => Promise<void> | void;
  onDelete: () => Promise<void> | void;
};

export function NodesBulkActions({
  selectedCount,
  onPublish,
  onUnpublish,
  onSchedulePublish,
  onScheduleUnpublish,
  onArchive,
  onDelete,
}: NodesBulkActionsProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-primary-200 bg-primary-50/70 px-3 py-2 text-sm font-medium text-primary-900 shadow-sm dark:border-primary-700/60 dark:bg-primary-900/20 dark:text-primary-50">
      <span className="text-sm font-semibold">Selected: {selectedCount}</span>
      <Button size="sm" variant="filled" color="primary" onClick={() => void onPublish()}>
        Publish
      </Button>
      <Button size="sm" variant="outlined" color="primary" onClick={() => void onUnpublish()}>
        Unpublish
      </Button>
      <Button size="sm" variant="outlined" color="neutral" onClick={() => void onSchedulePublish()}>
        Schedule publish
      </Button>
      <Button size="sm" variant="outlined" color="neutral" onClick={() => void onScheduleUnpublish()}>
        Schedule unpublish
      </Button>
      <Button size="sm" variant="ghost" color="neutral" onClick={() => void onArchive()}>
        Archive
      </Button>
      <Button size="sm" variant="filled" color="error" onClick={() => void onDelete()}>
        Delete selected
      </Button>
    </div>
  );
}
