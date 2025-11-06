import { NextResponse } from "next/server";

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
