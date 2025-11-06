import type { ReactElement } from "react";

import type { SitePageBlock, SitePageBlockItem } from "@caves/site-shared/site-page";

import styles from "./BlockRenderer.module.css";

function formatDate(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function renderItems(items: SitePageBlockItem[]): ReactElement | null {
  if (!items.length) {
    return (
      <div className={styles.placeholder}>
        <strong>Нет привязанных элементов.</strong>
        <span>
          Добавьте контент в Site Editor, чтобы блок отображал реальные данные.
        </span>
      </div>
    );
  }

  return (
    <div className={styles.itemsGrid}>
      {items.map((item, index) => (
        <article key={item.id ?? index} className={styles.itemCard}>
          {item.title ? <strong>{item.title}</strong> : null}
          {item.summary ? (
            <p className={styles.itemSummary}>{item.summary}</p>
          ) : null}
          <ul className={styles.itemMeta}>
            {item.slug ? (
              <li>
                <span>Slug</span> · {item.slug}
              </li>
            ) : null}
            {formatDate(item.publishAt) ? (
              <li>
                <span>Publish</span> · {formatDate(item.publishAt)}
              </li>
            ) : null}
            {formatDate(item.updatedAt) ? (
              <li>
                <span>Updated</span> · {formatDate(item.updatedAt)}
              </li>
            ) : null}
          </ul>
        </article>
      ))}
    </div>
  );
}

function buildMetaList(block: SitePageBlock): ReactElement | null {
  const tags: string[] = [];

  if (block.layout && typeof block.layout === "object") {
    const layoutKeys = Object.keys(block.layout);
    if (layoutKeys.length) {
      tags.push(`layout:${layoutKeys.length}`);
    }
  }

  if (block.dataSource && typeof block.dataSource === "object") {
    const sourceType =
      typeof block.dataSource.type === "string"
        ? block.dataSource.type
        : typeof block.dataSource.mode === "string"
          ? block.dataSource.mode
          : null;
    if (sourceType) {
      tags.push(`source:${sourceType}`);
    }
  }

  if (!tags.length) {
    return null;
  }

  return (
    <ul className={styles.tagList}>
      {tags.map((tag, index) => (
        <li key={index} className={styles.tag}>
          {tag}
        </li>
      ))}
    </ul>
  );
}

export function CollectionBlock({
  block,
}: {
  block: SitePageBlock;
  position: number;
}): ReactElement {
  const badge = block.type.toUpperCase();
  const title = block.title ?? `Блок №${block.id}`;
  const subtitle =
    typeof block.slots?.subtitle === "string"
      ? block.slots.subtitle
      : typeof block.slots?.description === "string"
        ? block.slots.description
        : null;

  return (
    <>
      <header className={styles.blockHeader}>
        <span className={styles.blockBadge}>{badge}</span>
        <h2 className={styles.blockTitle}>{title}</h2>
      </header>
      {subtitle ? <p className={styles.blockSubtitle}>{subtitle}</p> : null}
      {buildMetaList(block)}
      {renderItems(block.items)}
    </>
  );
}
