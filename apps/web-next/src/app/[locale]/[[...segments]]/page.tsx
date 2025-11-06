import type { Metadata } from "next";

import { normalizeLocale } from "@/config/i18n";
import { buildMetadataForPage, getSitePage } from "@/lib/site-page-api";
import { renderSitePage } from "@/lib/site-page-renderer";

type LocaleCatchAllPageParams = {
  locale: string;
  segments?: string[];
};

type LocaleCatchAllPageProps = Readonly<{
  params: Promise<LocaleCatchAllPageParams>;
}>;

export async function generateMetadata(
  { params }: LocaleCatchAllPageProps,
): Promise<Metadata> {
  const resolved = await params;
  const locale = normalizeLocale(resolved.locale);
  const { slug } = parseSegments(resolved.segments);
  const page = await getSitePage(slug, locale);
  if (!page) {
    return {
      title: "Page not found",
    };
  }
  return buildMetadataForPage(page);
}

export default async function LocaleCatchAllPage(
  { params }: LocaleCatchAllPageProps,
) {
  const resolved = await params;
  const locale = normalizeLocale(resolved.locale);
  const { slug, route } = parseSegments(resolved.segments);

  return renderSitePage({
    slug,
    locale,
    route: buildRoute(locale, route),
  });
}

function parseSegments(segments?: string[]) {
  const slugSegments = (segments ?? []).map((segment) =>
    decodeURIComponent(segment).trim(),
  );
  const filteredSegments = slugSegments.filter((segment) => segment.length > 0);
  const slug =
    filteredSegments.length > 0 ? filteredSegments.join("/") : "main";
  return {
    slug,
    route: filteredSegments,
  };
}

function buildRoute(locale: string, segments: string[]) {
  if (segments.length === 0) {
    return `/${locale}`;
  }
  return `/${locale}/${segments.join("/")}`;
}
