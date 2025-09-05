import { describe, expect, it, vi } from "vitest";

vi.mock("../lib/http", () => ({
  apiFetch: vi.fn().mockResolvedValue({ ok: true, status: 200 }),
}));

import { apiFetch } from "../lib/http";
import { sendRUM } from "./rum";

describe("sendRUM", () => {
  it("uses apiFetch when sendBeacon is unavailable", () => {
    sendRUM("test", { foo: "bar" });
    expect(apiFetch).toHaveBeenCalledWith("/metrics/rum", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: expect.any(String),
      keepalive: true,
    });

    const [, init] = (apiFetch as any).mock.calls[0];
    expect(JSON.parse(init.body)).toMatchObject({ event: "test", data: { foo: "bar" } });
  });
});
