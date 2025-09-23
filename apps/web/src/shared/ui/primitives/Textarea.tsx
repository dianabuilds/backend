import React from 'react';

type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label?: React.ReactNode;
  description?: React.ReactNode;
  error?: React.ReactNode | boolean;
  unstyled?: boolean;
};

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, description, error, className = '', unstyled, ...props }, ref) => {
    const inputCls = [
      'form-textarea-base',
      !unstyled && [
        'form-textarea',
        error
          ? 'border-error dark:border-error-lighter'
          : 'border-gray-300 hover:border-gray-400 focus:border-primary-600 dark:border-dark-450 dark:hover:border-dark-400 dark:focus:border-primary-500',
      ],
      className,
    ]
      .flat()
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
          <textarea ref={ref} className={inputCls} {...props} />
        </div>
        {!!error && typeof error !== 'boolean' && (
          <div className="mt-1 text-xs text-error">{error}</div>
        )}
        {description && (
          <span className="input-description dark:text-dark-300 mt-1 text-xs text-gray-400">
            {description}
          </span>
        )}
      </div>
    );
  },
);

