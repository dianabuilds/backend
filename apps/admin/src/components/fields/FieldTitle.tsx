import { type ChangeEventHandler, forwardRef, type InputHTMLAttributes, useId } from 'react';

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  value?: string;
  onChange?: (value: string) => void;
  error?: string | null;
  description?: string;
}

const FieldTitle = forwardRef<HTMLInputElement, Props>(function FieldTitle(
  { value = '', onChange, error, description, id, ...rest },
  ref,
) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const descId = `${inputId}-desc`;
  const handle: ChangeEventHandler<HTMLInputElement> = (e) => onChange?.(e.target.value);
  return (
    <div>
      <label htmlFor={inputId} className="block text-sm font-medium text-gray-900">
        Title
      </label>
      <input
        id={inputId}
        ref={ref}
        aria-describedby={description || error ? descId : undefined}
        className={`mt-1 w-full rounded border px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? 'border-red-500' : ''
        }`}
        value={value}
        onChange={handle}
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
});

export default FieldTitle;
