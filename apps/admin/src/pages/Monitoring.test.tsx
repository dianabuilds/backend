/* eslint-disable simple-import-sort/imports */
import "@testing-library/jest-dom";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("../features/monitoring/RumTab", () => ({ default: () => <div>RUM</div> }));
vi.mock("../features/monitoring/RateLimitsTab", () => ({ default: () => <div>Rate</div> }));
vi.mock("../features/monitoring/CacheTab", () => ({ default: () => <div>Cache</div> }));
vi.mock("../features/monitoring/AuditLogTab", () => ({ default: () => <div>Audit</div> }));
vi.mock("../features/monitoring/JobsTab", () => ({ default: () => <div>Jobs</div> }));

import Monitoring from "./Monitoring";

describe("Monitoring dashboard", () => {
  it("switches between monitoring sections", () => {
    render(<Monitoring />);
    const tabs = [
      { label: "Telemetry", content: "RUM" },
      { label: "Rate limits", content: "Rate" },
      { label: "Cache", content: "Cache" },
      { label: "Audit log", content: "Audit" },
      { label: "Jobs", content: "Jobs" },
    ];

    tabs.forEach(({ label }) => {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    });

    expect(screen.getByText("RUM")).toBeInTheDocument();

    tabs.slice(1).forEach(({ label, content }) => {
      fireEvent.click(screen.getByRole("button", { name: label }));
      expect(
        screen.getByText(content, { selector: "div" })
      ).toBeInTheDocument();
    });
  });
});
