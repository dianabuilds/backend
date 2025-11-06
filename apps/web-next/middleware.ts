import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import {
  DEFAULT_LOCALE,
  isSupportedLocale,
  normalizeLocale,
} from "./src/config/i18n";

const NEXT_LOCALE_COOKIE = "NEXT_LOCALE";
const PUBLIC_FILE = /\.(?:[a-zA-Z0-9]+)$/;

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (
    pathname.startsWith("/api") ||
    pathname.startsWith("/_next") ||
    pathname.startsWith("/legacy") ||
    PUBLIC_FILE.test(pathname)
  ) {
    return NextResponse.next();
  }

  const segments = pathname.split("/").filter(Boolean);
  const localeInPath = segments[0];

  if (isSupportedLocale(localeInPath)) {
    return ensureLocaleCookie(request, localeInPath);
  }

  const preferredLocale =
    detectLocaleFromCookie(request) ??
    detectLocaleFromHeader(request.headers.get("accept-language")) ??
    DEFAULT_LOCALE;

  const redirectUrl = request.nextUrl.clone();
  redirectUrl.pathname = buildLocalizedPath(preferredLocale, pathname);

  const response = NextResponse.redirect(redirectUrl);
  response.cookies.set(NEXT_LOCALE_COOKIE, preferredLocale, {
    path: "/",
  });
  return response;
}

export const config = {
  matcher: ["/((?!_next|api|.*\\..*).*)"],
};

function ensureLocaleCookie(
  request: NextRequest,
  locale: string,
): NextResponse {
  const normalized = normalizeLocale(locale);
  const response = NextResponse.next();
  const existing = request.cookies.get(NEXT_LOCALE_COOKIE)?.value;
  if (existing !== normalized) {
    response.cookies.set(NEXT_LOCALE_COOKIE, normalized, { path: "/" });
  }
  return response;
}

function detectLocaleFromCookie(request: NextRequest): string | null {
  const value = request.cookies.get(NEXT_LOCALE_COOKIE)?.value;
  if (value && isSupportedLocale(value)) {
    return normalizeLocale(value);
  }
  return null;
}

function detectLocaleFromHeader(header: string | null): string | null {
  if (!header) {
    return null;
  }
  const parsed = header
    .split(",")
    .map((token) => token.trim())
    .filter(Boolean)
    .map((token) => {
      const [langPart, ...params] = token.split(";");
      const primary = langPart.toLowerCase();
      const qParam = params
        .map((part) => part.trim())
        .find((part) => part.startsWith("q="));
      const weight = qParam ? Number.parseFloat(qParam.slice(2)) : 1;
      return {
        locale: primary,
        weight: Number.isFinite(weight) ? weight : 1,
      };
    })
    .sort((a, b) => b.weight - a.weight);

  for (const { locale, weight } of parsed) {
    if (weight <= 0) {
      continue;
    }
    const candidate = locale.split("-")[0];
    if (isSupportedLocale(candidate)) {
      return normalizeLocale(candidate);
    }
  }
  return null;
}

function buildLocalizedPath(locale: string, pathname: string) {
  const sanitized = pathname.replace(/^\/+/, "");
  if (!sanitized) {
    return `/${locale}`;
  }
  return `/${locale}/${sanitized}`;
}
