import { useEffect, useState } from 'react';

import { sendNotification } from '../../api/notifications';
import { useAuth } from '../../auth/AuthContext';
import { Modal } from '../../shared/ui/Modal';
import { useToast } from '../ToastProvider';
import { validateNotification } from './NotificationForm.validation';
import { type NotificationErrors, NotificationFormFields, type NotificationFormValues } from './NotificationFormCore';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function SendToUserModal({ isOpen, onClose }: Props) {
  const { user } = useAuth();
  const { addToast } = useToast();
  const [userId, setUserId] = useState('');
  const [values, setValues] = useState<NotificationFormValues>({ title: '', message: '', type: 'system' });
  const [errors, setErrors] = useState<NotificationErrors>({ title: null, message: null });

  useEffect(() => {
    if (user && !userId) setUserId(user.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const validate = () => {
    const { valid, errors: e } = validateNotification(values);
    setErrors(e);
    return valid;
  };

  const handleSend = async () => {
    if (!validate()) return;
    try {
      await sendNotification({ user_id: userId, title: values.title, message: values.message, type: values.type });
      addToast({ title: 'Notification sent', variant: 'success' });
      setValues((v) => ({ ...v, title: '', message: '' }));
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
        <NotificationFormFields
          values={values}
          errors={errors}
          onChange={(patch) => setValues((v) => ({ ...v, ...patch }))}
        />
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
