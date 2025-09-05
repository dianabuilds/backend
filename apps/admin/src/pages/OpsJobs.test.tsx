import "@testing-library/jest-dom";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { api } from "../api/client";
import Jobs from "./Jobs";

vi.mock("../api/client", () => ({ api: { get: vi.fn(), post: vi.fn() } }));

describe("Jobs page", () => {
  afterEach(() => vi.restoreAllMocks());

  it("loads jobs and retries", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        jobs: [
          { id: "1", name: "job", status: "failed", started_at: "2024-01-01T00:00:00Z" },
        ],
      },
    });
    vi.mocked(api.post).mockResolvedValue({ data: { status: "retried" } });
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Jobs />
      </MemoryRouter>
    );
    await waitFor(() => screen.getByText("job"));
    fireEvent.click(screen.getByRole("button", { name: "Перезапустить" }));
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith("/admin/ops/jobs/1/retry")
    );
  });
});
