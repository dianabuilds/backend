import type {
  NormalizeSitePageOptions,
  SiteBlock,
  SiteBlockBinding,
  SiteBlockMap,
  SiteBlockRef,
  SiteBlockReviewStatus,
  SiteBlockScope,
  SiteBlockStatus,
  SitePageBlock,
  SitePageBlockItem,
  SitePageFallbackEntry,
  SitePageResponse,
} from "./types";

type AnyRecord = Record<string, unknown>;

const DEFAULT_LOCALE = "ru";

export function normalizeSitePageResponse(
  source: unknown,
  options: NormalizeSitePageOptions = {},
): SitePageResponse {
  const root = pickRoot(source);
  const fallbackSlug = options.fallbackSlug ?? "main";

  const pageId = stringOrNull(
    root.page_id ??
      root.pageId ??
      root.id ??
      (isRecord(source) ? source.page_id ?? source.pageId ?? source.id : null),
  );

  const slug =
    stringOrNull(root.slug) ??
    stringOrNull((isRecord(source) ? source.slug : null)) ??
    fallbackSlug;

  const locale =
    stringOrNull(root.locale) ??
    stringOrNull(isRecord(source) ? source.locale : null);
  const requestedLocale =
    stringOrNull(root.requested_locale ?? root.requestedLocale) ??
    stringOrNull(
      isRecord(source)
        ? source.requested_locale ?? source.requestedLocale
        : null,
    );
  const fallbackLocale =
    stringOrNull(root.fallback_locale ?? root.fallbackLocale) ??
    stringOrNull(
      isRecord(source)
        ? source.fallback_locale ?? source.fallbackLocale
        : null,
    );

  const availableLocales = uniqueStrings(
    root.available_locales ??
      root.availableLocales ??
      (isRecord(source) ? source.available_locales ?? source.availableLocales : []),
  );

  const localizedSlugsRecord = recordOf(
    root.localized_slugs ??
      root.localizedSlugs ??
      (isRecord(source)
        ? source.localized_slugs ?? source.localizedSlugs
        : null),
  );
  const localizedSlugs = Object.fromEntries(
    Object.entries(localizedSlugsRecord).map(([key, value]) => [
      key,
      stringOrNull(value) ?? slug,
    ]),
  );

  const title = stringOrNull(root.title);
  const type = stringOrNull(root.type);
  const version = numberOrNull(root.version) ?? 0;
  const sourceName = stringOrNull(root.source ?? (isRecord(source) ? source.source : null));

  const publishedAt =
    stringOrNull(root.published_at ?? root.publishedAt) ??
    stringOrNull(
      isRecord(source) ? source.published_at ?? source.publishedAt : null,
    );
  const publishedBy =
    stringOrNull(root.published_by ?? root.publishedBy) ??
    stringOrNull(
      isRecord(source) ? source.published_by ?? source.publishedBy : null,
    );
  const updatedAt =
    stringOrNull(root.updated_at ?? root.updatedAt) ??
    stringOrNull(
      isRecord(source) ? source.updated_at ?? source.updatedAt : null,
    );
  const generatedAt =
    stringOrNull(root.generated_at ?? root.generatedAt) ??
    stringOrNull(
      isRecord(source) ? source.generated_at ?? source.generatedAt : null,
    );

  const blocks = normalizeBlocks(root.blocks ?? (isRecord(source) ? source.blocks : null));
  const fallbacks = normalizeFallbacks(
    root.fallbacks ?? (isRecord(source) ? source.fallbacks : null),
  );
  const rawBlocksMap =
    root.blocks_map ??
    root.blocksMap ??
    root.block_map ??
    (isRecord(source)
      ? source.blocks_map ?? source.blocksMap ?? source.block_map
      : null);

  const blocksMap = normalizeBlockMap(rawBlocksMap);

  const rawBlockRefs =
    root.block_refs ??
    root.blockRefs ??
    (isRecord(source) ? source.block_refs ?? source.blockRefs : null);
  const blockRefs = normalizeBlockRefs(rawBlockRefs);

  const rawBlockBindings =
    root.block_bindings ??
    root.blockBindings ??
    (isRecord(source) ? source.block_bindings ?? source.blockBindings : null);
  const blockBindings = normalizeBlockBindings(rawBlockBindings);

  const meta = recordOf(root.meta ?? (isRecord(source) ? source.meta : null));
  const payload = recordOf(
    root.payload ?? (isRecord(source) ? source.payload : null),
  );

  const response: SitePageResponse = {
    pageId,
    slug,
    locale,
    requestedLocale,
    fallbackLocale,
    availableLocales,
    localizedSlugs,
    title,
    type,
    source: sourceName,
    version,
    publishedAt,
    publishedBy,
    updatedAt,
    generatedAt,
    meta,
    payload,
    blocks,
    fallbacks,
    blocksMap,
    blockRefs,
    blockBindings,
  };

  return response;
}

function normalizeBlocks(value: unknown): SitePageBlock[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const result: SitePageBlock[] = [];
  value.forEach((entry, index) => {
    if (!isRecord(entry)) {
      return;
    }
    const id = stringOrNull(entry.id ?? entry.block_id) ?? `block-${index + 1}`;
    const type = stringOrNull(entry.type) ?? "unknown";
    const enabled = booleanValue(entry.enabled, true);
    result.push({
      id,
      type,
      enabled,
      title: stringOrNull(entry.title),
      subtitle: stringOrNull(entry.subtitle ?? entry.description),
      section: stringOrNull(entry.section ?? entry.zone),
      source: stringOrNull(entry.source),
      layout: recordOrNull(entry.layout),
      slots: recordOrNull(entry.slots),
      dataSource: recordOrNull(entry.data_source ?? entry.dataSource),
      data: recordOrNull(entry.data),
      meta: recordOrNull(entry.meta),
      items: normalizeBlockItems(entry.items),
      extras: extrasOrNull(entry.extras),
    });
  });
  return result;
}

function normalizeBlockItems(value: unknown): SitePageBlockItem[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const items: SitePageBlockItem[] = [];
  value.forEach((entry, index) => {
    if (!isRecord(entry)) {
      return;
    }
    const id =
      stringOrNull(entry.id ?? entry.slug ?? entry.key) ??
      `item-${index + 1}`;
    items.push({
      id,
      title: stringOrNull(entry.title),
      summary: stringOrNull(entry.summary ?? entry.description),
      slug: stringOrNull(entry.slug),
      href: stringOrNull(entry.href ?? entry.url),
      publishAt: stringOrNull(entry.publish_at ?? entry.publishAt),
      updatedAt: stringOrNull(entry.updated_at ?? entry.updatedAt),
      coverUrl: stringOrNull(entry.cover_url ?? entry.coverUrl ?? entry.image),
      provider: stringOrNull(entry.provider),
      data: recordOrNull(entry.data),
      extras: extrasOrNull(entry.extras),
    });
  });
  return items;
}

function normalizeFallbacks(value: unknown): SitePageFallbackEntry[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const entries: SitePageFallbackEntry[] = [];
  value.forEach((entry) => {
    const record = recordOrNull(entry);
    if (record) {
      entries.push(record);
    }
  });
  return entries;
}

function normalizeBlockMap(value: unknown): SiteBlockMap {
  if (!isRecord(value)) {
    return {};
  }
  const result: SiteBlockMap = {};
  for (const [key, raw] of Object.entries(value)) {
    if (!isRecord(raw)) {
      continue;
    }
    const id = stringOrNull(raw.id ?? raw.block_id) ?? key;
    const title = stringOrNull(raw.title);
    const section = stringOrNull(raw.section) ?? "general";
    const scope = normalizeScope(raw.scope);
    const defaultLocale =
      stringOrNull(raw.default_locale ?? raw.defaultLocale) ?? DEFAULT_LOCALE;
    const availableLocales = uniqueStrings(
      raw.available_locales ?? raw.availableLocales,
    );
    const status = normalizeStatus(raw.status);
    const reviewStatus = normalizeReviewStatus(raw.review_status ?? raw.reviewStatus);
    const requiresPublisher = booleanValue(
      raw.requires_publisher ?? raw.requiresPublisher,
      false,
    );
    const publishedVersion = numberOrNull(
      raw.published_version ?? raw.publishedVersion,
    );
    const draftVersion = numberOrNull(raw.draft_version ?? raw.draftVersion);
    const updatedAt = stringOrNull(raw.updated_at ?? raw.updatedAt);
    const updatedBy = stringOrNull(raw.updated_by ?? raw.updatedBy);
    const publishedAt = stringOrNull(raw.published_at ?? raw.publishedAt);
    const comment = stringOrNull(raw.comment);
    const sections = uniqueStrings(raw.sections ?? raw.section ?? [section]);
    const hasPendingPublish =
      booleanValue(raw.has_pending_publish ?? raw.hasPendingPublish) ??
      (draftVersion ?? 0) > (publishedVersion ?? 0);
    const locale = stringOrNull(raw.locale);
    result[key] = {
      id,
      key,
      title,
      section,
      scope,
      defaultLocale,
      availableLocales:
        availableLocales.length > 0 ? availableLocales : [defaultLocale],
      locale,
      status,
      reviewStatus,
      requiresPublisher,
      publishedVersion,
      draftVersion,
      version: draftVersion ?? publishedVersion ?? 0,
      comment,
      data: recordOf(raw.data),
      meta: recordOf(raw.meta),
      updatedAt,
      updatedBy,
      publishedAt,
      hasPendingPublish: Boolean(hasPendingPublish),
      sections: sections.length > 0 ? sections : [section],
      extras: extrasOrNull(raw.extras),
    };
  }
  return result;
}

function normalizeBlockRefs(value: unknown): SiteBlockRef[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const refs: SiteBlockRef[] = [];
  value.forEach((entry) => {
    if (!isRecord(entry)) {
      return;
    }
    const key = stringOrNull(entry.key ?? entry.reference);
    if (!key) {
      return;
    }
    refs.push({
      blockId: stringOrNull(entry.block_id ?? entry.blockId),
      key,
      section: stringOrNull(entry.section),
      scope: stringOrNull(entry.scope) ?? null,
    });
  });
  return refs;
}

function normalizeBlockBindings(value: unknown): SiteBlockBinding[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const bindings: SiteBlockBinding[] = [];
  value.forEach((entry) => {
    if (!isRecord(entry)) {
      return;
    }
    const blockId = stringOrNull(entry.block_id ?? entry.blockId);
    const pageId = stringOrNull(entry.page_id ?? entry.pageId);
    if (!blockId || !pageId) {
      return;
    }
    const locale = stringOrNull(entry.locale) ?? DEFAULT_LOCALE;
    const availableLocaleList = uniqueStrings(
      entry.available_locales ?? entry.availableLocales,
    );

    bindings.push({
      blockId,
      pageId,
      key: stringOrNull(entry.key),
      title: stringOrNull(entry.title),
      section: stringOrNull(entry.section),
      locale,
      defaultLocale: stringOrNull(entry.default_locale ?? entry.defaultLocale),
      availableLocales:
        availableLocaleList.length > 0 ? availableLocaleList : null,
      position: numberOrNull(entry.position) ?? 0,
      active: booleanValue(entry.active, true),
      hasDraft: booleanValue(entry.has_draft ?? entry.hasDraft, false),
      lastPublishedAt: stringOrNull(
        entry.last_published_at ?? entry.lastPublishedAt,
      ),
      updatedAt: stringOrNull(entry.updated_at ?? entry.updatedAt),
      updatedBy: stringOrNull(entry.updated_by ?? entry.updatedBy),
      requiresPublisher: booleanValue(
        entry.requires_publisher ?? entry.requiresPublisher,
        false,
      ),
      status: normalizeStatus(entry.status),
      reviewStatus: normalizeReviewStatus(entry.review_status ?? entry.reviewStatus),
      scope: stringOrNull(entry.scope) ?? null,
      extras: extrasOrNull(entry.extras),
    });
  });
  return bindings;
}

function pickRoot(value: unknown): AnyRecord {
  if (!isRecord(value)) {
    return {};
  }
  if (isRecord(value.page)) {
    return value.page;
  }
  return value;
}

function isRecord(value: unknown): value is AnyRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringOrNull(value: unknown): string | null {
  if (value == null) {
    return null;
  }
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return null;
}

function numberOrNull(value: unknown): number | null {
  if (value == null) {
    return null;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string") {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  }
  return null;
}

function booleanValue(value: unknown, fallback = false): boolean {
  if (value == null) {
    return fallback;
  }
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes"].includes(normalized)) {
      return true;
    }
    if (["false", "0", "no"].includes(normalized)) {
      return false;
    }
  }
  if (typeof value === "number") {
    return value !== 0;
  }
  return fallback;
}

function recordOf(value: unknown): Record<string, unknown> {
  if (isRecord(value)) {
    return { ...value };
  }
  return {};
}

function recordOrNull(value: unknown): Record<string, unknown> | null {
  if (isRecord(value)) {
    return { ...value };
  }
  return null;
}

function extrasOrNull(value: unknown): Record<string, unknown> | null {
  const record = recordOrNull(value);
  if (!record || Object.keys(record).length === 0) {
    return null;
  }
  return record;
}

function uniqueStrings(value: unknown): string[] {
  const result = new Set<string>();
  if (Array.isArray(value)) {
    value.forEach((entry) => {
      const normalized = stringOrNull(entry);
      if (normalized) {
        result.add(normalized);
      }
    });
  } else if (typeof value === "string") {
    const normalized = value
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean);
    normalized.forEach((part) => result.add(part));
  }
  return Array.from(result);
}

function normalizeStatus(value: unknown): SiteBlockStatus {
  const text = stringOrNull(value) ?? "draft";
  if (text === "published" || text === "archived") {
    return text;
  }
  return "draft";
}

function normalizeReviewStatus(value: unknown): SiteBlockReviewStatus {
  const text = stringOrNull(value) ?? "none";
  if (
    text === "pending" ||
    text === "approved" ||
    text === "rejected" ||
    text === "none"
  ) {
    return text;
  }
  return "none";
}

function normalizeScope(value: unknown): SiteBlockScope {
  const text = stringOrNull(value);
  if (text === "page" || text === "shared") {
    return text;
  }
  return "shared";
}
