import "@testing-library/jest-dom";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { listFlags, updateFlag } from "../api/flags";
import FeatureFlagsPage from "./FeatureFlags";

vi.mock("../api/flags", () => ({
  listFlags: vi.fn(),
  updateFlag: vi.fn(),
}));

vi.mock("../workspace/WorkspaceContext", () => ({
  useWorkspace: () => ({ workspaceId: "" }),
}));

function renderPage() {
  render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <FeatureFlagsPage />
    </MemoryRouter>,
  );
}

describe("FeatureFlagsPage", () => {
  afterEach(() => vi.restoreAllMocks());

  it("filters flags by key", async () => {
    vi.mocked(listFlags).mockResolvedValue([
      { key: "a", value: false, description: "A", updated_at: null, updated_by: null },
      { key: "b", value: false, description: "B", updated_at: null, updated_by: null },
    ]);
    renderPage();
    await waitFor(() => screen.getByText("a"));
    fireEvent.change(screen.getByLabelText(/filter by key/i), {
      target: { value: "a" },
    });
    expect(screen.getByText("a")).toBeInTheDocument();
    expect(screen.queryByText("b")).not.toBeInTheDocument();
  });

  it("allows editing flag in modal", async () => {
    vi.mocked(listFlags).mockResolvedValue([
      { key: "test", value: false, description: "", updated_at: null, updated_by: null },
    ]);
    const updateSpy = vi.mocked(updateFlag).mockResolvedValue({
      key: "test",
      value: true,
      description: "new",
      updated_at: "2024-01-01T00:00:00Z",
      updated_by: "me",
    });
    renderPage();
    await waitFor(() => screen.getByText("test"));
    fireEvent.click(screen.getByText("test"));
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: "new" },
    });
    fireEvent.click(screen.getByLabelText(/enabled/i));
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith("test", {
        description: "new",
        value: true,
      }),
    );
  });

  it("renders referrals program flag", async () => {
    vi.mocked(listFlags).mockResolvedValue([
      { key: "referrals.program", value: false, description: "", updated_at: null, updated_by: null },
    ]);
    renderPage();
    await waitFor(() => screen.getByText("referrals.program"));
    expect(screen.getByText("referrals.program")).toBeInTheDocument();
  });
});
