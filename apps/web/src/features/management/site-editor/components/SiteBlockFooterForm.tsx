import React from 'react';
import { Button, Card, Input, Tabs, Textarea } from '@ui';
import { Plus, Trash2 } from '@icons';
import {
  createDefaultFooterConfig,
  createDefaultFooterLocaleContent,
  type FooterConfig,
  type FooterContact,
  type FooterLink,
  type FooterLocaleContent,
} from '../schemas/footerBlock';

type SiteBlockFooterFormProps = {
  value: FooterConfig | null;
  disabled?: boolean;
  onChange: (next: FooterConfig) => void;
};

const LOCALE_TABS: Array<{ key: string; label: string }> = [
  { key: 'ru', label: 'Русский' },
  { key: 'en', label: 'Английский' },
];

function updateLocale(
  config: FooterConfig,
  locale: 'ru' | 'en',
  updater: (current: FooterLocaleContent) => FooterLocaleContent,
): FooterConfig {
  const nextLocales = { ...config.locales };
  const current = nextLocales[locale] ?? createDefaultFooterLocaleContent();
  nextLocales[locale] = updater(current);
  return {
    ...config,
    locales: nextLocales,
  };
}

function updateList<T>(
  list: T[],
  index: number,
  updater: (item: T) => T,
  fallback: T,
): T[] {
  if (index < 0 || index >= list.length) {
    return list;
  }
  const next = list.slice();
  next[index] = updater(next[index] ?? fallback);
  return next;
}

function removeAt<T>(list: T[], index: number): T[] {
  if (index < 0 || index >= list.length) {
    return list;
  }
  return [...list.slice(0, index), ...list.slice(index + 1)];
}

function addEntry<T>(list: T[], entry: T, limit = 20): T[] {
  if (list.length >= limit) {
    return list;
  }
  return [...list, entry];
}

function renderLinkRow({
  link,
  index,
  disabled,
  onChange,
  onRemove,
}: {
  link: FooterLink;
  index: number;
  disabled?: boolean;
  onChange: (next: FooterLink) => void;
  onRemove: () => void;
}): React.ReactElement {
  return (
    <div className="flex flex-wrap gap-2" key={`link-${index}`}>
      <Input
        className="flex-1"
        label="Название"
        value={link.label}
        disabled={disabled}
        onChange={(event) => onChange({ ...link, label: event.target.value })}
      />
      <Input
        className="flex-1"
        label="Ссылка"
        placeholder="https://"
        value={link.href}
        disabled={disabled}
        onChange={(event) => onChange({ ...link, href: event.target.value })}
      />
      <Button
        type="button"
        variant="ghost"
        color="neutral"
        size="icon"
        aria-label="Удалить ссылку"
        onClick={onRemove}
        disabled={disabled}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}

function renderContactRow({
  contact,
  index,
  disabled,
  onChange,
  onRemove,
}: {
  contact: FooterContact;
  index: number;
  disabled?: boolean;
  onChange: (next: FooterContact) => void;
  onRemove: () => void;
}): React.ReactElement {
  return (
    <div className="flex flex-wrap gap-2" key={`contact-${index}`}>
      <Input
        className="flex-1"
        label="Подпись"
        value={contact.label}
        disabled={disabled}
        onChange={(event) => onChange({ ...contact, label: event.target.value })}
      />
      <Input
        className="flex-1"
        label="Значение"
        value={contact.value}
        disabled={disabled}
        onChange={(event) => onChange({ ...contact, value: event.target.value })}
      />
      <Input
        className="flex-1"
        label="Ссылка (опционально)"
        value={contact.href ?? ''}
        disabled={disabled}
        onChange={(event) => onChange({ ...contact, href: event.target.value })}
      />
      <Button
        type="button"
        variant="ghost"
        color="neutral"
        size="icon"
        aria-label="Удалить контакт"
        onClick={onRemove}
        disabled={disabled}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}

export default function SiteBlockFooterForm({
  value,
  disabled,
  onChange,
}: SiteBlockFooterFormProps): React.ReactElement {
  const config = value ?? createDefaultFooterConfig();
  const [activeLocale, setActiveLocale] = React.useState<'ru' | 'en'>('ru');

  const currentLocale = config.locales[activeLocale] ?? createDefaultFooterLocaleContent();

  return (
    <div className="space-y-4">
      <Tabs
        value={activeLocale}
        onChange={(next) => setActiveLocale(next as 'ru' | 'en')}
        items={LOCALE_TABS}
      />

      <Card className="space-y-3 border border-gray-100 p-4 dark:border-dark-700">
        <Input
          label="Название компании"
          value={currentLocale.company}
          disabled={disabled}
          onChange={(event) =>
            onChange(
              updateLocale(config, activeLocale, (prev) => ({
                ...prev,
                company: event.target.value,
              })),
            )
          }
        />
        <Textarea
          label="Описание (кратко о компании)"
          value={currentLocale.description}
          disabled={disabled}
          rows={3}
          onChange={(event) =>
            onChange(
              updateLocale(config, activeLocale, (prev) => ({
                ...prev,
                description: event.target.value,
              })),
            )
          }
        />
        <Textarea
          label="Адрес и юридическая информация"
          value={currentLocale.address}
          disabled={disabled}
          rows={3}
          onChange={(event) =>
            onChange(
              updateLocale(config, activeLocale, (prev) => ({
                ...prev,
                address: event.target.value,
              })),
            )
          }
        />
      </Card>

      <Card className="space-y-4 border border-gray-100 p-4 dark:border-dark-700">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Контакты</h4>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() =>
              onChange(
                updateLocale(config, activeLocale, (prev) => ({
                  ...prev,
                  contacts: addEntry(prev.contacts, { label: '', value: '', href: '' }),
                })),
              )
            }
            disabled={disabled}
            className="inline-flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            <span>Добавить</span>
          </Button>
        </div>
        {currentLocale.contacts.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-dark-200">Нет контактов.</p>
        ) : (
          currentLocale.contacts.map((contact, index) =>
            renderContactRow({
              contact,
              index,
              disabled,
              onChange: (nextContact) =>
                onChange(
                  updateLocale(config, activeLocale, (prev) => ({
                    ...prev,
                    contacts: updateList(prev.contacts, index, () => nextContact, contact),
                  })),
                ),
              onRemove: () =>
                onChange(
                  updateLocale(config, activeLocale, (prev) => ({
                    ...prev,
                    contacts: removeAt(prev.contacts, index),
                  })),
                ),
            }),
          )
        )}
      </Card>

      <Card className="space-y-4 border border-gray-100 p-4 dark:border-dark-700">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Ссылки</h4>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() =>
              onChange(
                updateLocale(config, activeLocale, (prev) => ({
                  ...prev,
                  links: addEntry(prev.links, { label: '', href: '' }),
                })),
              )
            }
            disabled={disabled}
            className="inline-flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            <span>Добавить</span>
          </Button>
        </div>
        {currentLocale.links.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-dark-200">Нет ссылок.</p>
        ) : (
          currentLocale.links.map((link, index) =>
            renderLinkRow({
              link,
              index,
              disabled,
              onChange: (nextLink) =>
                onChange(
                  updateLocale(config, activeLocale, (prev) => ({
                    ...prev,
                    links: updateList(prev.links, index, () => nextLink, link),
                  })),
                ),
              onRemove: () =>
                onChange(
                  updateLocale(config, activeLocale, (prev) => ({
                    ...prev,
                    links: removeAt(prev.links, index),
                  })),
                ),
            }),
          )
        )}
      </Card>

      <Card className="space-y-4 border border-gray-100 p-4 dark:border-dark-700">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Соцсети</h4>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() =>
              onChange({
                ...config,
                social: addEntry(config.social, { label: '', href: '' }),
              })
            }
            disabled={disabled}
            className="inline-flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            <span>Добавить</span>
          </Button>
        </div>
        {config.social.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-dark-200">Нет ссылок на соцсети.</p>
        ) : (
          config.social.map((link, index) =>
            renderLinkRow({
              link,
              index,
              disabled,
              onChange: (nextLink) =>
                onChange({
                  ...config,
                  social: updateList(config.social, index, () => nextLink, link),
                }),
              onRemove: () =>
                onChange({
                  ...config,
                  social: removeAt(config.social, index),
                }),
            }),
          )
        )}
      </Card>

      <Input
        label="Copyright"
        value={config.copyright}
        disabled={disabled}
        onChange={(event) =>
          onChange({
            ...config,
            copyright: event.target.value,
          })
        }
      />
    </div>
  );
}
