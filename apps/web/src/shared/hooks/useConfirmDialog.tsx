import React from 'react';
import { ConfirmDialog } from '@ui/primitives/ConfirmDialog';

type ConfirmDialogOptions = {
  title?: React.ReactNode;
  description?: React.ReactNode;
  confirmLabel?: React.ReactNode;
  cancelLabel?: React.ReactNode;
  destructive?: boolean;
  busy?: boolean;
};

type UseConfirmDialogResult = {
  confirm: (options: ConfirmDialogOptions) => Promise<boolean>;
  confirmationElement: React.ReactNode;
};

const initialState: ConfirmDialogOptions & { open: boolean } = {
  open: false,
  title: undefined,
  description: undefined,
  confirmLabel: undefined,
  cancelLabel: undefined,
  destructive: false,
  busy: false,
};

export function useConfirmDialog(): UseConfirmDialogResult {
  const resolverRef = React.useRef<((value: boolean) => void) | null>(null);
  const [state, setState] = React.useState(initialState);

  const close = React.useCallback(
    (result: boolean) => {
      const resolver = resolverRef.current;
      resolverRef.current = null;
      setState(initialState);
      if (resolver) resolver(result);
    },
    [],
  );

  const confirm = React.useCallback((options: ConfirmDialogOptions) => {
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve;
      setState({ open: true, ...options });
    });
  }, []);

  const confirmationElement = (
    <ConfirmDialog
      open={state.open}
      title={state.title}
      description={state.description}
      confirmLabel={state.confirmLabel}
      cancelLabel={state.cancelLabel}
      destructive={state.destructive}
      busy={state.busy}
      onConfirm={() => close(true)}
      onCancel={() => close(false)}
    />
  );

  return { confirm, confirmationElement };
}

export default useConfirmDialog;
