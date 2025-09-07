import { api, type RequestOptions as ApiRequestOptions } from "./client";

export interface ProfileRequestOptions<P extends Record<string, unknown> = Record<string, never>>
  extends ApiRequestOptions {
  params?: P;
  raw?: boolean;
  /** Profile identifier to attach to the request. */
  profileId: string;
  /**
   * Configure profile ID handling. By default the ID is appended as
   * `profile_id` query parameter. Set to `false` to skip automatic
   * handling.
   */
  profile?: "query" | false;
}

async function request<
  T = unknown,
  P extends Record<string, unknown> = Record<string, never>,
>(url: string, opts: ProfileRequestOptions<P>): Promise<T> {
  const { params, headers: optHeaders, raw, profileId, profile = "query", ...rest } =
    opts as ProfileRequestOptions<P> & { raw?: boolean };

  const headers: Record<string, string> = {
    ...(optHeaders as Record<string, string> | undefined),
  };
  if (!Object.keys(headers).some((k) => k.toLowerCase() === "accept")) {
    headers["Accept"] = "application/json";
  }

  let finalUrl = url;
  const finalParams: Record<string, unknown> = { ...(params || {}) };
  if (profileId && profile === "query") {
    if (finalParams.profile_id === undefined) {
      finalParams.profile_id = profileId;
    }
  }

  if (Object.keys(finalParams).length > 0) {
    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(finalParams)) {
      if (value === undefined || value === null) continue;
      if (Array.isArray(value)) {
        for (const v of value) qs.append(key, String(v));
      } else {
        qs.set(key, String(value));
      }
    }
    const qsStr = qs.toString();
    if (qsStr) {
      finalUrl += (finalUrl.includes("?") ? "&" : "?") + qsStr;
    }
  }

  const res = await api.request<T>(finalUrl, { ...rest, headers });
  return raw ? res : (res.data as T);
}

export const profileApi = {
  request,
  get: <T = unknown, P extends Record<string, unknown> = Record<string, never>>(url: string, opts: ProfileRequestOptions<P>) =>
    request<T, P>(url, { ...opts, method: "GET" }),
  post: <
    TReq = unknown,
    TRes = unknown,
    P extends Record<string, unknown> = Record<string, never>,
  >(
    url: string,
    json?: TReq,
    opts: ProfileRequestOptions<P>,
  ) => request<TRes, P>(url, { ...opts, method: "POST", json }),
  put: <
    TReq = unknown,
    TRes = unknown,
    P extends Record<string, unknown> = Record<string, never>,
  >(
    url: string,
    json?: TReq,
    opts: ProfileRequestOptions<P>,
  ) => request<TRes, P>(url, { ...opts, method: "PUT", json }),
  patch: <
    TReq = unknown,
    TRes = unknown,
    P extends Record<string, unknown> = Record<string, never>,
  >(
    url: string,
    json?: TReq,
    opts: ProfileRequestOptions<P>,
  ) => request<TRes, P>(url, { ...opts, method: "PATCH", json }),
  delete: <T = unknown, P extends Record<string, unknown> = Record<string, never>>(url: string, opts: ProfileRequestOptions<P>) =>
    request<T, P>(url, { ...opts, method: "DELETE" }),
};

export const del = profileApi.delete;

export type { ProfileRequestOptions };

