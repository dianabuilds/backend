import "./index.css";
// Ensure TS picks up our type augmentations (custom DOM attributes like onCommit)
import "./types/react-augment.d.ts";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App.tsx";

const routeId = (window as any).__ROUTE_ID__;
console.log("route_id:", routeId);
if (import.meta.env.DEV) {
  const overlay = document.createElement("div");
  overlay.style.position = "fixed";
  overlay.style.bottom = "0";
  overlay.style.right = "0";
  overlay.style.background = "rgba(0,0,0,0.6)";
  overlay.style.color = "white";
  overlay.style.padding = "2px 4px";
  overlay.style.fontSize = "12px";
  overlay.style.zIndex = "9999";
  overlay.textContent = `route_id: ${routeId ?? "unknown"}`;
  document.body.appendChild(overlay);
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
