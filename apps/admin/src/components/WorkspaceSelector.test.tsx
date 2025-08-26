import "@testing-library/jest-dom";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { safeLocalStorage } from "../utils/safeStorage";
import { WorkspaceBranchProvider } from "../workspace/WorkspaceContext";
import WorkspaceSelector from "./WorkspaceSelector";

const queryData = { data: [] as any[] };
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => queryData,
}));

vi.mock("../api/client", () => ({
  api: { get: vi.fn() },
  setWorkspaceId: vi.fn(),
}));

describe("WorkspaceSelector", () => {
  beforeEach(() => {
    safeLocalStorage.clear();
    safeLocalStorage.setItem("workspaceId", "ws1");
    queryData.data = [
      { id: "ws1", name: "Workspace One" },
      { id: "ws2", name: "Workspace Two" },
    ];
  });

  it("supports quick switch", async () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <WorkspaceBranchProvider>
          <WorkspaceSelector />
        </WorkspaceBranchProvider>
      </MemoryRouter>,
    );
    const switchBtn = screen.getByTitle("Quick switch workspace");
    fireEvent.click(switchBtn);

    await waitFor(() => {
      const link = screen.getByTitle("Settings for Workspace Two");
      expect(link).toHaveAttribute("href", "/workspaces/ws2");
    });
  });

  it("shows create link when no workspaces", () => {
    queryData.data = [];
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <WorkspaceBranchProvider>
          <WorkspaceSelector />
        </WorkspaceBranchProvider>
      </MemoryRouter>,
    );
    const link = screen.getByText("Создать воркспейс");
    expect(link).toHaveAttribute("href", "/admin/workspaces");
  });
});
