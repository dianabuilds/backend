import { isPreviewEnv } from '../utils/env';

export default function EnvBanner() {
  if (!isPreviewEnv) return null;
  return (
    <div
      className="mb-4 p-2 bg-yellow-200 text-yellow-900 text-center text-sm rounded"
      role="alert"
    >
      PREVIEW DATA — NOT PROD
    </div>
  );
}
