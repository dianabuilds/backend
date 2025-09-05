// Lightweight RUM helpers: send navigation timings and custom events to backend
import { apiFetch } from "../lib/http";

type RUMPayload = Record<string, unknown>;

const RUM_ENDPOINT = "/metrics/rum";

export function sendRUM(event: string, data: RUMPayload = {}): void {
  try {
    const payload = JSON.stringify({
      event,
      ts: Date.now(),
      url: typeof location !== "undefined" ? location.pathname + location.search : "",
      data,
    });
    if (typeof navigator !== "undefined" && "sendBeacon" in navigator) {
      const blob = new Blob([payload], { type: "application/json" });
      (navigator as Navigator & { sendBeacon?: (url: string, data: BodyInit) => void }).sendBeacon?.(RUM_ENDPOINT, blob);
    } else {
      void apiFetch(RUM_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true,
      })
        .then((response) => {
          if (!response.ok) {
            console.error(`RUM request failed with status ${response.status}`);
            switch (response.status) {
              case 405:
                console.error("RUM endpoint method not allowed");
                break;
              case 422:
                console.error("RUM payload validation failed");
                break;
              case 500:
                console.error("RUM internal server error");
                break;
            }
          }
        })
        .catch((error) => {
          console.error("RUM request error", error);
        });
    }
  } catch (error) {
    console.error("Unexpected error sending RUM", error);
  }
}

function sendNavigation() {
  try {
    const nav = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    if (!nav) return;
    sendRUM("navigation", {
      type: nav.type,
      startTime: nav.startTime,
      duration: nav.duration,
      transferSize: (nav as unknown as { transferSize?: number }).transferSize ?? null,
      ttfb: nav.responseStart - nav.requestStart,
      domContentLoaded: nav.domContentLoadedEventEnd - nav.startTime,
      loadEvent: nav.loadEventEnd - nav.startTime,
      // milestones
      redirect: nav.redirectEnd - nav.redirectStart,
      dns: nav.domainLookupEnd - nav.domainLookupStart,
      connect: nav.connectEnd - nav.connectStart,
      request: nav.responseStart - nav.requestStart,
      response: nav.responseEnd - nav.responseStart,
    });
  } catch {
    // ignore
  }
}

function sendFirstInteraction() {
  try {
    sendRUM("first-interaction", { tti: performance.now() });
  } catch {
    // ignore
  }
}

// Auto-send navigation timings after full load and measure first interaction
if (typeof window !== "undefined") {
  if (document.readyState === "complete") {
    setTimeout(sendNavigation, 0);
  } else {
    window.addEventListener("load", () => setTimeout(sendNavigation, 0), { once: true });
  }
  const onFirstInput = () => {
    window.removeEventListener("pointerdown", onFirstInput);
    window.removeEventListener("keydown", onFirstInput);
    sendFirstInteraction();
  };
  window.addEventListener("pointerdown", onFirstInput, { once: true });
  window.addEventListener("keydown", onFirstInput, { once: true });
}
