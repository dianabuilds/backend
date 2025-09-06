import "@testing-library/jest-dom";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { listNodes } from "../api/nodes";
import Nodes from "./Nodes";

vi.mock("../api/nodes", () => ({
  listNodes: vi.fn(),
}));

vi.mock("../workspace/WorkspaceContext", () => ({
  useWorkspace: () => ({ workspaceId: "ws1" }),
}));

vi.mock("../components/ToastProvider", () => ({
  useToast: () => ({ addToast: vi.fn() }),
}));

vi.mock("../components/ScopeControls", () => ({
  default: () => <div />,
}));

function renderPage() {
  const qc = new QueryClient();
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Nodes />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Nodes page", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders space badge for node", async () => {
    vi.mocked(listNodes).mockResolvedValue([
      {
        id: 1,
        title: "One",
        slug: "one",
        status: "draft",
        is_visible: true,
        is_public: true,
        premium_only: false,
        is_recommendable: false,
        space: "alpha",
      },
    ]);

    renderPage();
    await waitFor(() => expect(listNodes).toHaveBeenCalled());
    expect(await screen.findByTestId("space-badge")).toHaveTextContent(
      "space:alpha",
    );
  });
});

