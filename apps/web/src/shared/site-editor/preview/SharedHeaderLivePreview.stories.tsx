import type { Meta, StoryObj } from '@storybook/react';
import { SharedHeaderLivePreview } from './SharedHeaderLivePreview';
import type { HeaderLayoutVariant, SiteHeaderConfig } from '@shared/site-editor/schemas/siteHeader';

const baseConfig: SiteHeaderConfig = {
  branding: {
    title: 'Caves Platform',
    subtitle: 'Единый доступ к сервисам',
    href: '/',
    logo: {
      light: 'https://dummyimage.com/80x80/1f2937/ffffff.png&text=C',
      dark: 'https://dummyimage.com/80x80/ffffff/1f2937.png&text=C',
      alt: 'Caves',
    },
  },
  navigation: {
    primary: [
      {
        id: 'features',
        label: 'Возможности',
        href: '#features',
        children: [
          { id: 'analytics', label: 'Аналитика', href: '#analytics' },
          { id: 'automation', label: 'Автоматизация', href: '#automation' },
          { id: 'security', label: 'Безопасность', href: '#security' },
        ],
      },
      { id: 'pricing', label: 'Тарифы', href: '#pricing' },
      { id: 'support', label: 'Поддержка', href: '#support' },
      { id: 'blog', label: 'Блог', href: '#blog' },
    ],
    secondary: [
      { id: 'docs', label: 'Документация', href: '#docs' },
      { id: 'status', label: 'Статус', href: '#status' },
    ],
    utility: [
      { id: 'ru', label: 'Ru', href: '#ru' },
      { id: 'login', label: 'Войти', href: '#login' },
    ],
    cta: {
      id: 'demo',
      label: 'Запросить демо',
      href: '#demo',
      style: 'primary',
    },
    mobile: {
      menu: [
        { id: 'mobile-features', label: 'Возможности', href: '#features' },
        { id: 'mobile-pricing', label: 'Тарифы', href: '#pricing' },
        { id: 'mobile-support', label: 'Поддержка', href: '#support' },
      ],
      cta: {
        id: 'mobile-demo',
        label: 'Получить доступ',
        href: '#demo',
        style: 'secondary',
      },
    },
  },
  layout: {
    variant: 'default',
    sticky: true,
    hideOnScroll: false,
  },
  features: {
    notifications: true,
    personalization: true,
  },
  localization: {
    available: ['ru', 'en'],
    fallbackLocale: 'ru',
  },
  meta: {},
};

const meta: Meta<typeof SharedHeaderLivePreview> = {
  title: 'Site Editor/Preview/SharedHeaderLivePreview',
  component: SharedHeaderLivePreview,
  args: {
    config: baseConfig,
    theme: 'light',
    device: 'desktop',
    locale: 'ru',
    availableLocales: ['ru', 'en'],
  },
  argTypes: {
    variant: {
      options: ['auto', 'default', 'compact', 'mega'],
      control: { type: 'radio' },
      mapping: {
        auto: undefined,
        default: 'default',
        compact: 'compact',
        mega: 'mega',
      },
      description: 'Переопределение layout-варианта',
    },
    theme: {
      options: ['light', 'dark'],
      control: { type: 'inline-radio' },
    },
    device: {
      options: ['desktop', 'mobile'],
      control: { type: 'inline-radio' },
    },
    locale: {
      control: { type: 'text' },
    },
    availableLocales: {
      control: { type: 'object' },
    },
  },
  parameters: {
    layout: 'centered',
    backgrounds: {
      default: 'surface',
      values: [
        { name: 'surface', value: '#f8fafc' },
        { name: 'dark', value: '#0f172a' },
      ],
    },
  },
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof SharedHeaderLivePreview>;

export const Default: Story = {};

export const Compact: Story = {
  args: {
    variant: 'compact' as HeaderLayoutVariant,
    locale: 'en',
  },
};

export const MegaDesktop: Story = {
  args: {
    variant: 'mega' as HeaderLayoutVariant,
    availableLocales: ['ru', 'en', 'de'],
  },
};

export const DarkMobile: Story = {
  args: {
    theme: 'dark',
    device: 'mobile',
    locale: 'en',
  },
};
