import type { ButtonHTMLAttributes } from 'react';

export function Button({ className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} className={`px-3 py-1 rounded border ${className}`.trim()} />;
}

export default Button;
