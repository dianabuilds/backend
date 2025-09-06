import process from "node:process";

import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv, type ProxyOptions } from "vite";

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
    const mode = req.headers["sec-fetch-mode"] || "";
    const dest = req.headers["sec-fetch-dest"] || "";
    const isDocumentNavigation = mode === "navigate" || dest === "document";
    if (isDocumentNavigation && typeof accept === "string" && accept.includes("text/html")) {
      return "/admin/index.html";
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

  // В dev base="/" (модули и /@vite/client отдаются с корня), в build — "/admin/"
  const base = command === "build" ? "/admin/" : "/";

  // https://vite.dev/config/
  return {
    base,
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: false,
      open: "/admin/",
      proxy,
    },
  };
});
