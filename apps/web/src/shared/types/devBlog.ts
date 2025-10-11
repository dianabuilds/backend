export type DevBlogAuthor = {
  id: string | null;
  name?: string | null;
};

export type DevBlogSummary = {
  id: number | string | null;
  slug: string;
  title: string | null;
  summary: string | null;
  coverUrl: string | null;
  publishAt: string | null;
  updatedAt: string | null;
  author: DevBlogAuthor | null;
  tags?: string[] | null;
};

export type DevBlogListResponse = {
  items: DevBlogSummary[];
  total: number;
  hasNext: boolean;
  availableTags?: string[];
  dateRange?: { start: string | null; end: string | null } | null;
  appliedTags?: string[] | null;
};

export type DevBlogDetail = DevBlogSummary & {
  content: string | null;
  status?: string | null;
  isPublic?: boolean | null;
  tags?: string[] | null;
};

export type DevBlogDetailResponse = {
  post: DevBlogDetail;
  prev: DevBlogSummary | null;
  next: DevBlogSummary | null;
};

export type DevBlogListParams = {
  page?: number;
  limit?: number;
  tags?: string[];
  publishedFrom?: string | null;
  publishedTo?: string | null;
};
