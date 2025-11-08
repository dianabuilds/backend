export type HeroBlockCtaStyle = 'primary' | 'secondary' | 'link';

export type HeroBlockCta = {
  label: string;
  href: string;
  style: HeroBlockCtaStyle;
};

export type HeroBlockMedia = {
  url: string;
  alt?: string | null;
};

export type HeroBlockLocaleContent = {
  headline: string;
  subheadline?: string;
  tagline?: string;
  primaryCta: HeroBlockCta;
  secondaryCta: HeroBlockCta | null;
  media: HeroBlockMedia | null;
  highlights: string[];
};

export type HeroBlockLayout = {
  variant: 'split' | 'stacked';
  theme: 'light' | 'dark';
  alignment: 'left' | 'center';
};

export type HeroBlockConfig = {
  layout: HeroBlockLayout;
  locales: Record<string, HeroBlockLocaleContent>;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

const DEFAULT_LAYOUT: HeroBlockLayout = {
  variant: 'split',
  theme: 'light',
  alignment: 'left',
};

export function createDefaultHeroLocale(): HeroBlockLocaleContent {
  return {
    headline: '',
    subheadline: '',
    tagline: '',
    primaryCta: {
      label: '',
      href: '',
      style: 'primary',
    },
    secondaryCta: null,
    media: null,
    highlights: [],
  };
}

export function createDefaultHeroConfig(locale: string = 'ru'): HeroBlockConfig {
  return {
    layout: DEFAULT_LAYOUT,
    locales: {
      [locale]: createDefaultHeroLocale(),
    },
  };
}

function pickString(value: unknown): string | undefined {
  if (typeof value === 'string') {
    return value.trim();
  }
  return undefined;
}

function normalizeCta(value: unknown, fallbackStyle: HeroBlockCtaStyle = 'primary'): HeroBlockCta {
  if (isRecord(value)) {
    const label = pickString(value.label) ?? '';
    const href = pickString(value.href) ?? '';
    const style: HeroBlockCtaStyle =
      value.style === 'secondary' || value.style === 'link' ? value.style : 'primary';
    return { label, href, style };
  }
  return { label: '', href: '', style: fallbackStyle };
}

function normalizeMedia(value: unknown): HeroBlockMedia | null {
  if (!isRecord(value)) {
    return null;
  }
  const url =
    pickString(value.url) ??
    pickString(value.src) ??
    pickString(value.image) ??
    pickString(value.path);
  if (!url) {
    return null;
  }
  const alt = pickString(value.alt) ?? pickString(value.description) ?? null;
  return { url, alt };
}

function normalizeHighlights(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => pickString(item))
    .filter((item): item is string => Boolean(item && item.length));
}

function normalizeLocaleContent(value: unknown): HeroBlockLocaleContent {
  if (isRecord(value) && isRecord(value.content)) {
    return normalizeLocaleContent(value.content);
  }

  // Legacy format: { items: [{ title, subtitle, href }, ... ] }
  if (isRecord(value) && Array.isArray(value.items)) {
    const [first, second] = value.items;
    const headline = pickString(first?.title) ?? 'Hero блок';
    const subheadline = pickString(first?.subtitle) ?? '';
    const primaryCta: HeroBlockCta = {
      label: pickString(second?.title) ?? 'Подробнее',
      href: pickString(second?.href) ?? '/',
      style: 'primary',
    };
    return {
      headline,
      subheadline,
      tagline: pickString(value.title) ?? '',
      primaryCta,
      secondaryCta: null,
      media: null,
      highlights: [],
    };
  }

  if (!isRecord(value)) {
    return createDefaultHeroLocale();
  }

  const headline = pickString(value.headline) ?? '';
  const subheadline = pickString(value.subheadline) ?? '';
  const tagline = pickString(value.tagline) ?? pickString(value.label) ?? '';
  const primaryCta = normalizeCta(value.primaryCta, 'primary');
  const secondaryCta = value.secondaryCta ? normalizeCta(value.secondaryCta, 'secondary') : null;
  const media = normalizeMedia(value.media);
  const highlights = normalizeHighlights(value.highlights ?? value.stats);

  return {
    headline,
    subheadline,
    tagline,
    primaryCta,
    secondaryCta,
    media,
    highlights,
  };
}

function normalizeLayout(value: unknown): HeroBlockLayout {
  if (!isRecord(value)) {
    return DEFAULT_LAYOUT;
  }
  const variant = value.variant === 'stacked' ? 'stacked' : 'split';
  const theme = value.theme === 'dark' ? 'dark' : 'light';
  const alignment = value.alignment === 'center' ? 'center' : 'left';
  return { variant, theme, alignment };
}

function collectLocaleMap(
  value: Record<string, unknown>,
  localeOrder: string[],
): Record<string, HeroBlockLocaleContent> {
  const locales: Record<string, HeroBlockLocaleContent> = {};
  localeOrder.forEach((locale) => {
    const entry = value[locale];
    if (entry) {
      locales[locale] = normalizeLocaleContent(entry);
    }
  });

  if (!Object.keys(locales).length) {
    Object.entries(value).forEach(([key, entry]) => {
      if (typeof key === 'string' && key.length <= 5 && entry) {
        locales[key] = normalizeLocaleContent(entry);
      }
    });
  }

  if (!Object.keys(locales).length) {
    locales[localeOrder[0] ?? 'ru'] = createDefaultHeroLocale();
  }

  return locales;
}

export function ensureHeroConfig(
  value: unknown,
  localeOrder: string[] = ['ru'],
): HeroBlockConfig {
  const normalizedLocales = localeOrder.length ? localeOrder : ['ru'];
  if (!isRecord(value)) {
    return createDefaultHeroConfig(normalizedLocales[0]);
  }

  const maybeLocales = isRecord(value.locales)
    ? (value.locales as Record<string, unknown>)
    : value;

  const layout = normalizeLayout(value.layout);
  const locales = collectLocaleMap(maybeLocales, normalizedLocales);

  normalizedLocales.forEach((locale) => {
    if (!locales[locale]) {
      locales[locale] = createDefaultHeroLocale();
    }
  });

  return {
    layout,
    locales,
  };
}

export function getHeroLocaleContent(
  config: HeroBlockConfig,
  locale: string,
): HeroBlockLocaleContent {
  if (config.locales[locale]) {
    return config.locales[locale];
  }
  const [firstLocale] = Object.keys(config.locales);
  if (firstLocale && config.locales[firstLocale]) {
    return config.locales[firstLocale];
  }
  return createDefaultHeroLocale();
}
