import { useQuery } from '@tanstack/react-query';

import { listNotifications, type NotificationItem } from '../../api/notifications';

export default function ActiveBanner() {
  const { data } = useQuery({
    queryKey: ['active-banner'],
    queryFn: () => listNotifications('banner'),
    refetchInterval: 30000,
  });

  const banner: NotificationItem | undefined = data?.[0];
  if (!banner) return null;

  return (
    <div className="mb-4 rounded bg-yellow-100 p-4 text-center">
      <p className="font-semibold">{banner.title}</p>
      <p>{banner.message}</p>
    </div>
  );
}
