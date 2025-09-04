/* eslint-disable simple-import-sort/imports */
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

vi.mock("../features/monitoring/RumTab", () => ({ default: () => <div>RUM</div> }));
vi.mock("../features/monitoring/RateLimitsTab", () => ({ default: () => <div>Rate</div> }));
vi.mock("../features/monitoring/CacheTab", () => ({ default: () => <div>Cache</div> }));
vi.mock("../features/monitoring/AuditLogTab", () => ({ default: () => <div>Audit</div> }));
vi.mock("../features/monitoring/JobsTab", () => ({ default: () => <div>Jobs</div> }));

import Monitoring from "./Monitoring";

describe("Monitoring dashboard", () => {
  it("renders all monitoring widgets", () => {
    render(<Monitoring />);
    expect(screen.getByText("RUM")).toBeInTheDocument();
    expect(screen.getByText("Rate")).toBeInTheDocument();
    expect(screen.getByText("Cache")).toBeInTheDocument();
    expect(screen.getByText("Audit")).toBeInTheDocument();
    expect(screen.getByText("Jobs")).toBeInTheDocument();
  });
});
