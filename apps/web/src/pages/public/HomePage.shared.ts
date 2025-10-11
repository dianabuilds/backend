export const HOME_DEFAULT_SLUG = 'main';

export function buildHomeCacheKey(slug: string): string {
  return `home:${slug}`;
}
