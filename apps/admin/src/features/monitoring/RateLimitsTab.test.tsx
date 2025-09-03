import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { api } from "../../api/client";
import RateLimitsTab from "./RateLimitsTab";

describe("RateLimitsTab", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("displays status and saves rule", async () => {
    vi.spyOn(api, "get").mockImplementation((url: string) => {
      if (url === "/admin/ratelimit/rules") {
        return Promise.resolve({
          data: { enabled: true, rules: { foo: "5/min" } },
        } as any);
      }
      if (url === "/admin/ratelimit/recent429") {
        return Promise.resolve({ data: [] } as any);
      }
      throw new Error("unexpected url " + url);
    });
    const patch = vi.spyOn(api, "patch").mockResolvedValue({} as any);

    render(<RateLimitsTab />);

    await screen.findByText("Enabled");
    const input = await screen.findByDisplayValue("5/min");
    fireEvent.change(input, { target: { value: "10/min" } });
    fireEvent.click(screen.getByText("Save"));

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith("/admin/ratelimit/rules", {
        key: "foo",
        rule: "10/min",
      }),
    );
  });
});

