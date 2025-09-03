import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("../features/monitoring/RumTab", () => ({ default: () => <div>RUM</div> }));
vi.mock("../features/monitoring/RateLimitsTab", () => ({ default: () => <div>Rate</div> }));
vi.mock("../features/monitoring/CacheTab", () => ({ default: () => <div>Cache</div> }));
vi.mock("../features/monitoring/AuditLogTab", () => ({ default: () => <div>Audit</div> }));
vi.mock("../features/monitoring/JobsTab", () => ({ default: () => <div>Jobs</div> }));

import Monitoring from "./Monitoring";

describe("Monitoring tabs", () => {
  it("exposes proper ARIA attributes", () => {
    render(<Monitoring />);
    const tablist = screen.getByRole("tablist");
    expect(tablist).toBeInTheDocument();
    const rumTab = screen.getByRole("tab", { name: "RUM" });
    expect(rumTab).toHaveAttribute("aria-controls", "rum-panel");
    expect(rumTab).toHaveAttribute("aria-selected", "true");
  });

  it("switches tabs with arrow keys", () => {
    render(<Monitoring />);
    const rumTab = screen.getByRole("tab", { name: "RUM" });
    rumTab.focus();
    fireEvent.keyDown(rumTab, { key: "ArrowRight" });
    const rateTab = screen.getByRole("tab", { name: "Rate limits" });
    expect(rateTab).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(rateTab, { key: "ArrowLeft" });
    expect(rumTab).toHaveAttribute("aria-selected", "true");
  });
});
