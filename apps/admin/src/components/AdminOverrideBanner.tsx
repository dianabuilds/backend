import { useWarningBannerStore } from '../shared/hooks';

export default function AdminOverrideBanner() {
  const banner = useWarningBannerStore();
  if (!banner) return null;
  return (
    <div
      className="mb-4 p-2 bg-yellow-200 text-yellow-900 text-center text-sm rounded"
      role="alert"
    >
      {banner}
    </div>
  );
}
