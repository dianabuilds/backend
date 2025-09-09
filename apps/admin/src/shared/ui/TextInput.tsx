import type { InputHTMLAttributes } from 'react';

export function TextInput({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`border rounded px-2 py-1 ${className}`.trim()} />;
}
