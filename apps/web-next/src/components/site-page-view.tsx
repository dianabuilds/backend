import type { Route } from "next";
import Link from "next/link";

import styles from "./site-page-view.module.css";
import { BlockRenderer } from "@/components/blocks";
import { GlobalHeader } from "@/components/global-header";
import { GlobalBlocksPanel } from "./global-blocks-panel";
import type {
  SiteBlock,
  SiteBlockBinding,
  SiteBlockMap,
} from "@caves/site-shared/site-page";
import { normalizeLocale } from "@/config/i18n";
import {
  buildLocalePath,
  resolveSlugForLocale,
  type SitePageData,
} from "@/lib/site-page-api";

type SitePageViewProps = {
  page: SitePageData;
};

export default function SitePageView({ page }: SitePageViewProps) {
  const requestedLocale = page.requestedLocale ?? undefined;
  const renderedLocaleRaw = page.locale ?? undefined;
  const fallbackLocaleRaw = page.fallbackLocale ?? undefined;

  const activeLocale = normalizeLocale(
    requestedLocale ?? renderedLocaleRaw,
  );
  const fallbackLocale =
    typeof fallbackLocaleRaw === "string"
      ? normalizeLocale(fallbackLocaleRaw)
      : null;
  const dataLocale =
    typeof renderedLocaleRaw === "string"
      ? normalizeLocale(renderedLocaleRaw)
      : activeLocale;

  const availableLocalesSet = new Set(
    (page.availableLocales ?? [])
      .filter(
        (locale): locale is string =>
          typeof locale === "string" && locale.length > 0,
      )
      .map((locale) => normalizeLocale(locale)),
  );

  const localeOptions = Array.from(
    new Set(
      [
        activeLocale,
        ...availableLocalesSet,
        dataLocale,
        fallbackLocale,
      ].filter((locale): locale is string => Boolean(locale)),
    ),
  );

  const localeNav = localeOptions.map((locale) => {
    const localizedSlug = resolveSlugForLocale(
      locale,
      page.slug,
      page.localizedSlugs,
    );
    return {
      locale,
      href: buildLocalePath(locale, localizedSlug) as Route,
      isActive: locale === activeLocale,
      isAvailable:
        availableLocalesSet.size === 0 || availableLocalesSet.has(locale),
      isFallback: Boolean(fallbackLocale && locale === fallbackLocale),
    };
  });

  const activeSlug = resolveSlugForLocale(
    activeLocale,
    page.slug,
    page.localizedSlugs,
  );
  const activePath = buildLocalePath(activeLocale, activeSlug);

  const blocksMap = page.blocksMap ?? {};
  const blockBindings = page.blockBindings ?? [];
  const sharedEntries = buildSharedEntries(blocksMap, blockBindings);
  const effectiveEntries =
    sharedEntries.length > 0
      ? sharedEntries
      : buildSharedEntries(blocksMap, []);
  const headerEntry = pickHeaderEntry(effectiveEntries);
  const headerBlock = headerEntry?.block ?? null;
  const headerLocale =
    headerEntry?.binding?.locale ??
    headerEntry?.block.locale ??
    activeLocale;
  const otherSharedEntries = effectiveEntries.filter(
    (entry) => !headerBlock || entry.block.id !== headerBlock.id,
  );
  const sharedBindings =
    blockBindings.filter(
      (binding) => (binding.scope ?? "shared") === "shared",
    ) ?? [];

  return (
    <main className={styles.container}>
      <header className={styles.header}>
        <p className={styles.slug}>
          path: <span>{activePath}</span>
        </p>
        <p className={styles.slug}>
          slug: <span>{activeSlug || "main"}</span>
        </p>
        <p className={styles.version}>version {page.version}</p>
        {page.updatedAt ? (
          <p className={styles.timestamp}>
            updated {formatTime(page.updatedAt)}
          </p>
        ) : null}
        <p className={styles.version}>source: {page.source}</p>
      </header>
      {localeNav.length > 0 ? (
        <nav className={styles.localeNav} aria-label="Локали страницы">
          <span className={styles.localeNavLabel}>Локали:</span>
          {localeNav.map((item) => {
            const label = item.locale.toUpperCase();
            if (item.isActive) {
              return (
                <span
                  key={item.locale}
                  className={`${styles.localeNavLink} ${styles.localeNavActive}`}
                  aria-current="page"
                >
                  <span className={styles.localeNavText}>{label}</span>
                  {item.isFallback ? (
                    <span className={styles.localeNavBadge}>fallback</span>
                  ) : null}
                  {!item.isAvailable ? (
                    <span className={styles.localeNavBadge}>нет контента</span>
                  ) : null}
                </span>
              );
            }
            return (
              <Link
                key={item.locale}
                href={item.href}
                className={styles.localeNavLink}
              >
                <span className={styles.localeNavText}>{label}</span>
                {item.isFallback ? (
                  <span className={styles.localeNavBadge}>fallback</span>
                ) : null}
                {!item.isAvailable ? (
                  <span className={styles.localeNavBadge}>нет контента</span>
                ) : null}
              </Link>
            );
          })}
        </nav>
      ) : null}

      <section className={styles.metaSection}>
        <dl>
          {page.title ? (
            <>
              <dt>title</dt>
              <dd>{page.title}</dd>
            </>
          ) : null}
          {page.meta?.description ? (
            <>
              <dt>description</dt>
              <dd>{String(page.meta.description)}</dd>
            </>
          ) : null}
        {page.locale ? (
          <>
            <dt>locale</dt>
            <dd>{page.locale}</dd>
          </>
        ) : null}
        {page.requestedLocale ? (
          <>
            <dt>requested locale</dt>
            <dd>{page.requestedLocale}</dd>
          </>
        ) : null}
        {page.fallbackLocale ? (
          <>
            <dt>fallback locale</dt>
            <dd>{page.fallbackLocale}</dd>
          </>
        ) : null}
        {page.availableLocales?.length ? (
          <>
            <dt>available locales</dt>
            <dd>{page.availableLocales.join(", ")}</dd>
          </>
        ) : null}
        {page.localizedSlugs && Object.keys(page.localizedSlugs).length ? (
          <>
            <dt>localized slugs</dt>
            <dd>
              {Object.entries(page.localizedSlugs)
                .map(([locale, slug]) => `${locale}: ${slug}`)
                .join(", ")}
            </dd>
          </>
        ) : null}
        <dt>blocks</dt>
        <dd>{page.blocks.length}</dd>
      </dl>
        <details className={styles.details}>
          <summary>meta payload</summary>
          <pre>{JSON.stringify(page.meta, null, 2)}</pre>
        </details>
      </section>

      {headerBlock ? (
        <GlobalHeader block={headerBlock} locale={headerLocale} />
      ) : null}

      <section className={styles.blocks} aria-live="polite">
        {page.blocks.length > 0 ? (
          page.blocks.map((block, index) => (
            <BlockRenderer
              key={`${block.id}:${index}`}
              block={block}
              position={index + 1}
            />
          ))
        ) : (
          <p className={styles.empty}>Блоки не найдены</p>
        )}
      </section>

      {otherSharedEntries.length > 0 ? (
        <GlobalBlocksPanel entries={otherSharedEntries} />
      ) : null}

      {sharedBindings.length > 0 ? (
        <aside className={styles.references}>
          <h3>Привязки общих блоков</h3>
          <ul>
            {sharedBindings.map((binding, index) => (
              <li
                key={`${binding.key ?? binding.blockId ?? index}:${
                  binding.section ?? "section"
                }`}
              >
                <code>{binding.key ?? binding.blockId ?? "unknown"}</code>
                {binding.section ? <span> → {binding.section}</span> : null}
                <span> · locale: {binding.locale ?? "—"}</span>
                <span> · position: {binding.position}</span>
              </li>
            ))}
          </ul>
        </aside>
      ) : legacyRefs.length > 0 ? (
        <aside className={styles.references}>
          <h3>Использование общих блоков</h3>
          <ul>
            {legacyRefs.map((ref, index) => (
              <li key={`${ref.key}:${ref.section ?? index}`}>
                <code>{ref.key}</code>
                {ref.section ? <span> → {ref.section}</span> : null}
              </li>
            ))}
          </ul>
        </aside>
      ) : null}

      {page.fallbacks.length > 0 ? (
        <aside className={styles.fallbacks}>
          <h3>Использованы fallbacks</h3>
          <pre>{JSON.stringify(page.fallbacks, null, 2)}</pre>
        </aside>
      ) : null}
    </main>
  );
}

function formatTime(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

type SharedBlockEntry = {
  block: SiteBlock;
  binding: SiteBlockBinding | null;
};

const HEADER_PREFERRED_KEYS = [
  "site-global-header",
  "global-header",
  "site-header",
  "header",
];
const HEADER_SECTION_HINTS = ["header", "global_header", "global-header"];

function buildSharedEntries(
  blocks: SiteBlockMap,
  bindings: SiteBlockBinding[],
): SharedBlockEntry[] {
  const entries: SharedBlockEntry[] = [];
  const usedIds = new Set<string>();

  bindings
    .filter((binding) => (binding.scope ?? "shared") === "shared")
    .forEach((binding) => {
      const block = resolveBlockForBinding(binding, blocks);
      if (!block) {
        return;
      }
      entries.push({ block, binding });
      usedIds.add(block.id);
    });

  Object.values(blocks).forEach((block) => {
    if (!block || (block.scope ?? "shared") !== "shared") {
      return;
    }
    if (usedIds.has(block.id)) {
      return;
    }
    entries.push({ block, binding: null });
  });

  return entries;
}

function resolveBlockForBinding(
  binding: SiteBlockBinding,
  blocks: SiteBlockMap,
): SiteBlock | null {
  if (binding.key && blocks[binding.key]) {
    return blocks[binding.key];
  }
  if (binding.blockId) {
    const match = Object.values(blocks).find(
      (block) => block.id === binding.blockId,
    );
    if (match) {
      return match;
    }
  }
  return null;
}

function pickHeaderEntry(entries: SharedBlockEntry[]): SharedBlockEntry | null {
  if (entries.length === 0) {
    return null;
  }
  const byBindingSection = entries.find((entry) => {
    const section = entry.binding?.section?.toLowerCase();
    if (!section) {
      return false;
    }
    return HEADER_SECTION_HINTS.some((hint) => section.includes(hint));
  });
  if (byBindingSection) {
    return byBindingSection;
  }

  const byPreferredKey = entries.find((entry) => {
    const key = entry.block.key?.toLowerCase();
    return key ? HEADER_PREFERRED_KEYS.includes(key) : false;
  });
  if (byPreferredKey) {
    return byPreferredKey;
  }

  const byBlockSection = entries.find((entry) =>
    entry.block.sections?.some((section) =>
      HEADER_SECTION_HINTS.some((hint) => section.toLowerCase().includes(hint)),
    ),
  );
  if (byBlockSection) {
    return byBlockSection;
  }

  return entries[0] ?? null;
}
