import "@testing-library/jest-dom";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";

import NavigationManager from "./NavigationManager";
import {
  bulkUpdate,
  listTransitions,
  updateTransition,
} from "../api/transitions";

vi.mock("../api/transitions", () => ({
  listTransitions: vi.fn(),
  updateTransition: vi.fn(),
  bulkUpdate: vi.fn(),
  createTransition: vi.fn(),
}));

vi.mock("../components/LimitBadge", () => ({
  __esModule: true,
  default: () => <div />,
  handleLimit429: vi.fn(),
  refreshLimits: vi.fn(),
}));

vi.mock("./Simulation", () => ({
  __esModule: true,
  default: () => <div />,
}));

function renderPage() {
  const qc = new QueryClient();
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <NavigationManager />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("NavigationManager transitions", () => {
  afterEach(() => vi.restoreAllMocks());

  it("displays transitions list", async () => {
    vi.mocked(listTransitions).mockResolvedValue([
      { id: "1", from_slug: "a", to_slug: "b", label: "L", weight: 1 },
    ]);
    renderPage();
    await waitFor(() => expect(listTransitions).toHaveBeenCalled());
    expect(await screen.findByText("a")).toBeInTheDocument();
    expect(screen.getByDisplayValue("L")).toBeInTheDocument();
  });

  it("updates weight inline", async () => {
    vi.mocked(listTransitions).mockResolvedValue([
      { id: "1", from_slug: "a", to_slug: "b", label: "L", weight: 1 },
    ]);
    const updateSpy = vi.mocked(updateTransition).mockResolvedValue();
    renderPage();
    const weightInput = await screen.findByDisplayValue("1");
    fireEvent.change(weightInput, { target: { value: "5" } });
    fireEvent.blur(weightInput);
    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith("1", { weight: 5 }),
    );
  });

  it("bulk updates selected transitions", async () => {
    vi.mocked(listTransitions).mockResolvedValue([
      { id: "1", from_slug: "a", to_slug: "b", label: "L", weight: 1 },
      { id: "2", from_slug: "a", to_slug: "c", label: "M", weight: 2 },
    ]);
    const bulkSpy = vi.mocked(bulkUpdate).mockResolvedValue();
    renderPage();
    fireEvent.click(await screen.findByLabelText("select 1"));
    fireEvent.click(await screen.findByLabelText("select 2"));
    fireEvent.change(screen.getByPlaceholderText(/bulk label/i), {
      target: { value: "X" },
    });
    fireEvent.click(screen.getByRole("button", { name: /apply/i }));
    await waitFor(() =>
      expect(bulkSpy).toHaveBeenCalledWith(["1", "2"], { label: "X" }),
    );
  });
});

