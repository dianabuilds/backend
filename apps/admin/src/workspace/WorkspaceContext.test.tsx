import "@testing-library/jest-dom";

import { render, screen, waitFor } from "@testing-library/react";
import type { Mock } from "vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../api/client";
import type { Workspace } from "../api/types";
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
    window.history.replaceState({}, "", "/");
  });

  it("uses server default workspace", async () => {
    (api.get as Mock).mockImplementation(async (url: string) => {
      if (url === "/users/me")
        return { data: { default_workspace_id: "did" } };
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
  it("falls back to global account", async () => {
    (api.get as Mock).mockImplementation(async (url: string) => {
      if (url === "/users/me") return { data: { default_workspace_id: null } };
      if (url === "/accounts") {
        const accounts: Workspace[] = [
          { id: "gid", slug: "global", type: "global" },
        ];
        return { data: accounts };
      }
      throw new Error("unknown url");
    });
    render(
      <WorkspaceBranchProvider>
        <ShowWorkspace />
      </WorkspaceBranchProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("ws").textContent).toBe("gid"));
    expect(api.get).toHaveBeenCalledWith("/accounts");
  });
});
