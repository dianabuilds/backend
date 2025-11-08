import React from 'react';
import { Card, Input, Select, Textarea, TagInput } from '@ui';
import {
  createDefaultHeroLocale,
  type HeroBlockConfig,
  type HeroBlockLocaleContent,
  type HeroBlockCtaStyle,
  type HeroBlockMedia,
} from '@shared/site-editor/schemas/heroBlock';

type SiteBlockHeroFormProps = {
  value: HeroBlockConfig;
  onChange: (next: HeroBlockConfig) => void;
  localeOptions: string[];
  defaultLocale: string;
  disabled?: boolean;
};

const CTA_STYLE_OPTIONS: Array<{ value: HeroBlockCtaStyle; label: string }> = [
  { value: 'primary', label: 'Primary' },
  { value: 'secondary', label: 'Secondary' },
  { value: 'link', label: 'Link' },
];

const VARIANT_OPTIONS: Array<{ value: HeroBlockConfig['layout']['variant']; label: string }> = [
  { value: 'split', label: 'Две колонки' },
  { value: 'stacked', label: 'Одна колонка' },
];

const THEME_OPTIONS: Array<{ value: HeroBlockConfig['layout']['theme']; label: string }> = [
  { value: 'light', label: 'Светлая тема' },
  { value: 'dark', label: 'Тёмная тема' },
];

const ALIGN_OPTIONS: Array<{ value: HeroBlockConfig['layout']['alignment']; label: string }> = [
  { value: 'left', label: 'По левому краю' },
  { value: 'center', label: 'По центру' },
];

function ensureLocale(
  config: HeroBlockConfig,
  locale: string,
  updater: (current: HeroBlockLocaleContent) => HeroBlockLocaleContent,
): HeroBlockConfig {
  const current = config.locales[locale] ?? createDefaultHeroLocale();
  return {
    ...config,
    locales: {
      ...config.locales,
      [locale]: updater(current),
    },
  };
}

function normalizeLocaleOptions(localeOptions: string[], defaultLocale: string): string[] {
  const list = localeOptions.length ? localeOptions : [defaultLocale || 'ru'];
  const unique = Array.from(
    new Set(
      list
        .map((locale) => locale?.trim().toLowerCase())
        .filter((locale): locale is string => Boolean(locale && locale.length)),
    ),
  );
  if (!unique.length) {
    return ['ru'];
  }
  return unique;
}

export function SiteBlockHeroForm({
  value,
  onChange,
  localeOptions,
  defaultLocale,
  disabled,
}: SiteBlockHeroFormProps): React.ReactElement {
  const normalizedLocales = React.useMemo(
    () => normalizeLocaleOptions(localeOptions, defaultLocale),
    [localeOptions, defaultLocale],
  );
  const [activeLocale, setActiveLocale] = React.useState(() => normalizedLocales[0] ?? 'ru');

  React.useEffect(() => {
    setActiveLocale((current) => (normalizedLocales.includes(current) ? current : normalizedLocales[0] ?? 'ru'));
  }, [normalizedLocales]);

  const localeContent = value.locales[activeLocale] ?? createDefaultHeroLocale();

  const handleLocaleFieldChange = React.useCallback(
    (
      updater:
        | HeroBlockLocaleContent
        | ((current: HeroBlockLocaleContent) => HeroBlockLocaleContent),
    ) => {
      onChange(
        ensureLocale(value, activeLocale, (current) =>
          typeof updater === 'function' ? updater(current) : updater,
        ),
      );
    },
    [activeLocale, onChange, value],
  );

  const handleLayoutChange = <Key extends keyof HeroBlockConfig['layout']>(
    key: Key,
    nextValue: HeroBlockConfig['layout'][Key],
  ) => {
    onChange({
      ...value,
      layout: {
        ...value.layout,
        [key]: nextValue,
      },
    });
  };

  const handleCtaChange = (
    target: 'primary' | 'secondary',
    key: 'label' | 'href' | 'style',
    next: string,
  ) => {
    handleLocaleFieldChange((current) => {
      const existing =
        target === 'primary'
          ? current.primaryCta
          : current.secondaryCta ?? { label: '', href: '', style: 'secondary' };
      const updated =
        key === 'style'
          ? { ...existing, style: next as HeroBlockCtaStyle }
          : { ...existing, [key]: next };
      return {
        ...current,
        primaryCta: target === 'primary' ? updated : current.primaryCta,
        secondaryCta: target === 'secondary' ? updated : current.secondaryCta,
      };
    });
  };

  const handleHighlightsChange = (items: string[]) => {
    handleLocaleFieldChange({
      ...localeContent,
      highlights: items,
    });
  };

  const handleMediaChange = (key: keyof HeroBlockMedia, nextValue: string) => {
    handleLocaleFieldChange((current) => {
      const media = current.media ?? { url: '', alt: '' };
      const nextMedia =
        key === 'url'
          ? { ...media, url: nextValue }
          : {
              ...media,
              alt: nextValue,
            };
      if (!nextMedia.url && !nextMedia.alt) {
        return {
          ...current,
          media: null,
        };
      }
      return {
        ...current,
        media: nextMedia,
      };
    });
  };

  const currentPrimaryCta = localeContent.primaryCta;
  const currentSecondaryCta =
    localeContent.secondaryCta ?? { label: '', href: '', style: 'secondary' };

  return (
    <div className="space-y-4">
      <Card className="space-y-4 border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-800">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Локаль
            </label>
            <Select
              value={activeLocale}
              onChange={(event) => setActiveLocale(event.target.value)}
              disabled={disabled}
            >
              {normalizedLocales.map((locale) => (
                <option key={locale} value={locale}>
                  {locale.toUpperCase()}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Вариант макета
            </label>
            <Select
              value={value.layout.variant}
              onChange={(event) =>
                handleLayoutChange('variant', event.target.value as HeroBlockConfig['layout']['variant'])
              }
              disabled={disabled}
            >
              {VARIANT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Тема
            </label>
            <Select
              value={value.layout.theme}
              onChange={(event) =>
                handleLayoutChange('theme', event.target.value as HeroBlockConfig['layout']['theme'])
              }
              disabled={disabled}
            >
              {THEME_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Выравнивание текста
            </label>
            <Select
              value={value.layout.alignment}
              onChange={(event) =>
                handleLayoutChange('alignment', event.target.value as HeroBlockConfig['layout']['alignment'])
              }
              disabled={disabled}
            >
              {ALIGN_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </Card>

      <Card className="space-y-4 border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-800">
        <div className="space-y-1">
          <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Теглайн</label>
          <Input
            value={localeContent.tagline ?? ''}
            onChange={(event) =>
              handleLocaleFieldChange({
                ...localeContent,
                tagline: event.target.value,
              })
            }
            disabled={disabled}
            placeholder="Например, «Платформа Caves»"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Заголовок</label>
          <Input
            value={localeContent.headline}
            onChange={(event) =>
              handleLocaleFieldChange({
                ...localeContent,
                headline: event.target.value,
              })
            }
            disabled={disabled}
            placeholder="Основной посыл hero-блока"
          />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
            Подзаголовок
          </label>
          <Textarea
            rows={3}
            value={localeContent.subheadline ?? ''}
            onChange={(event) =>
              handleLocaleFieldChange({
                ...localeContent,
                subheadline: event.target.value,
              })
            }
            disabled={disabled}
            placeholder="Расскажите подробнее о предложении"
          />
        </div>
      </Card>

      <Card className="space-y-4 border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-800">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Primary CTA — текст
            </label>
            <Input
              value={currentPrimaryCta.label}
              onChange={(event) => handleCtaChange('primary', 'label', event.target.value)}
              disabled={disabled}
              placeholder="Например, «Попробовать бесплатно»"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Primary CTA — ссылка
            </label>
            <Input
              value={currentPrimaryCta.href}
              onChange={(event) => handleCtaChange('primary', 'href', event.target.value)}
              disabled={disabled}
              placeholder="/signup"
            />
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="space-y-1 md:col-span-2">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Secondary CTA — текст
            </label>
            <Input
              value={currentSecondaryCta.label}
              onChange={(event) => handleCtaChange('secondary', 'label', event.target.value)}
              disabled={disabled}
              placeholder="Например, «Узнать больше»"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Secondary CTA — тип
            </label>
            <Select
              value={currentSecondaryCta.style}
              onChange={(event) =>
                handleCtaChange('secondary', 'style', event.target.value as HeroBlockCtaStyle)
              }
              disabled={disabled}
            >
              {CTA_STYLE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Secondary CTA — ссылка
            </label>
            <Input
              value={currentSecondaryCta.href}
              onChange={(event) => handleCtaChange('secondary', 'href', event.target.value)}
              disabled={disabled}
              placeholder="/docs"
            />
          </div>
        </div>
      </Card>

      <Card className="space-y-4 border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-800">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Изображение
            </label>
            <Input
              value={localeContent.media?.url ?? ''}
              onChange={(event) => handleMediaChange('url', event.target.value)}
              disabled={disabled}
              placeholder="https://cdn.caves.dev/hero.png"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
              Alt-текст
            </label>
            <Input
              value={localeContent.media?.alt ?? ''}
              onChange={(event) => handleMediaChange('alt', event.target.value)}
              disabled={disabled}
              placeholder="Описание изображения для доступности"
            />
          </div>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
            Ключевые тезисы (до 4 штук)
          </label>
          <TagInput
            value={localeContent.highlights}
            onChange={handleHighlightsChange}
            disabled={disabled}
            placeholder="Добавьте факты или показатели"
            maxItems={4}
          />
        </div>
      </Card>
    </div>
  );
}

export default SiteBlockHeroForm;
