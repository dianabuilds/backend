import { useEffect, useState } from 'react';

import type { FeatureFlag } from '../api/flags';
import { Modal } from '../shared/ui';

interface Props {
  flag: FeatureFlag | null;
  onClose: () => void;
  onSave: (
    key: string,
    patch: {
      description: string;
      value: boolean;
      audience: FeatureFlag['audience'];
    },
  ) => Promise<void>;
}

export default function FlagEditModal({ flag, onClose, onSave }: Props) {
  const [description, setDescription] = useState('');
  const [value, setValue] = useState(false);
  const [audience, setAudience] = useState<FeatureFlag['audience']>('all' as FeatureFlag['audience']);

  useEffect(() => {
    if (flag) {
      setDescription(flag.description || '');
      setValue(!!flag.value);
      setAudience(flag.audience);
    }
  }, [flag]);

  if (!flag) return null;

  return (
    <Modal isOpen={!!flag} onClose={onClose} title={`Edit ${flag.key}`}>
      <div className="space-y-4">
        <label className="block text-sm">
          Description
          <input
            className="mt-1 w-full px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={value} onChange={(e) => setValue(e.target.checked)} />
          <span>Enabled</span>
        </label>
        <label className="block text-sm">
          Audience
          <select
            className="mt-1 w-full px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
            value={audience}
            onChange={(e) => setAudience(e.target.value as FeatureFlag['audience'])}
          >
            <option value="all">all</option>
            <option value="premium">premium</option>
            <option value="beta">beta</option>
          </select>
        </label>
        <div className="flex justify-end gap-2 pt-2">
          <button className="px-3 py-1 rounded border" onClick={onClose}>
            Cancel
          </button>
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white"
            onClick={() => onSave(flag.key, { description, value, audience })}
          >
            Save
          </button>
        </div>
      </div>
    </Modal>
  );
}
