function getCsrfToken(): string {
  const match = document.cookie.match(/XSRF-TOKEN=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

export async function apiFetch(
  input: RequestInfo,
  init: RequestInit = {},
  retry = true,
): Promise<Response> {
  const method = init.method?.toUpperCase() || "GET";
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    init.headers = {
      ...(init.headers || {}),
      "X-CSRF-Token": getCsrfToken(),
    } as Record<string, string>;
  }
  const resp = await fetch(input, { ...init, credentials: "include" });
  if (resp.status === 401 && retry) {
    const r = await fetch("/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
    if (r.ok) {
      return apiFetch(input, init, false);
    }
  }
  return resp;
}

