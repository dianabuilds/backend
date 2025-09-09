import type { LucideIcon } from 'lucide-react';
import { Archive, CheckCircle2, Clock, FileText } from 'lucide-react';

export type Status = 'draft' | 'in_review' | 'published' | 'archived';

interface StatusCellProps {
  status: Status;
}

const STATUS_CONFIG: Record<Status, { Icon: LucideIcon; label: string; active: string }> = {
  draft: { Icon: FileText, label: 'Draft', active: 'text-gray-600' },
  in_review: { Icon: Clock, label: 'In review', active: 'text-blue-600' },
  published: { Icon: CheckCircle2, label: 'Published', active: 'text-green-600' },
  archived: { Icon: Archive, label: 'Archived', active: 'text-red-600' },
};

export default function StatusCell({ status }: StatusCellProps) {
  return (
    <div className="flex items-center justify-center gap-1">
      {(
        Object.entries(STATUS_CONFIG) as [
          Status,
          { Icon: LucideIcon; label: string; active: string },
        ][]
      ).map(([key, { Icon, label, active }]) => (
        <Icon
          key={key}
          className={`h-4 w-4 ${status === key ? active : 'text-gray-400'}`}
          aria-label={label}
          title={label}
        />
      ))}
    </div>
  );
}
