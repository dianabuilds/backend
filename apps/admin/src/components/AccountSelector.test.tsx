import "@testing-library/jest-dom";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AccountBranchProvider, useAccount } from "../account/AccountContext";
import { safeLocalStorage } from "../utils/safeStorage";
import AccountSelector from "./AccountSelector";

const queryData = { data: [] as any[], error: null };
vi.mock("@tanstack/react-query", () => ({
  useQuery: () => queryData,
}));

vi.mock("../api/client", () => ({
  api: { get: vi.fn() },
}));

describe("AccountSelector", () => {
  beforeEach(() => {
    safeLocalStorage.clear();
    safeLocalStorage.setItem("accountId", "ws1");
    queryData.error = null;
    queryData.data = [
      { id: "ws1", name: "Account One", slug: "one", role: "owner" },
      { id: "ws2", name: "Account Two", slug: "two", role: "editor" },
    ];
  });

  it("switches account via keyboard", async () => {
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountBranchProvider>
          <AccountSelector />
        </AccountBranchProvider>
      </MemoryRouter>,
    );
    fireEvent.keyDown(document, { key: "k", ctrlKey: true });
    await waitFor(() => screen.getByPlaceholderText("Search account..."));
    fireEvent.keyDown(screen.getByPlaceholderText("Search account..."), {
      key: "ArrowDown",
    });
    fireEvent.keyDown(screen.getByPlaceholderText("Search account..."), {
      key: "Enter",
    });
    await waitFor(() => {
      const link = screen.getByTitle("Settings for Account Two");
      expect(link).toHaveAttribute("href", "/accounts/ws2");
    });
  });

  it("shows create link when no accounts", () => {
    queryData.data = [];
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountBranchProvider>
          <AccountSelector />
        </AccountBranchProvider>
      </MemoryRouter>,
    );
    const link = screen.getByText("Создать аккаунт");
    expect(link).toHaveAttribute("href", "/accounts");
  });

  it("clears missing account", async () => {
    queryData.data = [];
    const ShowAccount = () => {
      const { accountId } = useAccount();
      return <div data-testid="account">{accountId}</div>;
    };
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountBranchProvider>
          <AccountSelector />
          <ShowAccount />
        </AccountBranchProvider>
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getByTestId("account").textContent).toBe(""),
    );
    expect(safeLocalStorage.getItem("accountId")).toBeNull();
  });

  it("shows login banner on error", () => {
    queryData.error = new Error("fail");
    queryData.data = undefined as any;
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountBranchProvider>
          <AccountSelector />
        </AccountBranchProvider>
      </MemoryRouter>,
    );
    screen.getByText("Не удалось загрузить список аккаунтов.");
    const link = screen.getByText("Авторизоваться");
    expect(link).toHaveAttribute("href", "/login");
  });
});
