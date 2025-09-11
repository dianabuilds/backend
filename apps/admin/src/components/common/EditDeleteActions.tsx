interface Props {
  onEdit?: () => void;
  onDelete?: () => void;
  editLabel?: string;
  deleteLabel?: string;
}

export default function EditDeleteActions({
  onEdit,
  onDelete,
  editLabel = 'Edit',
  deleteLabel = 'Delete',
}: Props) {
  return (
    <div className="inline-flex items-center">
      {onEdit ? (
        <button onClick={onEdit} className="text-blue-600 hover:underline mr-2">
          {editLabel}
        </button>
      ) : null}
      {onDelete ? (
        <button onClick={onDelete} className="text-red-600 hover:underline">
          {deleteLabel}
        </button>
      ) : null}
    </div>
  );
}
