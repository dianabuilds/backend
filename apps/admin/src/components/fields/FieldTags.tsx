import { useId, type SelectHTMLAttributes } from "react";

import TagPicker, { type TagOut } from "../tags/TagPicker";

interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  value: TagOut[];
  onChange: (tags: TagOut[]) => void;
  description?: string;
}

export default function FieldTags({
  value,
  onChange,
  id,
  description,
  ...rest
}: Props) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descId = description ? `${inputId}-desc` : undefined;
  return (
    <div>
      <label htmlFor={inputId} className="block text-sm font-medium text-gray-900">
        Tags
      </label>
      <TagPicker
        id={inputId}
        aria-describedby={descId}
        value={value}
        onChange={onChange}
        className="mt-1 w-full rounded border px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        {...rest}
      />
      {description ? (
        <p id={descId} className="mt-1 text-xs text-gray-600">
          {description}
        </p>
      ) : null}
    </div>
  );
}
