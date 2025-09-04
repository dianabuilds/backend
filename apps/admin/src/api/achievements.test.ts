import { afterEach, describe, expect, it, vi } from "vitest";

import {
  grantAchievement,
  listAdminAchievements,
  revokeAchievement,
} from "./achievements";
import { api } from "./client";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("achievements api", () => {
  it("lists achievements with query params", async () => {
    vi.spyOn(api, "get").mockResolvedValue({ data: [] } as unknown);
    await listAdminAchievements({ q: "test", limit: 5, offset: 10 });
    expect(api.get).toHaveBeenCalledWith(
      "/admin/achievements?q=test&limit=5&offset=10",
    );
  });

  it("grants achievement", async () => {
    vi.spyOn(api, "post").mockResolvedValue({} as unknown);
    await grantAchievement("a1", "u1", "because");
    expect(api.post).toHaveBeenCalledWith(
      "/admin/achievements/a1/grant",
      { user_id: "u1", reason: "because" },
    );
  });

  it("revokes achievement", async () => {
    vi.spyOn(api, "post").mockResolvedValue({} as unknown);
    await revokeAchievement("a1", "u1");
    expect(api.post).toHaveBeenCalledWith(
      "/admin/achievements/a1/revoke",
      { user_id: "u1", reason: undefined },
    );
  });
});

