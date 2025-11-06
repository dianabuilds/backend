import React from 'react';
import clsx from 'clsx';
import type {
  HeaderLayoutVariant,
  HeaderMenuGroup,
  HeaderMenuItem,
  SiteHeaderConfig,
} from '@shared/site-editor/schemas/siteHeader';

type PreviewTheme = 'light' | 'dark';
type PreviewDevice = 'desktop' | 'mobile';

export type SharedHeaderLivePreviewProps = {
  config: SiteHeaderConfig | null | undefined;
  variant?: HeaderLayoutVariant | null;
  theme?: PreviewTheme;
  device?: PreviewDevice;
  locale?: string | null;
  availableLocales?: string[] | null;
};

const THEME_TOKENS: Record<PreviewTheme, Record<string, string>> = {
  light: {
    container: 'bg-white text-gray-900 border border-gray-200 shadow-sm',
    subtle: 'text-gray-500',
    navItem: 'text-gray-700 hover:text-gray-900',
    divider: 'border-gray-200',
    chip: 'bg-gray-100 text-gray-600',
    megaPanel: 'bg-gray-50',
    megaTitle: 'text-gray-800',
    megaItem: 'text-gray-600 hover:text-gray-900',
    buttonPrimary: 'bg-primary-600 text-white hover:bg-primary-500',
    buttonSecondary: 'bg-transparent border border-gray-300 text-gray-700 hover:bg-gray-100',
    buttonLink: 'text-primary-600 hover:text-primary-500',
    mobilePanel: 'border border-gray-200 bg-gray-50',
    mobileItem: 'bg-gray-100 hover:bg-gray-200/70',
  },
  dark: {
    container: 'bg-slate-900 text-white border border-slate-700 shadow-[0_30px_60px_-40px_rgba(15,23,42,0.7)]',
    subtle: 'text-slate-300',
    navItem: 'text-slate-200 hover:text-white',
    divider: 'border-slate-700',
    chip: 'bg-slate-800 border border-slate-700 text-slate-300',
    megaPanel: 'bg-slate-800/60',
    megaTitle: 'text-white',
    megaItem: 'text-slate-200 hover:text-white',
    buttonPrimary: 'bg-indigo-500 text-white hover:bg-indigo-400',
    buttonSecondary: 'bg-transparent border border-slate-600 text-slate-200 hover:bg-slate-800/70',
    buttonLink: 'text-indigo-300 hover:text-indigo-200',
    mobilePanel: 'border border-white/10 bg-white/5 backdrop-blur-sm',
    mobileItem: 'bg-white/10 hover:bg-white/20',
  },
};

const CTA_STYLE_SEQUENCE: Array<HeaderLayoutVariant> = ['default', 'compact', 'mega'];

function pickMenu(items?: HeaderMenuGroup | null): HeaderMenuItem[] {
  if (!items || !Array.isArray(items)) {
    return [];
  }
  return items.filter((item) => item && typeof item === 'object');
}

function pickLocalizedLogo(config: SiteHeaderConfig, theme: PreviewTheme): { src: string | null; alt: string } {
  const logo = config.branding?.logo;
  if (!logo) {
    return { src: null, alt: config.branding?.title || 'Логотип' };
  }
  const themeLogo = theme === 'dark' ? logo.dark || logo.light : logo.light || logo.dark;
  return {
    src: themeLogo && themeLogo.trim() ? themeLogo.trim() : null,
    alt: logo.alt || config.branding?.title || 'Логотип',
  };
}

function formatLocaleToken(value: string): string {
  if (!value) {
    return '—';
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return '—';
  }
  return trimmed.length <= 6 ? trimmed.toUpperCase() : trimmed;
}

function getCtaClasses(style: string | undefined, tokens: Record<string, string>): string {
  switch (style) {
    case 'secondary':
      return clsx(
        'inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-semibold transition-colors',
        tokens.buttonSecondary,
      );
    case 'link':
      return clsx('inline-flex items-center justify-center px-2 text-sm font-semibold transition-colors', tokens.buttonLink);
    case 'primary':
    default:
      return clsx(
        'inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-semibold transition-colors',
        tokens.buttonPrimary,
      );
  }
}

function buildFeatureChips(config: SiteHeaderConfig): string[] {
  const chips: string[] = [];
  if (config.layout?.sticky) {
    chips.push('Sticky');
  }
  if (config.layout?.hideOnScroll) {
    chips.push('Скрывать при прокрутке');
  }
  if (config.localization?.available?.length) {
    const locales = config.localization.available.filter((locale) => typeof locale === 'string' && locale.trim());
    if (locales.length) {
      chips.push(`Локали: ${locales.join(', ')}`);
    }
  }
  const featureEntries = Object.entries(config.features ?? {})
    .filter(([, value]) => value != null && value !== false && value !== '');
  featureEntries.slice(0, 3).forEach(([key]) => {
    chips.push(`Фича: ${key}`);
  });
  return chips;
}

function renderMenuItems(items: HeaderMenuItem[], tokens: Record<string, string>): React.ReactElement {
  if (!items.length) {
    return <span className={clsx('text-xs', tokens.subtle)}>Нет пунктов меню</span>;
  }
  return (
    <div className="flex flex-wrap items-center gap-3 text-sm font-medium">
      {items.slice(0, 8).map((item) => (
        <span
          key={item.id || item.label || item.href}
          className={clsx('cursor-pointer rounded-full px-3 py-1 transition-colors', tokens.navItem)}
        >
          {item.label || 'Без названия'}
        </span>
      ))}
    </div>
  );
}

function renderMegaColumns(items: HeaderMenuItem[], tokens: Record<string, string>): React.ReactElement | null {
  const columns = items
    .filter((item) => item.children && item.children.length)
    .slice(0, 3);
  if (!columns.length) {
    return null;
  }
  return (
    <div className={clsx('mt-6 rounded-2xl p-4', tokens.megaPanel)}>
      <div className="grid gap-4 md:grid-cols-3">
        {columns.map((item) => (
          <div key={`mega-${item.id || item.label}`} className="space-y-2">
            <div className={clsx('text-sm font-semibold uppercase tracking-wide', tokens.megaTitle)}>
              {item.label || 'Без названия'}
            </div>
            <ul className="space-y-1 text-xs">
              {item.children!.slice(0, 6).map((child, index) => (
                <li
                  key={`${item.id || item.label}-child-${child?.id || child?.label || index}`}
                  className={clsx('cursor-pointer rounded-md px-2 py-1 transition-colors', tokens.megaItem)}
                >
                  {child?.label || 'Без названия'}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

export function SharedHeaderLivePreview({
  config,
  variant,
  theme = 'light',
  device = 'desktop',
  locale,
  availableLocales,
}: SharedHeaderLivePreviewProps): React.ReactElement {
  if (!config) {
    return (
      <div className="rounded-2xl border border-dashed border-gray-200 p-4 text-xs text-gray-500">
        Конфигурация ещё не загружена.
      </div>
    );
  }

  const effectiveVariant = variant ?? config.layout?.variant ?? CTA_STYLE_SEQUENCE[0];
  const tokens = THEME_TOKENS[theme];
  const logo = pickLocalizedLogo(config, theme);
  const primaryMenu = pickMenu(config.navigation?.primary);
  const utilityMenu = pickMenu(config.navigation?.utility);
  const secondaryMenu = pickMenu(config.navigation?.secondary);
  const mobileMenu =
    pickMenu(config.navigation?.mobile?.menu).length > 0 ? pickMenu(config.navigation?.mobile?.menu) : primaryMenu;
  const cta = config.navigation?.cta ?? config.navigation?.mobile?.cta ?? null;
  const chips = buildFeatureChips(config);
  if (locale) {
    chips.unshift(`Локаль: ${formatLocaleToken(locale)}`);
  } else if (availableLocales?.length) {
    chips.unshift(`Локали: ${availableLocales.map((entry) => formatLocaleToken(entry)).join(', ')}`);
  }

  const containerWidth = device === 'mobile' ? 'max-w-[390px]' : 'w-full';

  return (
    <div className={clsx('transition-colors', containerWidth)}>
      <div className={clsx('rounded-3xl p-5 md:p-6 lg:p-7', tokens.container)}>
        <div
          className={clsx(
            'flex flex-col gap-4 md:flex-row md:items-center md:justify-between',
            device === 'mobile' ? 'gap-3' : effectiveVariant === 'compact' ? 'gap-4' : 'gap-6',
          )}
        >
          <div className="flex flex-1 items-center gap-4 md:gap-6">
            <div className="flex items-center gap-3">
              {logo.src ? (
                <img
                  src={logo.src}
                  alt={logo.alt}
                  className={clsx(
                    'h-10 w-10 rounded-xl object-cover',
                    theme === 'dark' ? 'border border-white/20' : 'border border-gray-200',
                  )}
                  draggable={false}
                />
              ) : (
                <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-dashed border-current/30 text-sm font-semibold uppercase">
                  {(config.branding?.title || 'logo').slice(0, 2)}
                </div>
              )}
                <div>
                  <div className="text-sm font-semibold uppercase tracking-wide">{config.branding?.title || 'Заголовок'}</div>
                  {config.branding?.subtitle ? (
                    <div className={clsx('text-xs', tokens.subtle)}>{config.branding.subtitle}</div>
                  ) : null}
                </div>
                {locale ? (
                  <span className={clsx('rounded-full px-2.5 py-1 text-[11px] font-medium uppercase tracking-wide', tokens.chip)}>
                    {formatLocaleToken(locale)}
                  </span>
                ) : null}
              </div>
              {device === 'desktop' ? (
              <div className="hidden flex-1 flex-col gap-3 lg:flex">
                {renderMenuItems(primaryMenu, tokens)}
                {secondaryMenu.length ? (
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    {secondaryMenu.slice(0, 6).map((item) => (
                      <span
                        key={`secondary-${item.id || item.label || item.href}`}
                        className={clsx('rounded-full border px-2.5 py-0.5', tokens.divider, tokens.subtle)}
                      >
                        {item.label || 'Без названия'}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
          </div>
          <div className="flex items-center gap-3 md:min-w-[200px] md:justify-end">
            {utilityMenu.slice(0, 3).map((item) => (
              <span key={`utility-${item.id || item.label || item.href}`} className={clsx('text-xs', tokens.subtle)}>
                {item.label || '—'}
              </span>
            ))}
            {cta ? (
              <span className={getCtaClasses(cta.style || config.navigation?.cta?.style, tokens)}>
                {cta.label || 'CTA'}
              </span>
            ) : null}
          </div>
        </div>

        {device === 'mobile' ? (
          <div className={clsx('mt-5 space-y-3 rounded-2xl p-4', tokens.mobilePanel)}>
            <div className="flex items-center justify-between">
              <div className={clsx('text-xs font-semibold uppercase tracking-wide', tokens.subtle)}>Меню</div>
              <div className="flex flex-col gap-1.5">
                <span className="h-0.5 w-6 rounded-full bg-current/60" />
                <span className="h-0.5 w-6 rounded-full bg-current" />
                <span className="h-0.5 w-6 rounded-full bg-current/60" />
              </div>
            </div>
            <ul className="space-y-2 text-sm">
              {mobileMenu.length ? (
                mobileMenu.slice(0, 6).map((item) => (
                  <li
                    key={`mobile-${item.id || item.label || item.href}`}
                    className={clsx('rounded-xl px-3 py-2 transition-colors', tokens.mobileItem)}
                  >
                    <div className="font-medium">{item.label || 'Без названия'}</div>
                    {item.description ? (
                      <div className={clsx('text-xs', tokens.subtle)}>{item.description}</div>
                    ) : null}
                  </li>
                ))
              ) : (
                <li className={clsx('text-xs', tokens.subtle)}>Нет пунктов мобильного меню</li>
              )}
            </ul>
            {config.navigation?.mobile?.cta ? (
              <div className="pt-3">
                <span className={getCtaClasses(config.navigation.mobile.cta.style, tokens)}>
                  {config.navigation.mobile.cta.label || 'CTA'}
                </span>
              </div>
            ) : null}
          </div>
        ) : null}

        {device === 'desktop' && effectiveVariant === 'mega'
          ? renderMegaColumns(primaryMenu, tokens)
          : null}
      </div>
      {chips.length ? (
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {chips.map((chip) => (
            <span key={chip} className={clsx('rounded-full px-3 py-1 text-[11px] uppercase tracking-wide', tokens.chip)}>
              {chip}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
