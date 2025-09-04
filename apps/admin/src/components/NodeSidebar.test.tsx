import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import NodeSidebar from "./NodeSidebar";

vi.mock("../api/flags", () => ({
  listFlags: vi.fn().mockResolvedValue([]),
}));

vi.mock("../api/nodes", () => ({
  patchNode: vi.fn().mockResolvedValue({}),
}));

vi.mock("../api/wsApi", () => ({
  wsApi: { request: vi.fn() },
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ user: { role: "admin" } }),
}));

vi.mock("../utils/compressImage", () => ({
  compressImage: vi.fn(),
}));

describe("NodeSidebar", () => {
  const node = {
    id: "1",
    slug: "node-1",
    authorId: "user",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    isPublic: true,
    publishedAt: null,
    nodeType: "text",
    coverUrl: null,
    coverAssetId: null,
    coverAlt: "",
    coverMeta: null,
    allowFeedback: true,
    premiumOnly: false,
  };

  it("does not render Advanced section", async () => {
    render(<NodeSidebar node={node} workspaceId="ws" />);
    await screen.findByText("Metadata");
    expect(screen.queryByText("Advanced")).toBeNull();
  });
});

