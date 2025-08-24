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

  it("shows active workspace indicator and updates on change", async () => {
    render(
      <MemoryRouter>
        <WorkspaceProvider>
          <WorkspaceSelector />
        </WorkspaceProvider>
      </MemoryRouter>,
    );

    const options = screen.getAllByRole("option");
    expect(options[0].textContent).toContain("Workspace One (active)");

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "ws2" } });

    await waitFor(() => {
      expect(screen.getAllByRole("option")[1].textContent).toContain(
        "Workspace Two (active)",
      );
    });

    const link = screen.getByTitle("Settings for Workspace Two");
    expect(link).toHaveAttribute("href", "/workspaces/ws2");
  });
});
