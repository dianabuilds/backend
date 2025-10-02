import React from 'react';

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
    <div className="mt-3 flex flex-wrap items-center gap-2 rounded border border-primary-200 bg-primary-50 p-3 text-sm dark:border-primary-700 dark:bg-primary-900/20">
      <span className="font-medium">Selected: {selectedCount}</span>
      <button className="btn-base btn bg-green-600 text-white hover:bg-green-700 disabled:opacity-60" onClick={onPublish}>
        Publish
      </button>
      <button className="btn-base btn bg-yellow-600 text-white hover:bg-yellow-700 disabled:opacity-60" onClick={onUnpublish}>
        Unpublish
      </button>
      <button className="btn-base btn bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60" onClick={onSchedulePublish}>
        Schedule publish
      </button>
      <button className="btn-base btn bg-gray-600 text-white hover:bg-gray-700 disabled:opacity-60" onClick={onScheduleUnpublish}>
        Schedule unpublish
      </button>
      <button className="btn-base btn bg-slate-600 text-white hover:bg-slate-700 disabled:opacity-60" onClick={onArchive}>
        Archive
      </button>
      <button className="btn-base btn bg-red-600 text-white hover:bg-red-700 disabled:opacity-60" onClick={onDelete}>
        Delete selected
      </button>
    </div>
  );
}
