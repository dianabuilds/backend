import "@testing-library/jest-dom";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Mock } from "vitest";

import { api } from "../api/client";
import { safeLocalStorage } from "../utils/safeStorage";
import { WorkspaceBranchProvider, useWorkspace } from "./WorkspaceContext";

vi.mock("../api/client", () => ({
  api: { get: vi.fn() },
}));

function ShowWorkspace() {
  const { workspaceId } = useWorkspace();
  return <div data-testid="ws">{workspaceId}</div>;
}

describe("WorkspaceBranchProvider", () => {
  beforeEach(() => {
    safeLocalStorage.clear();
    (api.get as Mock).mockReset();
  });

  it("uses server default workspace", async () => {
    (api.get as Mock).mockImplementation(async (url: string) => {
      if (url === "/users/me") return { data: { default_workspace_id: "did" } } as any;
      throw new Error("unknown url");
    });
    render(
      <WorkspaceBranchProvider>
        <ShowWorkspace />
      </WorkspaceBranchProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("ws").textContent).toBe("did"));
    expect(api.get).toHaveBeenCalledWith("/users/me");
  });
});
