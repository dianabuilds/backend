import type { SiteBlock } from '@shared/types/management';
import type { HomeBlock, HomeBlockType } from './types';
import { generateBlockId } from './blockDefinitions';

const SECTION_TO_BLOCK_TYPE: Record<string, HomeBlockType> = {
  hero: 'hero',
  dev_blog_list: 'dev_blog_list',
  dev_blog: 'dev_blog_list',
  quests_carousel: 'quests_carousel',
  nodes_carousel: 'nodes_carousel',
  popular_carousel: 'popular_carousel',
  editorial_picks: 'editorial_picks',
  recommendations: 'recommendations',
  custom_carousel: 'custom_carousel',
};

function normalizeLocaleCode(value?: string | null): string | null {
  if (!value) {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length ? trimmed.toLowerCase() : null;
}

export function mapSiteBlockSectionToHomeType(section?: string | null): HomeBlockType | null {
  if (!section) {
    return null;
  }
  const normalized = section.trim().toLowerCase();
  return SECTION_TO_BLOCK_TYPE[normalized] ?? null;
}

export function createBlockFromSiteBlock({
  siteBlock,
  existingBlocks,
  preferredLocale,
}: {
  siteBlock: SiteBlock;
  existingBlocks: HomeBlock[];
  preferredLocale?: string | null;
}): HomeBlock | null {
  const blockType = mapSiteBlockSectionToHomeType(siteBlock.section);
  if (!blockType) {
    return null;
  }

  const blockId = generateBlockId(blockType, existingBlocks);
  const availableLocales = Array.isArray(siteBlock.available_locales)
    ? siteBlock.available_locales
        .map(normalizeLocaleCode)
        .filter((locale): locale is string => Boolean(locale && locale.length))
    : [];
  const normalizedPreferred = normalizeLocaleCode(preferredLocale);
  const defaultLocale = normalizeLocaleCode(siteBlock.default_locale) ?? normalizeLocaleCode(siteBlock.locale);
  const resolvedLocale =
    (normalizedPreferred && availableLocales.includes(normalizedPreferred) && normalizedPreferred) ||
    defaultLocale ||
    availableLocales[0] ||
    normalizedPreferred ||
    null;
  const hasDraft =
    typeof siteBlock.draft_version === 'number' &&
    (siteBlock.published_version == null || siteBlock.draft_version > siteBlock.published_version);

  return {
    id: blockId,
    type: blockType,
    title: siteBlock.title ?? siteBlock.key ?? blockType,
    enabled: true,
    source: 'site',
    siteBlockId: siteBlock.id,
    siteBlockKey: siteBlock.key,
    siteBlockTitle: siteBlock.title ?? null,
    siteBlockSection: siteBlock.section ?? blockType,
    siteBlockLocale: resolvedLocale,
    siteBlockStatus: siteBlock.status ?? null,
    siteBlockReviewStatus: siteBlock.review_status ?? null,
    siteBlockRequiresPublisher: siteBlock.requires_publisher ?? null,
    siteBlockHasPendingPublish: siteBlock.has_pending_publish ?? null,
    siteBlockHasDraft: hasDraft ? true : null,
    siteBlockUpdatedAt: siteBlock.updated_at ?? null,
    siteBlockUpdatedBy: siteBlock.updated_by ?? null,
  };
}

