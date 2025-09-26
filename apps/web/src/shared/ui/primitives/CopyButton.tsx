import React from 'react';

type CopyButtonRenderProps = {
  copy: () => Promise<void> | void;
  copied: boolean;
};

type CopyButtonProps = {
  value: string;
  children: (props: CopyButtonRenderProps) => React.ReactNode;
  copyTimeoutMs?: number;
  onCopyError?: (error: unknown) => void;
};

function writeClipboard(value: string): Promise<void> {
  if (navigator?.clipboard?.writeText) {
    return navigator.clipboard.writeText(value);
  }
  return Promise.reject(new Error('clipboard_unavailable'));
}

export function CopyButton({ value, children, copyTimeoutMs = 1500, onCopyError }: CopyButtonProps) {
  const [copied, setCopied] = React.useState(false);
  const timeoutRef = React.useRef<number | null>(null);

  React.useEffect(() => () => {
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const copy = React.useCallback(async () => {
    try {
      await writeClipboard(value);
      setCopied(true);
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = window.setTimeout(() => {
        setCopied(false);
        timeoutRef.current = null;
      }, copyTimeoutMs);
    } catch (error) {
      setCopied(false);
      if (onCopyError) onCopyError(error);
    }
  }, [value, copyTimeoutMs, onCopyError]);

  return <>{children({ copy, copied })}</>;
}
