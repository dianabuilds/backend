import process from "node:process";

import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv, type ProxyOptions } from "vite";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.VITE_API_BASE || "http://localhost:8000";

  const apiPrefixes = [
    "auth",
    "users",
    "nodes",
    "content",
    "tags",
    "moderation",
    "transitions",
    "navigation",
    "notifications",
    "quests",
    "traces",
    "achievements",
    "payments",
    "search",
    "media", // upload endpoint (cover/images)
  ];

  const proxy = apiPrefixes.reduce<Record<string, ProxyOptions>>(
    (acc, prefix) => {
      acc[`/${prefix}`] = {
        target: proxyTarget,
        changeOrigin: true,
        ...(prefix === "notifications" ? { ws: true } : {}),
      };
      return acc;
    },
    {},
  );

  // Admin API endpoints that share paths with the SPA. For HTML navigation requests
  // we need to serve the SPA index instead of proxying to the backend.
  const adminPrefixes = [
    "echo",
    "navigation",
    "users",
    "menu",
    "dashboard",
    "cache",
    "ratelimit",
    "restrictions",
    "audit",
    "metrics",
    "notifications",
    "ai",
    "quests",
    "tags",
    "transitions",
    "traces",
    "flags",
    "nodes",
    "content",
    "achievements",
    "moderation",
    "ops",
    "accounts",
  ];

  const htmlBypass = (req: { headers: Record<string, string | undefined> }) => {
    const accept = req.headers["accept"] || "";
    if (typeof accept === "string" && accept.includes("text/html")) {
      // In dev, our base is "/", so index lives at "/index.html"
      return "/index.html";
    }
  };

  adminPrefixes.forEach((p) => {
    proxy[`/admin/${p}`] = {
      target: proxyTarget,
      changeOrigin: true,
      ...(p === "notifications" ? { ws: true } : {}),
      bypass: htmlBypass,
    };
  });

  // Ensure root /admin and /admin/ are handled by SPA fallback in dev
  proxy["/admin"] = {
    target: proxyTarget,
    changeOrigin: true,
    bypass: htmlBypass,
  };
  proxy["/admin/"] = {
    target: proxyTarget,
    changeOrigin: true,
    bypass: htmlBypass,
  };

  // В dev base="/" (модули и /@vite/client отдаются с корня), в build — "/admin/"
  const base = command === "build" ? "/admin/" : "/";

  // Dev-only middleware: serve index.html for any HTML navigation (/, /admin, /admin/*, etc.)
  // This avoids the classic "Cannot GET /admin" when proxying.
  const spaFallback = () => ({
    name: "admin-spa-fallback",
    configureServer(server: any) {
      server.middlewares.use(async (req: any, res: any, next: any) => {
        try {
          const url = (req.url as string) || "";
          const accept = (req.headers?.accept as string) || "";
          const isHtml = accept.includes("text/html");
          // Skip Vite internals and static assets
          if (!isHtml || url.startsWith("/@vite") || url.startsWith("/assets") || url.startsWith("/src")) {
            return next();
          }
          // For any other HTML navigation, serve the app index
          if (isHtml) {
            const indexPath = resolve(server.config.root, "index.html");
            const raw = readFileSync(indexPath, "utf-8");
            const html = await server.transformIndexHtml(url, raw);
            res.setHeader("Content-Type", "text/html");
            res.statusCode = 200;
            res.end(html);
            return;
          }
        } catch {
          // fall through
        }
        next();
      });
    },
  });

  // https://vite.dev/config/
  return {
    base,
    // Ensure our SPA fallback middleware is registered first in dev
    plugins: [...(command === "serve" ? [spaFallback()] : []), react()],
    server: {
      port: 5173,
      strictPort: false,
      open: "/admin/",
      proxy,
    },
  };
});
