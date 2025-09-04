import type { LucideIcon } from "lucide-react";
import { Archive, CheckCircle2, Clock, FileText } from "lucide-react";

export type Status = "draft" | "in_review" | "published" | "archived";

interface StatusCellProps {
  status: Status;
}

const statuses: Record<
  Status,
  { icon: LucideIcon; label: string; color: string }
> = {
  draft: { icon: FileText, label: "Draft", color: "text-gray-600" },
  in_review: { icon: Clock, label: "In review", color: "text-blue-600" },
  published: {
    icon: CheckCircle2,
    label: "Published",
    color: "text-green-600",
  },
  archived: { icon: Archive, label: "Archived", color: "text-red-600" },
};

export default function StatusCell({ status }: StatusCellProps) {
  return (
    <div className="flex items-center justify-center gap-1">
      {(Object.entries(statuses) as [Status, { icon: LucideIcon; label: string; color: string }][]).map(
        ([key, { icon: Icon, label, color }]) => (
          <Icon
            key={key}
            className={`h-4 w-4 ${status === key ? color : "text-gray-400"}`}
            aria-label={label}
            title={label}
          />
        ),
      )}
    </div>
  );
}

