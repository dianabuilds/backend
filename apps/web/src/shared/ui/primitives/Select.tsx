import React from 'react';

type SelectProps = React.SelectHTMLAttributes<HTMLSelectElement> & {
  label?: string;
  error?: string | boolean;
};

const lookAndFeel =
  'rounded-2xl border border-white/60 bg-white/90 shadow-[0_18px_45px_-32px_rgba(79,70,229,0.45)] focus:border-primary-500 focus:ring-2 focus:ring-primary-500/25 focus-visible:outline-none dark:border-white/10 dark:bg-dark-800/80';

// Minimal styled select matching template input styles
export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, className = '', children, ...props }, ref) => {
    const base = [
      'form-input-base',
      'form-select',
      error
        ? 'border-error dark:border-error-lighter'
        : 'border-gray-300 hover:border-gray-400 focus:border-primary-600 dark:border-dark-450 dark:hover:border-dark-400 dark:focus:border-primary-500',
      lookAndFeel,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className="input-root">
        {label && (
          <label className="input-label">
            <span className="input-label">{label}</span>
          </label>
        )}
        <div className={`input-wrapper relative ${label ? 'mt-1.5' : ''}`}>
          <select ref={ref} className={base} {...props}>
            {children}
          </select>
        </div>
      </div>
    );
  },
);

