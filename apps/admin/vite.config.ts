import react from "@vitejs/plugin-react";
import process from "node:process";
import { defineConfig, loadEnv, type ProxyOptions } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.VITE_API_BASE || "http://localhost:8000";

  const apiPrefixes = [
    "auth",
    "users",
    "nodes",
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

  // Точечные админские API (не перехватываем корневой /admin, чтобы SPA работала)
  proxy["/admin/echo"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/navigation"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/users"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/menu"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/dashboard"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/cache"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/ratelimit"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/restrictions"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/audit"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/metrics"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/notifications"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/ai"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/quests"] = {
    target: proxyTarget,
    changeOrigin: true,
    bypass(req) {
      const accept = req.headers["accept"] || "";
      if (typeof accept === "string" && accept.includes("text/html")) {
        return "/admin/index.html";
      }
    },
  };

  proxy["/admin/tags"] = {
    target: proxyTarget,
    changeOrigin: true,
    bypass(req) {
      const accept = req.headers["accept"] || "";
      if (typeof accept === "string" && accept.includes("text/html")) {
        return "/admin/index.html";
      }
    },
  };
  proxy["/admin/transitions"] = {
    target: proxyTarget,
    changeOrigin: true,
    bypass(req) {
      const accept = req.headers["accept"] || "";
      // Для навигации по SPA возвращаем индекс, а для JSON-запросов проксируем на backend
      if (typeof accept === "string" && accept.includes("text/html")) {
        return "/admin/index.html";
      }
    },
  };
  proxy["/admin/traces"] = {
    target: proxyTarget,
    changeOrigin: true,
    bypass(req) {
      const accept = req.headers["accept"] || "";
      if (typeof accept === "string" && accept.includes("text/html")) {
        return "/admin/index.html";
      }
    },
  };
  proxy["/admin/flags"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/nodes"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/achievements"] = { target: proxyTarget, changeOrigin: true };
  proxy["/admin/moderation"] = { target: proxyTarget, changeOrigin: true };

  // https://vite.dev/config/
  return {
    base: "/admin/",
    plugins: [react()],
    server: {
      port: 5173,
      strictPort: false,
      open: "/admin/",
      proxy,
    },
  };
});
