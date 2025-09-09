import { useEffect, useState } from 'react';
import { z } from 'zod';

import { sendNotification } from '../../api/notifications';
import { useAuth } from '../../auth/AuthContext';
import Modal from '../../shared/ui/Modal';
import { useToast } from '../ToastProvider';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function SendToUserModal({ isOpen, onClose }: Props) {
  const { user } = useAuth();
  const { addToast } = useToast();
  const [userId, setUserId] = useState('');
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [type, setType] = useState('system');
  const [errors, setErrors] = useState<{ title: string | null; message: string | null }>({
    title: null,
    message: null,
  });

  useEffect(() => {
    if (user && !userId) setUserId(user.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const schema = z.object({
    title: z.string().min(1, 'Title required'),
    message: z.string().min(1, 'Message required'),
  });

  const validate = () => {
    const res = schema.safeParse({ title, message });
    setErrors({
      title: res.success ? null : (res.error.formErrors.fieldErrors.title?.[0] ?? null),
      message: res.success ? null : (res.error.formErrors.fieldErrors.message?.[0] ?? null),
    });
    return res.success;
  };

  const handleSend = async () => {
    if (!validate()) return;
    try {
      await sendNotification({ user_id: userId, title, message, type });
      addToast({ title: 'Notification sent', variant: 'success' });
      setTitle('');
      setMessage('');
      onClose();
    } catch (e) {
      addToast({
        title: 'Failed to send',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Send to user">
      <div className="flex flex-col gap-2">
        <div className="flex flex-col">
          <label className="text-sm text-gray-600">User ID</label>
          <input
            className="border rounded px-2 py-1"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="UUID"
          />
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-600">Type</label>
          <select
            className="border rounded px-2 py-1"
            value={type}
            onChange={(e) => setType(e.target.value)}
          >
            <option value="system">system</option>
            <option value="info">info</option>
            <option value="warning">warning</option>
            <option value="quest">quest</option>
          </select>
        </div>
        <div className="flex flex-col">
          <label htmlFor="send-title" className="text-sm text-gray-600">
            Title
          </label>
          <input
            id="send-title"
            className="border rounded px-2 py-1"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          {errors.title && <span className="text-xs text-red-600">{errors.title}</span>}
        </div>
        <div className="flex flex-col">
          <label htmlFor="send-message" className="text-sm text-gray-600">
            Message
          </label>
          <input
            id="send-message"
            className="border rounded px-2 py-1"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          {errors.message && <span className="text-xs text-red-600">{errors.message}</span>}
        </div>
        <div className="flex justify-end gap-2 mt-2">
          <button className="px-3 py-1 rounded border" onClick={onClose}>
            Cancel
          </button>
          <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={handleSend}>
            Send
          </button>
        </div>
      </div>
    </Modal>
  );
}
