const supportedLocales = (process.env.NEXT_PUBLIC_SUPPORTED_LOCALES ?? "ru,en")
  .split(",")
  .map((locale) => locale.trim())
  .filter((locale) => locale.length > 0);

const locales = supportedLocales.length > 0 ? supportedLocales : ["ru", "en"];

const defaultLocaleEnv = process.env.NEXT_PUBLIC_DEFAULT_LOCALE ?? locales[0];
const defaultLocale = locales.includes(defaultLocaleEnv)
  ? defaultLocaleEnv
  : locales[0];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
  },
  transpilePackages: ["@caves/site-shared"],
  i18n: {
    locales,
    defaultLocale,
  },
};

export default nextConfig;
