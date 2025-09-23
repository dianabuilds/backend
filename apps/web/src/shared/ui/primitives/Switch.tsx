import React from 'react';

type SwitchProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label?: React.ReactNode;
  unstyled?: boolean;
};

export const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  ({ label, className = '', unstyled, disabled, ...props }, ref) => {
    const cls = [
      'form-switch',
      !unstyled && [
        'bg-gray-300 before:bg-gray-50 checked:bg-primary-600 checked:before:bg-white dark:bg-surface-1 dark:before:bg-dark-50 dark:checked:bg-primary-400 dark:checked:before:bg-white focus-visible:ring-3 focus-visible:ring-primary-500/50',
        disabled
          ? 'before:bg-gray-400 bg-gray-150 border border-gray-200 pointer-events-none select-none opacity-70 dark:bg-dark-450 dark:border-dark-450 dark:before:bg-dark-800 dark:opacity-60'
          : '',
      ],
      className,
    ]
      .flat()
      .filter(Boolean)
      .join(' ');

    const input = (
      <input ref={ref} type="checkbox" className={cls} disabled={disabled} {...props} />
    );

    if (!label) return input;
    return (
      <label className="input-label inline-flex items-center gap-2">
        {input}
        <span className="label">{label}</span>
      </label>
    );
  },
);

