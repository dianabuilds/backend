import React from 'react';
import { PromptDialog } from '../ui/primitives/PromptDialog';

type PromptDialogOptions = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  placeholder?: string;
  submitLabel?: React.ReactNode;
  cancelLabel?: React.ReactNode;
  initialValue?: string;
  validate?: (value: string) => string | null;
};

type UsePromptDialogResult = {
  prompt: (options: PromptDialogOptions) => Promise<string | null>;
  promptElement: React.ReactNode;
};

const defaultOptions: PromptDialogOptions & { open: boolean } = {
  open: false,
  title: undefined,
  description: undefined,
  placeholder: undefined,
  submitLabel: undefined,
  cancelLabel: undefined,
  initialValue: '',
  validate: undefined,
};

export function usePromptDialog(): UsePromptDialogResult {
  const resolverRef = React.useRef<((value: string | null) => void) | null>(null);
  const [options, setOptions] = React.useState(defaultOptions);
  const [value, setValue] = React.useState('');
  const [error, setError] = React.useState<string | null>(null);
  const validate = options.validate;

  const close = React.useCallback((result: string | null) => {
    const resolver = resolverRef.current;
    resolverRef.current = null;
    setOptions(defaultOptions);
    setValue('');
    setError(null);
    if (resolver) resolver(result);
  }, []);

  const submit = React.useCallback(() => {
    const trimmed = value.trim();
    if (validate) {
      const validation = validate(trimmed);
      if (validation) {
        setError(validation);
        return;
      }
    }
    close(trimmed);
  }, [close, validate, value]);

  const prompt = React.useCallback((opts: PromptDialogOptions) => {
    return new Promise<string | null>((resolve) => {
      resolverRef.current = resolve;
      setOptions({ open: true, ...opts });
      setValue(opts.initialValue ?? '');
      setError(null);
    });
  }, []);

  const promptElement = (
    <PromptDialog
      open={options.open}
      title={options.title}
      description={options.description}
      value={value}
      placeholder={options.placeholder}
      submitLabel={options.submitLabel}
      cancelLabel={options.cancelLabel}
      error={error}
      onChange={(next) => {
        setValue(next);
        if (error) setError(null);
      }}
      onSubmit={submit}
      onCancel={() => close(null)}
    />
  );

  return { prompt, promptElement };
}

export default usePromptDialog;
