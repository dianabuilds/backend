export function buildDevBlogPostKey(slug: string | undefined): string | null {
  if (!slug) return null;
  return `dev-blog:post:${slug}`;
}
