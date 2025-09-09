import { type ChangeEventHandler, type TextareaHTMLAttributes, useId } from 'react';

interface Props extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'onChange'> {
  value: string;
  onChange: (value: string) => void;
  error?: string | null;
}

export default function FieldSummary({ value, onChange, error, id, ...rest }: Props) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descId = `${inputId}-desc`;
  const handle: ChangeEventHandler<HTMLTextAreaElement> = (e) => onChange(e.target.value);
  return (
    <div>
      <label htmlFor={inputId} className="block text-sm font-medium text-gray-900">
        Summary
      </label>
      <textarea
        id={inputId}
        aria-describedby={descId}
        className={`mt-1 w-full rounded border px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? 'border-red-500' : ''
        }`}
        rows={3}
        value={value}
        onChange={handle}
        placeholder="Short description"
        {...rest}
      />
      {error ? (
        <p id={descId} className="mt-1 text-xs text-red-600">
          {error}
        </p>
      ) : (
        <p id={descId} className="mt-1 text-xs text-gray-600">
          A concise summary shown in lists and search results.
        </p>
      )}
    </div>
  );
}
