import { revalidateTag } from "next/cache";
import { NextResponse } from "next/server";

import {
  buildSitePageCacheTag,
  SITE_PAGE_REVALIDATE_SECONDS,
} from "@/lib/site-page-api";
import {
  DEFAULT_LOCALE,
  isSupportedLocale,
  normalizeLocale,
} from "@/config/i18n";

type RevalidatePayload = {
  secret?: string;
  slug?: string;
  locale?: string;
};

type PreviewLocaleOverride = {
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
};

type PreviewRequestPayload = {
  pageId: string;
  secret?: string | null;
  locale?: string | null;
  layout?: string | null;
  layouts?: string[] | null;
  version?: number | null;
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
  locales?: Record<string, PreviewLocaleOverride>;
};

const previewSecret = process.env.SITE_PAGE_PREVIEW_SECRET;
const apiBase =
  process.env.SITE_API_BASE ??
  process.env.NEXT_PUBLIC_SITE_API_BASE ??
  "http://127.0.0.1:8000";

export async function POST(request: Request) {
  const contentType = request.headers.get("content-type") ?? "";
  let parsedBody: unknown = null;
  if (contentType.includes("application/json")) {
    parsedBody = await request.json().catch(() => null);
  }

  if (
    parsedBody &&
    typeof parsedBody === "object" &&
    parsedBody !== null &&
    "pageId" in parsedBody
  ) {
    return handlePreviewRequest(request, parsedBody as PreviewRequestPayload);
  }

  const payload = await readRevalidatePayload(request, parsedBody);
  return handleRevalidateRequest(payload);
}

async function handlePreviewRequest(
  request: Request,
  payload: PreviewRequestPayload,
) {
  const pageId = String(payload.pageId ?? "").trim();
  if (!pageId) {
    return NextResponse.json(
      { error: "pageId is required for preview requests" },
      { status: 400 },
    );
  }

  const locale =
    typeof payload.locale === "string" && payload.locale
      ? normalizeLocale(payload.locale)
      : undefined;

  const { secret: _unusedSecret, pageId: _unusedPageId, ...rest } = payload;
  void _unusedSecret;
  void _unusedPageId;
  const bodyPayload = {
    ...rest,
    ...(locale ? { locale } : {}),
  };

  const backendUrl = buildBackendPreviewUrl(pageId);
  const headers: Record<string, string> = {
    Accept: "application/json",
    "Content-Type": "application/json",
  };

  const csrfHeader = request.headers.get("x-csrf-token");
  if (csrfHeader) {
    headers["x-csrf-token"] = csrfHeader;
  }
  const cookieHeader = request.headers.get("cookie");
  if (cookieHeader) {
    headers.cookie = cookieHeader;
  }
  const authHeader = request.headers.get("authorization");
  if (authHeader) {
    headers.authorization = authHeader;
  }

  const backendResponse = await fetch(backendUrl, {
    method: "POST",
    headers,
    body: JSON.stringify(bodyPayload),
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  const rawSetCookie =
    (backendResponse.headers as unknown as { getSetCookie?: () => string[] })
      ?.getSetCookie?.() ?? [];
  for (const cookie of rawSetCookie) {
    responseHeaders.append("set-cookie", cookie);
  }

  const contentType = backendResponse.headers.get("content-type") ?? "";
  const responseText = await backendResponse.text();
  if (!contentType || !contentType.includes("application/json")) {
    if (responseText.length === 0) {
      return new NextResponse(null, {
        status: backendResponse.status,
        headers: responseHeaders,
      });
    }
    responseHeaders.set("content-type", contentType || "text/plain");
    return new NextResponse(responseText, {
      status: backendResponse.status,
      headers: responseHeaders,
    });
  }

  let jsonBody: unknown = null;
  if (responseText.length > 0) {
    try {
      jsonBody = JSON.parse(responseText);
    } catch {
      return NextResponse.json(
        {
          error: "Invalid JSON received from backend preview endpoint",
        },
        { status: 502 },
      );
    }
  }

  return NextResponse.json(jsonBody, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

function handleRevalidateRequest(payload: RevalidatePayload) {
  const { secret, slug = "main", locale } = payload;

  if (!previewSecret || secret !== previewSecret) {
    return NextResponse.json(
      { revalidated: false, message: "Invalid preview secret" },
      { status: 401 },
    );
  }

  const normalizedLocale = locale
    ? normalizeLocale(locale)
    : DEFAULT_LOCALE;

  revalidateTag(buildSitePageCacheTag(slug, normalizedLocale));

  return NextResponse.json({
    revalidated: true,
    slug,
    locale: normalizedLocale,
    revalidateInSeconds: SITE_PAGE_REVALIDATE_SECONDS,
  });
}

async function readPayload(request: Request): Promise<RevalidatePayload> {
  const contentType = request.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      const payload = (await request.json()) as RevalidatePayload;
      return payload;
    } catch {
      return {};
    }
  }
  const params = new URL(request.url).searchParams;
  const result: RevalidatePayload = {};
  if (params.has("secret")) {
    result.secret = params.get("secret") ?? undefined;
  }
  if (params.has("slug")) {
    result.slug = params.get("slug") ?? undefined;
  }
  if (params.has("locale")) {
    const rawLocale = params.get("locale") ?? undefined;
    if (rawLocale && isSupportedLocale(rawLocale)) {
      result.locale = rawLocale;
    } else {
      result.locale = rawLocale ?? undefined;
    }
  }
  return result;
}

async function readRevalidatePayload(
  request: Request,
  parsedBody: unknown,
): Promise<RevalidatePayload> {
  if (
    parsedBody &&
    typeof parsedBody === "object" &&
    parsedBody !== null &&
    !("pageId" in parsedBody)
  ) {
    const source = parsedBody as Record<string, unknown>;
    return {
      secret: toOptionalString(source.secret) ?? undefined,
      slug: toOptionalString(source.slug) ?? undefined,
      locale: toOptionalString(source.locale) ?? undefined,
    };
  }
  return readPayload(request);
}

function toOptionalString(value: unknown): string | null {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  }
  return null;
}

function buildBackendPreviewUrl(pageId: string): string {
  const normalizedBase = apiBase.replace(/\/+$/u, "");
  return `${normalizedBase}/v1/site/pages/${encodeURIComponent(pageId)}/preview`;
}
