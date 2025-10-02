import React from 'react';
import { Button } from './Button';
import { Dialog } from './Dialog';
import { Input } from './Input';

type PromptDialogProps = {
  open: boolean;
  title?: React.ReactNode;
  description?: React.ReactNode;
  value: string;
  error?: string | null;
  placeholder?: string;
  submitLabel?: React.ReactNode;
  cancelLabel?: React.ReactNode;
  busy?: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
};

export function PromptDialog({
  open,
  title,
  description,
  value,
  error,
  placeholder,
  submitLabel = 'Сохранить',
  cancelLabel = 'Отмена',
  busy = false,
  onChange,
  onSubmit,
  onCancel,
}: PromptDialogProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);

  return (
    <Dialog
      open={open}
      onClose={busy ? undefined : onCancel}
      title={title}
      size="sm"
      initialFocusRef={inputRef as React.RefObject<HTMLElement>}
    >
      <div className="flex flex-col gap-4">
        {description ? <div className="text-sm text-gray-600 dark:text-dark-200">{description}</div> : null}
        <Input
          ref={inputRef}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              onSubmit();
            }
          }}
          error={error || undefined}
        />
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="outlined"
            color="neutral"
            onClick={onCancel}
            disabled={busy}
          >
            {cancelLabel}
          </Button>
          <Button onClick={onSubmit} disabled={busy}>
            {submitLabel}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}

export default PromptDialog;
