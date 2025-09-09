import { useState } from 'react';
import { createRoot } from 'react-dom/client';

import Button from './Button';
import Modal from './Modal';
import TextInput from './TextInput';

export function alertDialog(message: string): void {
  const div = document.createElement('div');
  document.body.appendChild(div);
  const root = createRoot(div);
  const close = () => {
    root.unmount();
    div.remove();
  };
  root.render(
    <Modal isOpen onClose={close}>
      <p>{message}</p>
      <div className="mt-4 text-right">
        <Button onClick={close}>OK</Button>
      </div>
    </Modal>,
  );
}

export function confirmDialog(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    const div = document.createElement('div');
    document.body.appendChild(div);
    const root = createRoot(div);
    const close = (result: boolean) => {
      resolve(result);
      root.unmount();
      div.remove();
    };
    root.render(
      <Modal isOpen onClose={() => close(false)}>
        <p>{message}</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button onClick={() => close(true)}>OK</Button>
          <Button onClick={() => close(false)}>Cancel</Button>
        </div>
      </Modal>,
    );
  });
}

export function promptDialog(message: string, defaultValue = ''): Promise<string | undefined> {
  return new Promise((resolve) => {
    const div = document.createElement('div');
    document.body.appendChild(div);
    const root = createRoot(div);
    function Prompt() {
      const [value, setValue] = useState(defaultValue);
      const close = (v: string | undefined) => {
        resolve(v);
        root.unmount();
        div.remove();
      };
      return (
        <Modal isOpen onClose={() => close(undefined)}>
          <p>{message}</p>
          <TextInput
            className="mt-2 w-full"
            autoFocus
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') close(value);
            }}
          />
          <div className="mt-4 flex justify-end gap-2">
            <Button onClick={() => close(value)}>OK</Button>
            <Button onClick={() => close(undefined)}>Cancel</Button>
          </div>
        </Modal>
      );
    }
    root.render(<Prompt />);
  });
}
