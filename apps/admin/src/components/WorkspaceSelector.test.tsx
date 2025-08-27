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

vi.mock("../api/baseApi", () => ({
  baseApi: { get: vi.fn() },
}));

describe("WorkspaceSelector", () => {
  beforeEach(() => {
    safeLocalStorage.clear();
    safeLocalStorage.setItem("workspaceId", "ws1");
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
});
