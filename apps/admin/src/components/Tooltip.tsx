// @ts-nocheck
import { Info } from 'lucide-react';

interface TooltipProps {
  text: string;
  className?: string;
}

export default function Tooltip({ text, className }: TooltipProps) {
  return (
    <Info
      className={['inline-block w-4 h-4 text-gray-400 cursor-help', className || ''].join(' ')}
      aria-label={text}
      title={text}
    />
  );
}

