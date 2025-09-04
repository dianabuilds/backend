import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { listCases } from "../api/moderationCases";
import ModerationInbox from "./ModerationInbox";

vi.mock("../api/moderationCases", () => ({
  listCases: vi.fn(),
  createCase: vi.fn(),
}));

vi.mock("../workspace/WorkspaceContext", () => ({
  useWorkspace: () => ({ workspaceId: "" }),
}));

function renderPage() {
  render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <ModerationInbox />
    </MemoryRouter>,
  );
}

describe("ModerationInbox", () => {
  afterEach(() => vi.restoreAllMocks());

  it("applies filters when loading", async () => {
    vi.mocked(listCases).mockResolvedValue({ items: [], page: 1, size: 50, total: 0 });
    renderPage();
    await waitFor(() => expect(listCases).toHaveBeenCalled());
    fireEvent.change(screen.getByPlaceholderText("Search..."), { target: { value: "foo" } });
    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[0], { target: { value: "new" } });
    fireEvent.change(selects[1], { target: { value: "support_request" } });
    fireEvent.change(selects[2], { target: { value: "P1" } });
    fireEvent.click(screen.getByRole("button", { name: /apply/i }));
    await waitFor(() =>
      expect(listCases).toHaveBeenLastCalledWith({
        q: "foo",
        status: "new",
        type: "support_request",
        priority: "P1",
        page: 1,
        size: 50,
      }),
    );
  });
});
