import { cookies } from "next/headers";
import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

import { normalizeLocale } from "@/config/i18n";

const sansFont = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const monoFont = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

const siteOrigin =
  process.env.NEXT_PUBLIC_SITE_ORIGIN ??
  process.env.SITE_ORIGIN ??
  "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteOrigin),
  title: {
    default: "Site Platform",
    template: "%s — Site Platform",
  },
  description:
    "Новая витрина и редактор сайта на Next.js. Сборка для миграции с Vite.",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = await cookies();
  const localeCookie = cookieStore.get("NEXT_LOCALE")?.value;
  const lang = normalizeLocale(localeCookie);

  return (
    <html lang={lang} suppressHydrationWarning>
      <body className={`${sansFont.variable} ${monoFont.variable}`}>
        {children}
      </body>
    </html>
  );
}
