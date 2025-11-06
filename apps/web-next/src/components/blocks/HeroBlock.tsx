import Image from "next/image";
import type { ReactElement } from "react";

import type { SitePageBlock } from "@caves/site-shared/site-page";

import styles from "./BlockRenderer.module.css";

type HeroSlots = {
  headline?: string;
  subheadline?: string;
  cta?: { label?: string; href?: string | null } | null;
  media?: string | null;
};

function resolveSlots(slots: SitePageBlock["slots"]): HeroSlots {
  if (!slots || typeof slots !== "object") {
    return {};
  }
  const result: HeroSlots = {};
  if (typeof slots.headline === "string") result.headline = slots.headline;
  if (typeof slots.subheadline === "string") result.subheadline = slots.subheadline;
  if (typeof slots.media === "string") result.media = slots.media;
  if (
    slots.cta &&
    typeof slots.cta === "object" &&
    slots.cta !== null &&
    typeof (slots.cta as { label?: unknown }).label === "string"
  ) {
    const cta = slots.cta as HeroSlots["cta"];
    result.cta = {
      label: typeof cta?.label === "string" ? cta.label : undefined,
      href:
        typeof cta?.href === "string" && cta.href.trim().length > 0
          ? cta.href
          : null,
    };
  }
  return result;
}

export function HeroBlock({
  block,
  position,
}: {
  block: SitePageBlock;
  position: number;
}): ReactElement {
  const { headline, subheadline, cta, media } = resolveSlots(block.slots);
  const title = headline?.trim().length ? headline : block.title ?? "Hero";
  const description =
    subheadline && subheadline.trim().length ? subheadline : null;

  const primaryBadge = block.type.toUpperCase();
  const isPrimaryHero = position === 1;

  return (
    <>
      <header className={styles.blockHeader}>
        <span className={styles.blockBadge}>{primaryBadge}</span>
        <h2 className={styles.blockTitle}>{title}</h2>
      </header>
      {description ? (
        <p className={styles.blockSubtitle}>{description}</p>
      ) : null}
      <div className={styles.hero}>
        <div className={styles.heroContent}>
          {description ? null : (
            <p className={styles.heroSubheadline}>
              Создайте описание в Site Editor&apos;e, чтобы рассказать о блоке
              подробнее.
            </p>
          )}
          {cta && cta.label && cta.href ? (
            <a
              className={styles.heroCta}
              href={cta.href}
              rel="noreferrer"
              target={cta.href.startsWith("http") ? "_blank" : "_self"}
            >
              {cta.label}
            </a>
          ) : null}
        </div>
        {media ? (
          <div className={styles.heroMedia}>
            <Image
              src={media}
              alt={title}
              width={720}
              height={540}
              loading={isPrimaryHero ? "eager" : "lazy"}
              decoding="async"
              className={styles.heroImage}
            />
          </div>
        ) : null}
      </div>
    </>
  );
}
