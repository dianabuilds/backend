
interface Props {
  primaryLabel?: string;
  onPrimary?: () => void;
  primaryDisabled?: boolean;
  secondaryLabel?: string;
  onSecondary?: () => void;
  secondaryDisabled?: boolean;
  align?: 'start' | 'end';
  className?: string;
}

export default function FormActions({
  primaryLabel = 'Save',
  onPrimary,
  primaryDisabled,
  secondaryLabel = 'Reset',
  onSecondary,
  secondaryDisabled,
  align = 'start',
  className = '',
}: Props) {
  return (
    <div className={`mt-3 flex gap-2 ${align === 'end' ? 'justify-end' : ''} ${className}`.trim()}>
      {onPrimary ? (
        <button
          onClick={onPrimary}
          disabled={primaryDisabled}
          className={`text-sm px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {primaryLabel}
        </button>
      ) : null}
      {onSecondary ? (
        <button
          onClick={onSecondary}
          disabled={secondaryDisabled}
          className={`text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {secondaryLabel}
        </button>
      ) : null}
    </div>
  );
}
