import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { vi } from "vitest";

import { api } from "../api/client";
import Alerts from "./Alerts";

function renderPage() {
  const qc = new QueryClient();
  render(
    <QueryClientProvider client={qc}>
        <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Alerts />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  }

describe("Alerts page", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders alert entries and resolves them", async () => {
    vi.spyOn(api, "get").mockResolvedValue({
      data: {
        alerts: [
          {
            id: "1",
            startsAt: "2024-01-01T00:00:00Z",
            description: "boom",
            url: "http://example.com",
            type: "system",
            severity: "critical",
            status: "active",
          },
        ],
      },
    } as any);
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({} as any);
    renderPage();
    await waitFor(() => screen.getByText("boom"));
    expect(screen.getByText("boom")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /source/i }),
    ).toHaveAttribute("href", "http://example.com");
    fireEvent.click(screen.getByRole("button", { name: /mark resolved/i }));
    await waitFor(() => expect(postSpy).toHaveBeenCalled());
  });
});
