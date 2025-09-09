import { type InputHTMLAttributes, useId } from 'react';

import TagInput from '../TagInput';

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  value?: string[];
  onChange?: (tags: string[]) => void;
  error?: string | null;
  description?: string;
}

export default function FieldTags({
  value = [],
  onChange,
  id,
  error,
  description,
  ...rest
}: Props) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descId = error || description ? `${inputId}-desc` : undefined;
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
        className={`mt-1 w-full ${error ? 'border-red-500' : ''}`}
        {...rest}
      />
      {error ? (
        <p id={descId} className="mt-1 text-xs text-red-600">
          {error}
        </p>
      ) : description ? (
        <p id={descId} className="mt-1 text-xs text-gray-600">
          {description}
        </p>
      ) : null}
    </div>
  );
}
