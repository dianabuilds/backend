interface PublishBarProps {
  onPublish?: () => void;
}

export default function PublishBar({ onPublish }: PublishBarProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-500">Draft</span>
      <button
        type="button"
        className="px-3 py-1 rounded bg-green-600 text-white hover:bg-green-700"
        onClick={onPublish}
      >
        Publish
      </button>
    </div>
  );
}
