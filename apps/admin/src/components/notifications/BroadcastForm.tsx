import { useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { createCampaign, estimateCampaign } from '../../api/notifications';
import type { CampaignCreate, CampaignFilters } from '../../openapi';
import { Modal } from '../../shared/ui';
import { useToast } from '../ToastProvider';
import NotificationFilters from './NotificationFilters';
import { validateNotification } from './NotificationForm.validation';
import { type NotificationErrors, NotificationFormFields, type NotificationFormValues } from './NotificationFormCore';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export default function BroadcastForm({ isOpen, onClose }: Props) {
  const { addToast } = useToast();
  const qc = useQueryClient();
  const [values, setValues] = useState<NotificationFormValues>({
    title: '',
    message: '',
    type: 'system',
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [role, setRole] = useState('');
  const [isActive, setIsActive] = useState('any');
  const [isPremium, setIsPremium] = useState('any');
  const [createdFrom, setCreatedFrom] = useState('');
  const [createdTo, setCreatedTo] = useState('');
  const [estimate, setEstimate] = useState<number | null>(null);
  const [errors, setErrors] = useState<NotificationErrors>({ title: null, message: null });

  const validate = () => {
    const { valid, errors: e } = validateNotification(values);
    setErrors(e);
    return valid;
  };

  const payloadFilters = useMemo(() => {
    const f: CampaignFilters = {};
    if (role) f.role = role;
    if (isActive !== 'any') f.is_active = isActive === 'true';
    if (isPremium !== 'any') f.is_premium = isPremium === 'true';
    if (createdFrom) f.created_from = new Date(createdFrom).toISOString();
    if (createdTo) f.created_to = new Date(createdTo).toISOString();
    return f;
  }, [role, isActive, isPremium, createdFrom, createdTo]);

  const doDryRun = async () => {
    if (!validate()) return;
    try {
      const res = (await estimateCampaign(payloadFilters)) as {
        total_estimate?: number;
      };
      setEstimate(res.total_estimate ?? 0);
      addToast({
        title: 'Estimated recipients',
        description: String(res.total_estimate ?? 0),
        variant: 'info',
      });
    } catch (e) {
      addToast({
        title: 'Dry-run failed',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  const doStart = async () => {
    if (!validate()) return;
    try {
      const payload: CampaignCreate = {
        title: values.title,
        message: values.message,
        type: values.type,
        filters: payloadFilters,
      };
      await createCampaign(payload);
      setEstimate(null);
      setValues((v) => ({ ...v, title: '', message: '' }));
      addToast({ title: 'Broadcast started', variant: 'success' });
      void qc.invalidateQueries({ queryKey: ['campaigns'] });
      onClose();
    } catch (e) {
      addToast({
        title: 'Failed to start broadcast',
        description: e instanceof Error ? e.message : String(e),
        variant: 'error',
      });
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Start broadcast">
      <div className="flex flex-col gap-2">
        <NotificationFormFields
          values={values}
          errors={errors}
          onChange={(patch) => setValues((v) => ({ ...v, ...patch }))}
          multilineMessage
        />
        <button
          className="self-start text-sm text-blue-600"
          onClick={() => setShowAdvanced((v) => !v)}
        >
          {showAdvanced ? 'Hide filters' : 'Show filters'}
        </button>
        {showAdvanced && (
          <NotificationFilters
            role={role}
            isActive={isActive as 'any' | 'true' | 'false'}
            isPremium={isPremium as 'any' | 'true' | 'false'}
            createdFrom={createdFrom}
            createdTo={createdTo}
            onRoleChange={setRole}
            onIsActiveChange={(v) => setIsActive(v)}
            onIsPremiumChange={(v) => setIsPremium(v)}
            onCreatedFromChange={setCreatedFrom}
            onCreatedToChange={setCreatedTo}
          />
        )}
        <div className="flex items-center gap-2 mt-2">
          <button className="px-3 py-1 rounded border" onClick={doDryRun}>
            Estimate
          </button>
          <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={doStart}>
            Start
          </button>
          {estimate !== null && (
            <span className="text-sm text-gray-600">Estimated recipients: {estimate}</span>
          )}
        </div>
      </div>
    </Modal>
  );
}
