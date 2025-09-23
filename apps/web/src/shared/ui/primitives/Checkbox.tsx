import React from 'react';

type CheckboxProps = Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label?: string;
};

// Native template classes: form-checkbox + input-label
export function Checkbox({ label, className = '', ...props }: CheckboxProps) {
  const control = <input className={`form-checkbox ${className}`} type="checkbox" {...props} />;
  return label ? (
    <label className="input-label inline-flex items-center gap-2">
      {control}
      <span className="label">{label}</span>
    </label>
  ) : (
    control
  );
}
