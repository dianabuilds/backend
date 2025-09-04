import "@testing-library/jest-dom";

import { render, screen } from "@testing-library/react";

import StatusCell, { type Status } from "./StatusCell";

describe("StatusCell", () => {
  const cases: [Status, string, string][] = [
    ["draft", "Draft", "text-gray-600"],
    ["in_review", "In review", "text-blue-600"],
    ["published", "Published", "text-green-600"],
    ["archived", "Archived", "text-red-600"],
  ];

  it.each(cases)(
    "renders %s status with proper icon and tooltip",
    (status, label, color) => {
      render(<StatusCell status={status} />);
      const el = screen.getByLabelText(label);
      expect(el).toBeInTheDocument();
      expect(el.tagName.toLowerCase()).toBe("svg");
      expect(el).toHaveAttribute("title", label);
      expect(el).toHaveClass(color);
    },
  );
});

