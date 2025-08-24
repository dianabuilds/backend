import "@testing-library/jest-dom";
import { act, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import LimitBadge, {
  refreshLimits,
  handleLimit429,
} from "./LimitBadge";
import { api } from "../api/client";

describe("LimitBadge", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("updates count and message", async () => {
    const getSpy = vi
      .spyOn(api, "get")
      .mockResolvedValueOnce({ data: { compass_calls: 5 } } as any)
      .mockResolvedValueOnce({ data: { compass_calls: 3 } } as any)
      .mockResolvedValueOnce({ data: { compass_calls: 3 } } as any)
      .mockResolvedValueOnce({ data: { compass_calls: 2 } } as any);

    render(<LimitBadge limitKey="compass_calls" />);

    await waitFor(() =>
      expect(screen.getByTestId("limit-compass_calls")).toHaveTextContent("5"),
    );

    await act(async () => {
      await refreshLimits();
    });
    await waitFor(() =>
      expect(screen.getByTestId("limit-compass_calls")).toHaveTextContent("3"),
    );

    await act(async () => {
      await handleLimit429("compass_calls", 9);
    });
    await waitFor(() =>
      expect(screen.getByTestId("limit-compass_calls")).toHaveAttribute(
        "title",
        "try again in 9s",
      ),
    );

    await act(async () => {
      await refreshLimits();
    });
    await waitFor(() =>
      expect(screen.getByTestId("limit-compass_calls")).toHaveTextContent("2"),
    );
    expect(screen.getByTestId("limit-compass_calls")).not.toHaveAttribute(
      "title",
    );
    expect(getSpy).toHaveBeenCalledTimes(4);
  });
});

