import type { ChangeEventHandler } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  error?: string | null;
}

export default function FieldSummary({ value, onChange, error }: Props) {
  const handle: ChangeEventHandler<HTMLTextAreaElement> = (e) =>
    onChange(e.target.value);
  return (
    <div>
      <label className="block text-sm font-medium">Summary</label>
      <textarea
        className={`mt-1 border rounded px-2 py-1 w-full ${
          error ? "border-red-500" : ""
        }`}
        rows={3}
        value={value}
        onChange={handle}
        placeholder="Short description"
      />
      {error ? (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      ) : (
        <p className="mt-1 text-xs text-gray-500">
          A concise summary shown in lists and search results.
        </p>
      )}
    </div>
  );
}

