import type { ReactElement } from "react";

import type { SiteBlock } from "@caves/site-shared/site-page";
import { isRecord, mergeLocalizedRecord } from "@/lib/localized-record";

import styles from "./global-header.module.css";

type Branding = {
  title: string;
  subtitle: string | null;
  href: string;
  logoText: string;
};

type NavLink = {
  id: string;
  label: string;
  href: string;
  description: string | null;
};

export function GlobalHeader({
  block,
  locale,
}: {
  block: SiteBlock | null;
  locale: string;
}): ReactElement | null {
  if (!block) {
    return null;
  }
  const payload = resolveHeaderPayload(block, locale);
  const headerData = extractHeaderData(block, payload);
  if (!headerData) {
    return null;
  }

  return (
    <section className={styles.wrapper} aria-label="Global header preview">
      <div className={styles.branding}>
        <span className={styles.logo}>{headerData.branding.logoText}</span>
        <div className={styles.titles}>
          <h3 className={styles.title}>{headerData.branding.title}</h3>
          {headerData.branding.subtitle ? (
            <p className={styles.subtitle}>{headerData.branding.subtitle}</p>
          ) : null}
        </div>
      </div>
      <nav className={styles.nav} aria-label="Primary navigation">
        {headerData.primary.map((link) => (
          <a key={link.id} href={link.href}>
            {link.label}
          </a>
        ))}
        {headerData.cta ? (
          <a
            className={styles.cta}
            href={headerData.cta.href}
            target={
              headerData.cta.href.startsWith("http") ? "_blank" : "_self"
            }
            rel="noreferrer"
          >
            {headerData.cta.label}
          </a>
        ) : null}
      </nav>
      <div className={styles.secondary}>
        <span>Ветка: v{block.version}</span>
        <span>· Локаль: {locale}</span>
        {block.locale && block.locale !== locale ? (
          <span>· Данные блока: {block.locale}</span>
        ) : null}
        {block.publishedAt ? (
          <span>· Обновлено: {formatDate(block.publishedAt)}</span>
        ) : null}
      </div>
    </section>
  );
}

type HeaderData = {
  branding: Branding;
  primary: NavLink[];
  cta: NavLink | null;
};

function resolveHeaderPayload(
  block: SiteBlock,
  locale: string,
): Record<string, unknown> {
  return mergeLocalizedRecord(block.data, locale, block.locale) ?? {};
}

function extractHeaderData(
  block: SiteBlock,
  payload: Record<string, unknown>,
): HeaderData | null {
  const branding = resolveBranding(payload.branding, block);
  const navigation = isRecord(payload.navigation) ? payload.navigation : null;
  const primary = resolveNavLinks(navigation?.primary);
  const cta = resolveCta(navigation);

  if (!primary.length && !cta) {
    return null;
  }

  return {
    branding,
    primary,
    cta,
  };
}

function ensureString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function resolveBranding(data: unknown, fallback: SiteBlock): Branding {
  if (isRecord(data)) {
    const title =
      ensureString(data.title).trim() ||
      fallback.title ||
      fallback.key ||
      "Brand";
    const subtitle = ensureString(data.subtitle, "").trim() || null;
    const href = ensureString(data.href, "/") || "/";
    let logoText = title.charAt(0).toUpperCase();

    if (isRecord(data.logo) && typeof data.logo.alt === "string") {
      const alt = data.logo.alt.trim();
      if (alt) {
        logoText = alt.charAt(0).toUpperCase();
      }
    }

    return {
      title,
      subtitle,
      href,
      logoText,
    };
  }

  const title = fallback.title ?? "Brand";
  return {
    title,
    subtitle: null,
    href: "/",
    logoText: title.charAt(0).toUpperCase(),
  };
}

function resolveNavLinks(group: unknown): NavLink[] {
  if (!Array.isArray(group)) {
    return [];
  }

  return group
    .map((entry) => {
      if (!isRecord(entry)) {
        return null;
      }
      const id = ensureString(entry.id) || ensureString(entry.label) || "";
      const label = ensureString(entry.label);
      const href = ensureString(entry.href, "#");
      if (!label) {
        return null;
      }
      return {
        id: id || label,
        label,
        href,
        description:
          typeof entry.description === "string" && entry.description.trim()
            ? entry.description
            : null,
      };
    })
    .filter((link): link is NavLink => Boolean(link));
}

function resolveCta(nav: unknown): NavLink | null {
  if (!isRecord(nav)) {
    return null;
  }
  const cta = nav.cta;
  if (!isRecord(cta)) {
    return null;
  }
  const label = ensureString(cta.label);
  const href = ensureString(cta.href, "#");
  if (!label) {
    return null;
  }
  return {
    id: ensureString(cta.id, label),
    label,
    href,
    description: null,
  };
}

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
