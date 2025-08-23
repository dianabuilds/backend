import type { ChangeEventHandler } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
}

export default function FieldSlug({ value, onChange }: Props) {
  const handle: ChangeEventHandler<HTMLInputElement> = (e) => onChange(e.target.value);
  return (
    <div>
      <label className="block text-sm font-medium">Slug</label>
      <input
        className="mt-1 border rounded px-2 py-1 w-full"
        value={value}
        onChange={handle}
      />
    </div>
  );
}
