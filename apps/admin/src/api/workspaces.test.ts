import { api } from "./client";
import { listAccounts } from "./accounts";

vi.mock("./client", () => ({
  api: { get: vi.fn() },
}));

describe("listAccounts", () => {
  it("passes query params", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });
    await listAccounts({ q: "test", type: "team", limit: 5, offset: 10 });
    expect(api.get).toHaveBeenCalledWith(
      "/admin/accounts?q=test&type=team&limit=5&offset=10",
    );
  });
});
