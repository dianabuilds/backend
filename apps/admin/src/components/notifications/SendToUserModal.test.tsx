import '@testing-library/jest-dom';

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import * as api from '../../api/notifications';
import SendToUserModal from './SendToUserModal';

vi.mock('../../auth/AuthContext', () => ({
  useAuth: () => ({ user: { id: 'u1' } }),
}));
vi.mock('../ToastProvider', () => ({
  useToast: () => ({ addToast: vi.fn() }),
}));

describe('SendToUserModal', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sends notification', async () => {
    const send = vi
      .spyOn(api, 'sendNotification')
      .mockResolvedValue({} as unknown as Awaited<ReturnType<typeof api.sendNotification>>);
    render(<SendToUserModal isOpen={true} onClose={() => {}} />);
    fireEvent.change(screen.getByLabelText('Title'), {
      target: { value: 'hi' },
    });
    fireEvent.change(screen.getByLabelText('Message'), {
      target: { value: 'msg' },
    });
    fireEvent.click(screen.getByText('Send'));
    await waitFor(() =>
      expect(send).toHaveBeenCalledWith({
        user_id: 'u1',
        title: 'hi',
        message: 'msg',
        type: 'system',
      }),
    );
  });
});
