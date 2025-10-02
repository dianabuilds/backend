
import React from 'react';

type InputProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, 'prefix'> & {
  label?: React.ReactNode;
  error?: React.ReactNode;
  prefix?: React.ReactNode;
  hint?: React.ReactNode;
  description?: React.ReactNode;
};

// Native template classes: input-label, input-wrapper, form-input-base, form-input
export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, prefix, hint, description, className = '', ...props }, ref) => {
    const inputCls = [
      'form-input-base',
      'form-input',
      prefix ? 'ltr:pl-9 rtl:pr-9' : '',
      error ? 'border-error dark:border-error-lighter' : 'border-gray-300 hover:border-gray-400 focus:border-primary-600 dark:border-dark-450 dark:hover:border-dark-400 dark:focus:border-primary-500',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    const isPlainLabel = typeof label === 'string' || typeof label === 'number';
    const labelText = label ? (
      <label className="input-label">
        {isPlainLabel ? <span className="input-label">{label}</span> : label}
      </label>
    ) : null;

    const helper = description ?? hint;
    const showError = error && typeof error !== 'boolean';

    return (
      <div className="input-root">
        {labelText}
        <div className={`input-wrapper relative ${label ? 'mt-1.5' : ''}`}>
          <input ref={ref} className={inputCls} {...props} />
          {prefix && (
            <div className="prefix ltr:left-0 rtl:right-0 absolute top-0 flex h-full w-9 items-center justify-center text-gray-400 peer-focus:text-primary-600 transition-colors">
              {prefix}
            </div>
          )}
        </div>
        {showError && <div className="mt-1 text-xs text-error">{error}</div>}
        {helper && !showError && (
          <span className="input-description dark:text-dark-300 mt-1 text-xs text-gray-400">{helper}</span>
        )}
      </div>
    );
  },
);


