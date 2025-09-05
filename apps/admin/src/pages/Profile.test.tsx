import "@testing-library/jest-dom";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { api } from "../api/client";
import Profile from "./Profile";

vi.mock("../api/client", () => ({
  api: { get: vi.fn(), patch: vi.fn() },
}));

vi.mock("../workspace/WorkspaceContext", () => ({
  useWorkspace: () => ({ setWorkspace: vi.fn() }),
}));

vi.mock("../components/ToastProvider", () => ({
  useToast: () => ({ addToast: vi.fn() }),
}));

describe("Profile", () => {
  it("loads and saves default workspace via API", async () => {
    const workspaces = [{ id: "w1", name: "One" }];
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === "/workspaces") {
        return { data: workspaces } as unknown as { data: typeof workspaces };
      }
      if (url === "/users/me") {
        return {
          data: { default_workspace_id: "w1" },
        } as unknown as { data: { default_workspace_id: string } };
      }
      throw new Error("unknown url");
    });
    vi.mocked(api.patch).mockResolvedValue({} as unknown);

    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Profile />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() =>
      expect(
        (screen.getByLabelText(/default workspace/i) as HTMLSelectElement).value,
      ).toBe("w1"),
    );

    fireEvent.change(screen.getByLabelText(/default workspace/i), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByText(/save/i));
    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith(
        "/users/me/default-workspace",
        { default_workspace_id: null },
      ),
    );
  });
});
