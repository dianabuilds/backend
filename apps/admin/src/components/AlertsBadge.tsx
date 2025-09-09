import { useQuery } from '@tanstack/react-query';
import { AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

import { getAlerts } from '../api/alerts';

export default function AlertsBadge() {
  const { data } = useQuery({
    queryKey: ['alerts'],
    queryFn: getAlerts,
    refetchInterval: 15000,
  });

  const count = data?.length ?? 0;

  return (
    <Link to="/ops/alerts" className="relative inline-block" aria-label="Alerts">
      <AlertTriangle className="w-5 h-5 text-gray-700 dark:text-gray-200" />
      {count > 0 && (
        <span
          data-testid="alerts-badge"
          className={
            'absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full w-5 h-5 flex items-center ' +
            'justify-center'
          }
        >
          {count}
        </span>
      )}
    </Link>
  );
}
