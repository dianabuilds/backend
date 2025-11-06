export {
  normalizeSitePageResponse,
  type SitePageBlock,
  type SitePageBlockItem,
  type SitePageResponse,
  type SiteBlock,
  type SiteBlockBinding,
  type SiteBlockMap,
  type SiteBlockRef,
} from "@caves/site-shared/site-page";

export type SitePageLocaleEntry = {
  locale: string;
  slug: string;
  status: "draft" | "published" | "missing";
  title?: string | null;
  description?: string | null;
};

export type SitePageLocalizedMeta = Record<string, Record<string, unknown>>;
