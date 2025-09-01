import { describe, it, expect, vi } from "vitest";

vi.mock("../../api/client", () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from "../../api/client";
import { client } from "./client";

describe("client", () => {
  it("throws Error with response.detail", async () => {
    (apiFetch as any).mockResolvedValue({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      headers: { get: () => "application/json" },
      json: async () => ({ detail: "invalid" }),
    });

    await expect(client.get("/foo")).rejects.toThrow("invalid");
  });
});
