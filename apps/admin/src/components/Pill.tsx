import type { ReactNode } from 'react';

type PillVariant = 'ok' | 'warn' | 'danger';

interface PillProps {
  variant: PillVariant;
  children: ReactNode;
  className?: string;
}

const variants: Record<PillVariant, string> = {
  ok: 'bg-green-200 text-green-800',
  warn: 'bg-yellow-200 text-yellow-800',
  danger: 'bg-red-200 text-red-800',
};

export default function Pill({ variant, children, className = '' }: PillProps) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap px-2 py-0.5 rounded text-xs ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
