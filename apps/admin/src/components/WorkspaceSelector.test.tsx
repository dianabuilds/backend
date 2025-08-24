import "@testing-library/jest-dom";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WorkspaceProvider } from "../workspace/WorkspaceContext";
import WorkspaceSelector from "./WorkspaceSelector";

vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({
    data: [
      { id: "ws1", name: "Workspace One" },
      { id: "ws2", name: "Workspace Two" },
    ],
  }),
}));

vi.mock("../api/client", () => ({
  api: { get: vi.fn() },
  setWorkspaceId: vi.fn(),
}));

describe("WorkspaceSelector", () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem("workspaceId", "ws1");
  });

  it("supports quick switch", async () => {
      render(
        <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <WorkspaceProvider>
            <WorkspaceSelector />
          </WorkspaceProvider>
        </MemoryRouter>,
      );
    const switchBtn = screen.getByTitle("Quick switch workspace");
    fireEvent.click(switchBtn);

    await waitFor(() => {
      const link = screen.getByTitle("Settings for Workspace Two");
      expect(link).toHaveAttribute("href", "/workspaces/ws2");
    });
  });
});
