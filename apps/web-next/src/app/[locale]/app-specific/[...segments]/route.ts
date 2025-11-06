import { NextResponse } from "next/server";

/**
 * Chrome DevTools автоматически опрашивает `/<locale>/app-specific/...`.
 * Возвращаем 204 и не проксируем запросы в API, иначе лог засыпает 429.
 */

export function GET() {
  return new NextResponse("", {
    status: 200,
    headers: {
      "Cache-Control": "public, max-age=3600",
    },
  });
}

export const dynamic = "force-static";
export const revalidate = 3600;

export function HEAD() {
  return GET();
}
