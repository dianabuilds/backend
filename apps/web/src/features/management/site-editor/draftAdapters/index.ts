import { homeDraftAdapter } from './homeDraftAdapter';
import type { SiteDraftAdapter } from './types';

export function resolveDraftAdapter(): SiteDraftAdapter {
  // Пока доступен только home-адаптер; далее можно расширить выбор по типу страницы.
  return homeDraftAdapter;
}

export { type SiteDraftAdapter } from './types';
