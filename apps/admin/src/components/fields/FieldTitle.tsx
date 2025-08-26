import { forwardRef, type ChangeEventHandler } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  error?: string | null;
}

const FieldTitle = forwardRef<HTMLInputElement, Props>(function FieldTitle(
  { value, onChange, error },
  ref,
) {
  const handle: ChangeEventHandler<HTMLInputElement> = (e) => onChange(e.target.value);
  return (
    <div>
      <label className="block text-sm font-medium">Title</label>
      <input
        ref={ref}
        className={`mt-1 border rounded px-2 py-1 w-full ${
          error ? "border-red-500" : ""
        }`}
        value={value}
        onChange={handle}
      />
      {error ? <p className="mt-1 text-xs text-red-600">{error}</p> : null}
    </div>
  );
});

export default FieldTitle;
