import "@testing-library/jest-dom";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import { addAttachment, getCaseFull, patchLabels } from "../api/moderationCases";
import ModerationCase from "./ModerationCase";

vi.mock("../api/moderationCases", () => ({
  getCaseFull: vi.fn(),
  addNote: vi.fn(),
  patchLabels: vi.fn(),
  addAttachment: vi.fn(),
  closeCase: vi.fn(),
}));

vi.mock("../account/AccountContext", () => ({
  useAccount: () => ({ accountId: "" }),
}));

function renderPage() {
  render(
    <MemoryRouter
      initialEntries={["/moderation/cases/1"]}
      future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
    >
      <Routes>
        <Route path="/moderation/cases/:id" element={<ModerationCase />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ModerationCase", () => {
  afterEach(() => vi.restoreAllMocks());

  it("allows adding labels and attachments", async () => {
    vi.mocked(getCaseFull).mockResolvedValue({
      case: {
        id: "1",
        type: "support_request",
        status: "new",
        priority: "P1",
        summary: "s",
        labels: [],
        target_type: null,
        target_id: null,
        assignee_id: null,
      },
      notes: [],
      attachments: [],
      events: [],
    });
    renderPage();
    await waitFor(() => screen.getByText(/Details/i));
    fireEvent.change(screen.getByPlaceholderText("Add label"), {
      target: { value: "bug" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add label/i }));
    await waitFor(() =>
      expect(patchLabels).toHaveBeenCalledWith("1", { add: ["bug"] }),
    );
    fireEvent.change(screen.getByPlaceholderText("Attachment URL"), {
      target: { value: "http://x" },
    });
    fireEvent.click(screen.getByRole("button", { name: /upload/i }));
    await waitFor(() =>
      expect(addAttachment).toHaveBeenCalledWith("1", { url: "http://x" }),
    );
  });
});
