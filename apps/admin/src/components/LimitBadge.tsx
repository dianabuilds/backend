import { useEffect, useState } from 'react';

import { ensureFetched, getLimitState, subscribe } from './LimitBadgeController';

interface Props {
  limitKey: string;
}

// Helpers exported from controller: import directly where needed

export default function LimitBadge({ limitKey }: Props) {
  const initial = getLimitState(limitKey);
  const [value, setValue] = useState<number | null>(initial.value);
  const [msg, setMsg] = useState<string | undefined>(initial.message);

  useEffect(() => {
    const listener = () => {
      const s = getLimitState(limitKey);
      setValue(s.value);
      setMsg(s.message);
    };
    const unsubscribe = subscribe(listener);
    void ensureFetched(limitKey);
    return () => unsubscribe();
  }, [limitKey]);

  const title = msg || undefined;
  const cls = msg ? 'bg-red-200 text-red-800' : 'bg-gray-200 text-gray-800';

  return (
    <span
      className={`ml-2 px-2 py-0.5 rounded text-xs ${cls}`}
      title={title}
      data-testid={`limit-${limitKey}`}
    >
      {value ?? '-'}
    </span>
  );
}
