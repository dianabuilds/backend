type FooterLocale = 'ru' | 'en';

export type FooterLink = {
  label: string;
  href: string;
};

export type FooterContact = {
  label: string;
  value: string;
  href?: string | null;
};

export type FooterLocaleContent = {
  company: string;
  description: string;
  address: string;
  contacts: FooterContact[];
  links: FooterLink[];
};

export type FooterConfig = {
  locales: Record<FooterLocale, FooterLocaleContent>;
  social: FooterLink[];
  copyright: string;
};

const SUPPORTED_LOCALES: FooterLocale[] = ['ru', 'en'];

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function pickString(value: unknown): string | null {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length ? trimmed : null;
  }
  return null;
}

function normalizeLink(value: unknown): FooterLink {
  if (isRecord(value)) {
    const label = pickString(value.label) ?? '';
    const href = pickString(value.href) ?? '';
    return { label, href };
  }
  return { label: '', href: '' };
}

function normalizeLinks(value: unknown): FooterLink[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((entry) => normalizeLink(entry))
    .filter((entry) => entry.label.length || entry.href.length);
}

function normalizeContacts(value: unknown): FooterContact[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((entry) => {
      if (!isRecord(entry)) {
        return null;
      }
      const label = pickString(entry.label) ?? '';
      const val = pickString(entry.value) ?? '';
      const href = pickString(entry.href);
      if (!label.length && !val.length) {
        return null;
      }
      const contact: FooterContact = { label, value: val };
      if (href !== null) {
        contact.href = href;
      }
      return contact;
    })
    .filter((entry): entry is FooterContact => Boolean(entry));
}

function normalizeLocaleContent(value: unknown): FooterLocaleContent {
  if (!isRecord(value)) {
    return createDefaultFooterLocaleContent();
  }
  const company = pickString(value.company) ?? '';
  const description = pickString(value.description) ?? '';
  const address =
    pickString(value.address) ??
    pickString((value.legal as Record<string, unknown> | undefined)?.address) ??
    '';
  const contacts = normalizeContacts(value.contacts ?? value.contact_list);
  const links = normalizeLinks(value.links ?? value.navigation);
  return {
    company,
    description,
    address,
    contacts,
    links,
  };
}

export function createDefaultFooterLocaleContent(): FooterLocaleContent {
  return {
    company: '',
    description: '',
    address: '',
    contacts: [],
    links: [],
  };
}

export function createDefaultFooterConfig(): FooterConfig {
  const locales: Record<FooterLocale, FooterLocaleContent> = {
    ru: createDefaultFooterLocaleContent(),
    en: createDefaultFooterLocaleContent(),
  };
  return {
    locales,
    social: [],
    copyright: '',
  };
}

export function ensureFooterConfig(value: unknown): FooterConfig {
  if (!isRecord(value)) {
    return createDefaultFooterConfig();
  }
  const result = createDefaultFooterConfig();
  const rawLocales = isRecord(value.locales) ? (value.locales as Record<string, unknown>) : {};
  SUPPORTED_LOCALES.forEach((locale) => {
    const entry = rawLocales[locale];
    result.locales[locale] = normalizeLocaleContent(entry);
  });
  result.social = normalizeLinks(value.social);
  result.copyright = pickString(value.copyright) ?? '';
  return result;
}
