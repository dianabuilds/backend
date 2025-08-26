import { useId, type InputHTMLAttributes } from "react";

import TagInput from "../TagInput";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  value: string[];
  onChange: (tags: string[]) => void;
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
      <TagInput
        id={inputId}
        aria-describedby={descId}
        value={value}
        onChange={onChange}
        className="mt-1 w-full"
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
