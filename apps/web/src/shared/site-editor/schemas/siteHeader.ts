export type HeaderPrimitive = string | number | boolean | null;

export type HeaderAnalytics = {
  event?: string;
  context?: Record<string, HeaderPrimitive>;
} | null;

export type HeaderLogo = {
  light: string;
  dark?: string | null;
  alt?: string | null;
};

export type HeaderMenuItem = {
  id: string;
  label: string;
  href: string;
  description?: string | null;
  badge?: string | null;
  icon?: string | null;
  target?: '_self' | '_blank';
  analytics?: HeaderAnalytics;
  children?: HeaderMenuGroup | null;
};

export type HeaderMenuGroup = HeaderMenuItem[];

export type HeaderCta = {
  id?: string;
  label: string;
  href: string;
  target?: '_self' | '_blank';
  style?: HeaderCtaStyle;
  analytics?: HeaderAnalytics;
} | null;
export type HeaderCtaValue = Exclude<HeaderCta, null>;
export type HeaderCtaStyle = 'primary' | 'secondary' | 'link';

export type HeaderBranding = {
  title: string;
  subtitle?: string | null;
  href: string;
  logo?: HeaderLogo;
};

export type HeaderNavigation = {
  primary: HeaderMenuGroup;
  secondary?: HeaderMenuGroup;
  utility?: HeaderMenuGroup;
  cta?: HeaderCta;
  mobile?: {
    menu?: HeaderMenuGroup;
    cta?: HeaderCta;
  };
};

export type HeaderLayoutVariant = 'default' | 'compact' | 'mega';

export type HeaderLayout = {
  variant?: HeaderLayoutVariant;
  sticky?: boolean;
  hideOnScroll?: boolean;
};

export type HeaderFeatures = Record<string, HeaderPrimitive>;

export type HeaderLocalization = {
  fallbackLocale?: string;
  available?: string[];
};

export type SiteHeaderConfig = {
  branding: HeaderBranding;
  navigation: HeaderNavigation;
  layout?: HeaderLayout;
  features?: HeaderFeatures;
  localization?: HeaderLocalization;
  meta?: Record<string, unknown>;
};

export function createDefaultLogo(): HeaderLogo {
  return {
    light: '',
    dark: null,
    alt: null,
  };
}

export function createDefaultMenuItem(): HeaderMenuItem {
  return {
    id: '',
    label: '',
    href: '',
    description: null,
    badge: null,
    icon: null,
    target: '_self',
    analytics: null,
    children: null,
  };
}

export function createDefaultMenuGroup(): HeaderMenuGroup {
  return [];
}

export function createDefaultCta(): HeaderCta {
  return {
    id: '',
    label: '',
    href: '',
    target: '_self',
    style: 'primary',
    analytics: null,
  };
}

export function createDefaultHeaderConfig(): SiteHeaderConfig {
  const menuAnalytics = (group: string, item: string): HeaderAnalytics => ({
    event: 'header.menu.click',
    context: {
      group,
      item,
      surface: 'site-editor-preview',
    },
  });

  const primaryMenu: HeaderMenuGroup = [
    {
      id: 'dashboard',
      label: 'Главная',
      description: 'Сводка продуктов и активностей',
      href: '/dashboard',
      badge: null,
      icon: null,
      target: '_self',
      analytics: menuAnalytics('primary', 'dashboard'),
      children: [
        {
          id: 'overview',
          label: 'Обзор',
          href: '/dashboard/overview',
          description: null,
          badge: null,
          icon: null,
          target: '_self',
          analytics: menuAnalytics('primary.children', 'overview'),
          children: null,
        },
        {
          id: 'metrics',
          label: 'Метрики',
          href: '/dashboard/metrics',
          description: null,
          badge: null,
          icon: null,
          target: '_self',
          analytics: menuAnalytics('primary.children', 'metrics'),
          children: null,
        },
      ],
    },
    {
      id: 'solutions',
      label: 'Решения',
      description: 'Готовые сценарии для сайта',
      href: '/solutions',
      badge: 'New',
      icon: null,
      target: '_self',
      analytics: menuAnalytics('primary', 'solutions'),
      children: [
        {
          id: 'landing',
          label: 'Лендинги',
          href: '/solutions/landing',
          description: null,
          badge: null,
          icon: null,
          target: '_self',
          analytics: menuAnalytics('primary.children', 'landing'),
          children: null,
        },
        {
          id: 'knowledge-base',
          label: 'База знаний',
          href: '/solutions/knowledge-base',
          description: null,
          badge: null,
          icon: null,
          target: '_self',
          analytics: menuAnalytics('primary.children', 'knowledge-base'),
          children: null,
        },
      ],
    },
    {
      id: 'resources',
      label: 'Ресурсы',
      description: 'Документация, новости, сообщество',
      href: '/resources',
      badge: null,
      icon: null,
      target: '_self',
      analytics: menuAnalytics('primary', 'resources'),
      children: [
        {
          id: 'docs',
          label: 'Документация',
          href: '/docs',
          description: null,
          badge: null,
          icon: null,
          target: '_self',
          analytics: menuAnalytics('primary.children', 'docs'),
          children: null,
        },
        {
          id: 'community',
          label: 'Сообщество',
          href: '/community',
          description: null,
          badge: null,
          icon: null,
          target: '_blank',
          analytics: menuAnalytics('primary.children', 'community'),
          children: null,
        },
      ],
    },
  ];

  const secondaryMenu: HeaderMenuGroup = [
    {
      id: 'pricing',
      label: 'Тарифы',
      href: '/pricing',
      description: null,
      badge: null,
      icon: null,
      target: '_self',
      analytics: menuAnalytics('secondary', 'pricing'),
      children: null,
    },
    {
      id: 'partners',
      label: 'Партнёры',
      href: '/partners',
      description: null,
      badge: null,
      icon: null,
      target: '_self',
      analytics: menuAnalytics('secondary', 'partners'),
      children: null,
    },
  ];

  const utilityMenu: HeaderMenuGroup = [
    {
      id: 'support',
      label: 'Поддержка',
      href: '/support',
      description: null,
      badge: null,
      icon: null,
      target: '_self',
      analytics: menuAnalytics('utility', 'support'),
      children: null,
    },
    {
      id: 'login',
      label: 'Войти',
      href: '/auth/login',
      description: null,
      badge: null,
      icon: null,
      target: '_self',
      analytics: menuAnalytics('utility', 'login'),
      children: null,
    },
  ];

  const ctaAnalytics: HeaderAnalytics = {
    event: 'header.cta.click',
    context: {
      surface: 'site-editor-preview',
      position: 'desktop',
    },
  };

  return {
    branding: {
      title: 'Caves Platform',
      subtitle: 'Редактор сайта и библиотека блоков',
      href: '/',
      logo: {
        light: '/static/branding/caves-light.svg',
        dark: '/static/branding/caves-dark.svg',
        alt: 'Caves Platform',
      },
    },
    navigation: {
      primary: primaryMenu,
      secondary: secondaryMenu,
      utility: utilityMenu,
      cta: {
        id: 'cta-demo',
        label: 'Запросить демо',
        href: '/request-demo',
        target: '_self',
        style: 'primary',
        analytics: ctaAnalytics,
      },
      mobile: {
        menu: [...primaryMenu, ...secondaryMenu],
        cta: {
          id: 'cta-mobile',
          label: 'Начать бесплатно',
          href: '/signup',
          target: '_self',
          style: 'secondary',
          analytics: {
            event: 'header.cta.click',
            context: {
              surface: 'site-editor-preview',
              position: 'mobile',
            },
          },
        },
      },
    },
    layout: {
      variant: 'default',
      sticky: true,
      hideOnScroll: false,
    },
    features: {
      showBetaBadge: true,
      enableThemeSwitch: true,
    },
    localization: {
      fallbackLocale: 'ru',
      available: ['ru', 'en'],
    },
    meta: {
      samplePreset: 'default-header',
    },
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function clonePrimitive(value: unknown): HeaderPrimitive {
  if (value === null) return null;
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }
  return null;
}

function cloneAnalytics(value: unknown): HeaderAnalytics {
  if (!isRecord(value)) {
    return null;
  }
  const next: HeaderAnalytics = {};
  if (typeof value.event === 'string') {
    next.event = value.event;
  }
  if (isRecord(value.context)) {
    const context: Record<string, HeaderPrimitive> = {};
    for (const [key, contextValue] of Object.entries(value.context)) {
      context[key] = clonePrimitive(contextValue);
    }
    if (Object.keys(context).length) {
      next.context = context;
    }
  }
  return Object.keys(next).length ? next : null;
}

function cloneMenuItem(value: unknown): HeaderMenuItem {
  const base = createDefaultMenuItem();
  if (!isRecord(value)) {
    return base;
  }
  const analytics = cloneAnalytics(value.analytics);
  const next: HeaderMenuItem = {
    id: typeof value.id === 'string' ? value.id : '',
    label: typeof value.label === 'string' ? value.label : '',
    href: typeof value.href === 'string' ? value.href : '',
    description: typeof value.description === 'string' ? value.description : null,
    badge: typeof value.badge === 'string' ? value.badge : null,
    icon: typeof value.icon === 'string' ? value.icon : null,
    target: value.target === '_blank' ? '_blank' : '_self',
    ...(analytics ? { analytics } : {}),
  };
  if (!analytics && 'analytics' in next) {
    delete (next as { analytics?: HeaderMenuItem['analytics'] }).analytics;
  }
  if (Array.isArray(value.children)) {
    next.children = value.children.map(cloneMenuItem);
  } else {
    next.children = null;
  }
  return next;
}

function cloneMenuGroup(value: unknown): HeaderMenuGroup {
  if (!Array.isArray(value)) {
    return createDefaultMenuGroup();
  }
  return value.map(cloneMenuItem);
}

export { cloneMenuItem, cloneMenuGroup };

function cloneCta(value: unknown): HeaderCta {
  if (value == null) {
    return null;
  }
  if (!isRecord(value)) {
    return null;
  }
  const analytics = cloneAnalytics(value.analytics);
  return {
    id: typeof value.id === 'string' ? value.id : '',
    label: typeof value.label === 'string' ? value.label : '',
    href: typeof value.href === 'string' ? value.href : '',
    target: value.target === '_blank' ? '_blank' : '_self',
    style:
      value.style === 'primary' || value.style === 'secondary' || value.style === 'link'
        ? value.style
        : 'primary',
    ...(analytics ? { analytics } : {}),
  };
}

function cloneLogo(value: unknown): HeaderLogo {
  const base = createDefaultLogo();
  if (!isRecord(value)) {
    return base;
  }
  return {
    light: typeof value.light === 'string' ? value.light : '',
    dark: typeof value.dark === 'string' ? value.dark : null,
    alt: typeof value.alt === 'string' ? value.alt : null,
  };
}

export function ensureHeaderConfig(value: unknown): SiteHeaderConfig {
  const base = createDefaultHeaderConfig();
  if (!isRecord(value)) {
    return base;
  }

  const branding = isRecord(value.branding) ? value.branding : {};
  const navigation = isRecord(value.navigation) ? value.navigation : {};
  const mobileNavigation = isRecord(navigation.mobile) ? navigation.mobile : {};
  const layout = isRecord(value.layout) ? value.layout : {};
  const features = isRecord(value.features) ? value.features : {};
  const localization = isRecord(value.localization) ? value.localization : {};
  const meta = isRecord(value.meta) ? value.meta : {};

  const next: SiteHeaderConfig = {
    branding: {
      title: typeof branding.title === 'string' ? branding.title : '',
      subtitle: typeof branding.subtitle === 'string' ? branding.subtitle : null,
      href: typeof branding.href === 'string' ? branding.href : '',
      logo: cloneLogo(branding.logo),
    },
    navigation: {
      primary: cloneMenuGroup(navigation.primary),
      secondary: cloneMenuGroup(navigation.secondary),
      utility: cloneMenuGroup(navigation.utility),
      cta: cloneCta(navigation.cta),
      mobile: {
        menu: cloneMenuGroup(mobileNavigation.menu),
        cta: cloneCta(mobileNavigation.cta),
      },
    },
  };

  const layoutVariant =
    layout.variant === 'compact' || layout.variant === 'mega' ? layout.variant : 'default';

  next.layout = {
    variant: layoutVariant,
    sticky: typeof layout.sticky === 'boolean' ? layout.sticky : true,
    hideOnScroll: typeof layout.hideOnScroll === 'boolean' ? layout.hideOnScroll : false,
  };

  const featureMap: HeaderFeatures = {};
  for (const [key, featureValue] of Object.entries(features)) {
    featureMap[key] = clonePrimitive(featureValue);
  }
  next.features = featureMap;

  const availableLocales = Array.isArray(localization.available)
    ? localization.available.filter((item) => typeof item === 'string')
    : [];

  next.localization = {
    fallbackLocale:
      typeof localization.fallbackLocale === 'string' ? localization.fallbackLocale : undefined,
    available: availableLocales.length ? (availableLocales as string[]) : undefined,
  };

  next.meta = { ...meta } as Record<string, unknown>;

  return next;
}

export const HEADER_VARIANT_OPTIONS: Array<{ value: HeaderLayoutVariant; label: string }> = [
  { value: 'default', label: 'Стандартный' },
  { value: 'compact', label: 'Компактный' },
  { value: 'mega', label: 'Мега-меню' },
];

export const HEADER_CTA_STYLE_OPTIONS: Array<{ value: HeaderCtaStyle; label: string }> = [
  { value: 'primary', label: 'Primary' },
  { value: 'secondary', label: 'Secondary' },
  { value: 'link', label: 'Link' },
];

export const HEADER_LINK_TARGET_OPTIONS: Array<{ value: '_self' | '_blank'; label: string }> = [
  { value: '_self', label: 'Текущая вкладка' },
  { value: '_blank', label: 'Новая вкладка' },
];
