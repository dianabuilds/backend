import { NextResponse } from "next/server";

/**
 * Chrome DevTools probes `/.well-known/...` and `/app-specific/com.chrome.devtools.json`
 * on every refresh. Витрина всё равно не отдаёт такие файлы, поэтому сразу отвечаем
 * пустым 204, чтобы не пробрасывать запросы в Site Editor API и не засорять логи.
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
