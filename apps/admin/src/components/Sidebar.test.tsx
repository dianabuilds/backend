import "@testing-library/jest-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import Sidebar from "./Sidebar";

vi.mock("../api/client", () => ({
  getAdminMenu: vi.fn(),
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: { role: "admin" },
    login: vi.fn(),
    logout: vi.fn(),
    ready: true,
  }),
}));

import { getAdminMenu } from "../api/client";

describe("Sidebar", () => {
  it("shows menu groups and workspaces item", async () => {
    (getAdminMenu as any).mockResolvedValue({
      items: [
        {
          id: "content",
          label: "Content",
          children: [
            { id: "nodes", label: "Nodes", path: "/nodes", order: 1 },
            { id: "quests", label: "Quests", path: "/quests", order: 2 },
          ],
        },
        {
          id: "navigation",
          label: "Navigation",
          children: [
            { id: "navigation-main", label: "Navigation", path: "/navigation", order: 1 },
            { id: "nav-transitions", label: "Transitions", path: "/transitions", order: 2 },
          ],
        },
        {
          id: "monitoring",
          label: "Monitoring",
          children: [
            { id: "dashboard", label: "Dashboard", path: "/", order: 1 },
            { id: "traces", label: "Traces", path: "/traces", order: 2 },
          ],
        },
        {
          id: "administration",
          label: "Administration",
          children: [
            { id: "users-list", label: "Users", path: "/users", order: 1 },
            { id: "workspaces", label: "Workspaces", path: "/workspaces", order: 2 },
          ],
        },
      ],
    });

    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Content")).toBeInTheDocument();
    expect(await screen.findByText("Navigation")).toBeInTheDocument();
    expect(await screen.findByText("Monitoring")).toBeInTheDocument();

    const adminBtn = await screen.findByRole("button", { name: "Administration" });
    fireEvent.click(adminBtn);

    expect(await screen.findByText("Workspaces")).toBeInTheDocument();
  });
});
