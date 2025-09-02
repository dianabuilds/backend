import { setPreviewToken } from "../api/client";

/**
 * Parse preview token from URL (?token=... or ?previewToken=...) or hash fragment
 * and store it via setPreviewToken so that X-Preview-Token header is sent.
 * Optionally removes the token from the visible URL using history.replaceState.
 */
export function initPreviewTokenFromUrl(): void {
  try {
    const loc = window.location;
    const url = new URL(loc.href);

    const getToken = (): string | null => {
      let t = url.searchParams.get("token") || url.searchParams.get("previewToken");
      if (t) return t;
      // Also try hash part like #token=...
      if (url.hash && url.hash.includes("=")) {
        const hashParams = new URLSearchParams(url.hash.replace(/^#/, ""));
        t = hashParams.get("token") || hashParams.get("previewToken");
        if (t) return t;
      }
      return null;
    };

    const token = getToken();
    if (!token) return;

    // Save token for this session
    setPreviewToken(token);

    // Clean the URL by removing token params from both search and hash
    url.searchParams.delete("token");
    url.searchParams.delete("previewToken");
    if (url.hash) {
      const hashParams = new URLSearchParams(url.hash.replace(/^#/, ""));
      hashParams.delete("token");
      hashParams.delete("previewToken");
      const nextHash = hashParams.toString();
      url.hash = nextHash ? "#" + nextHash : "";
    }

    const cleaned = url.pathname + (url.search ? url.search : "") + (url.hash ? url.hash : "");
    if (cleaned !== loc.pathname + loc.search + loc.hash) {
      window.history.replaceState(null, document.title, cleaned);
    }
  } catch {
    // no-op
  }
}
