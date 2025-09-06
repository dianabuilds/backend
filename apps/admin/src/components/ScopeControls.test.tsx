import "@testing-library/jest-dom";

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AccountBranchProvider } from "../account/AccountContext";
import { getOverrideState } from "../shared/hooks/useOverrideStore";
import ScopeControls from "./ScopeControls";

const queryData: { data: unknown[] } = { data: [] };
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => queryData,
}));

describe("ScopeControls", () => {
  beforeEach(() => {
    queryData.data = [
      { id: "ws1", name: "One" },
      { id: "ws2", name: "Two" },
    ];
  });

  it("changes scope mode and space", () => {
    const handle = vi.fn();
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountBranchProvider>
          <ScopeControls scopeMode="member" onScopeModeChange={handle} roles={[]} onRolesChange={() => {}} />
        </AccountBranchProvider>
      </MemoryRouter>,
    );
    fireEvent.change(screen.getByTestId("scope-mode-select"), { target: { value: "global" } });
    expect(handle).toHaveBeenCalledWith("global");
    fireEvent.change(screen.getByTestId("account-select"), { target: { value: "ws2" } });
  });

  it("toggles override store", () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountBranchProvider>
          <ScopeControls scopeMode="member" onScopeModeChange={() => {}} roles={[]} onRolesChange={() => {}} />
        </AccountBranchProvider>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("override-toggle"));
    expect(getOverrideState().enabled).toBe(true);
    fireEvent.change(screen.getByTestId("override-reason"), { target: { value: "test" } });
    expect(getOverrideState().reason).toBe("test");
    fireEvent.click(screen.getByTestId("override-toggle"));
    expect(getOverrideState().enabled).toBe(false);
  });

  it("toggles roles", () => {
    const handle = vi.fn();
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountBranchProvider>
          <ScopeControls scopeMode="member" onScopeModeChange={() => {}} roles={[]} onRolesChange={handle} />
        </AccountBranchProvider>
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByTestId("role-admin"));
    expect(handle).toHaveBeenCalledWith(["admin"]);
  });
});

