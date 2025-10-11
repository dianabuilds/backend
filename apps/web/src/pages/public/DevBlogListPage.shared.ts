export type DevBlogListKeyFilters = {
  tags: string[];
  from?: string | undefined;
  to?: string | undefined;
};

export const DEV_BLOG_PAGE_SIZE = 12;

export function buildDevBlogListKey(page: number, filters: DevBlogListKeyFilters = { tags: [], from: undefined, to: undefined }): string {
  const sortedTags = [...filters.tags].sort().join(',');
  const from = filters.from ?? '';
  const to = filters.to ?? '';
  return `dev-blog:list:page:${page}:tags:${sortedTags}:from:${from}:to:${to}`;
}
