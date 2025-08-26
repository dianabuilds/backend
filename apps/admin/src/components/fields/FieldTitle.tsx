import { forwardRef, type ChangeEventHandler } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
}

const FieldTitle = forwardRef<HTMLInputElement, Props>(function FieldTitle(
  { value, onChange },
  ref,
) {
  const handle: ChangeEventHandler<HTMLInputElement> = (e) => onChange(e.target.value);
  return (
    <div>
      <label className="block text-sm font-medium">Title</label>
      <input
        ref={ref}
        className="mt-1 border rounded px-2 py-1 w-full"
        value={value}
        onChange={handle}
      />
    </div>
  );
});

export default FieldTitle;
