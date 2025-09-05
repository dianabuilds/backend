import "@testing-library/jest-dom";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { safeLocalStorage } from "../utils/safeStorage";
import { WorkspaceBranchProvider, useWorkspace } from "../workspace/WorkspaceContext";
import WorkspaceSelector from "./WorkspaceSelector";

const queryData = { data: [] as any[], error: null };
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => queryData,
}));

vi.mock("../api/client", () => ({
  api: { get: vi.fn() },
}));

describe("WorkspaceSelector", () => {
  beforeEach(() => {
    safeLocalStorage.clear();
    safeLocalStorage.setItem("workspaceId", "ws1");
    queryData.error = null;
    queryData.data = [
      { id: "ws1", name: "Workspace One", slug: "one", role: "owner" },
      { id: "ws2", name: "Workspace Two", slug: "two", role: "editor" },
    ];
  });

  it("switches workspace via keyboard", async () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <WorkspaceBranchProvider>
          <WorkspaceSelector />
        </WorkspaceBranchProvider>
      </MemoryRouter>,
    );
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    await waitFor(() => screen.getByPlaceholderText("Search workspace..."));
    fireEvent.keyDown(screen.getByPlaceholderText("Search workspace..."), {
      key: "ArrowDown",
    });
    fireEvent.keyDown(screen.getByPlaceholderText("Search workspace..."), {
      key: "Enter",
    });
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

  it("clears missing workspace", async () => {
    queryData.data = [];
    const ShowWs = () => {
      const { workspaceId } = useWorkspace();
      return <div data-testid="ws">{workspaceId}</div>;
    };
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <WorkspaceBranchProvider>
          <WorkspaceSelector />
          <ShowWs />
        </WorkspaceBranchProvider>
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getByTestId("ws").textContent).toBe(""),
    );
    expect(safeLocalStorage.getItem("workspaceId")).toBeNull();
  });

  it("shows login banner on error", () => {
    queryData.error = new Error("fail");
    queryData.data = undefined as any;
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <WorkspaceBranchProvider>
          <WorkspaceSelector />
        </WorkspaceBranchProvider>
      </MemoryRouter>,
    );
    screen.getByText("Не удалось загрузить список воркспейсов.");
    const link = screen.getByText("Авторизоваться");
    expect(link).toHaveAttribute("href", "/login");
  });
});
