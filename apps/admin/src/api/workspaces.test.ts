import { api } from "./client";
import { listWorkspaces } from "./workspaces";

vi.mock("./client", () => ({
  api: { get: vi.fn() },
}));

describe("listWorkspaces", () => {
  it("passes query params", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });
    await listWorkspaces({ q: "test", type: "team", limit: 5, offset: 10 });
    expect(api.get).toHaveBeenCalledWith(
      "/admin/workspaces?q=test&type=team&limit=5&offset=10",
    );
  });
});
