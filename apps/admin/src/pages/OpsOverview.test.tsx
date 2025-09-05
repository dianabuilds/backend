import "@testing-library/jest-dom";

import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { api } from "../api/client";
import OpsOverview from "./OpsOverview";

vi.mock("../api/client", () => ({ api: { get: vi.fn() } }));

describe("OpsOverview page", () => {
  afterEach(() => vi.restoreAllMocks());

  it("loads overview data", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { uptime: 1 } });
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <OpsOverview />
      </MemoryRouter>
    );
    await waitFor(() => expect(api.get).toHaveBeenCalled());
    expect(api.get).toHaveBeenCalledWith("/admin/ops/overview");
    await waitFor(() => screen.getByText(/uptime/i));
  });
});
