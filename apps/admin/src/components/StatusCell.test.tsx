import "@testing-library/jest-dom";

import { render, screen } from "@testing-library/react";

import StatusCell from "./StatusCell";

describe("StatusCell", () => {
  it("highlights active status icon", () => {
    render(<StatusCell status="published" />);
    expect(screen.getByLabelText("Published")).toHaveClass("text-green-600");
    expect(screen.getByLabelText("Draft")).toHaveClass("text-gray-400");
  });
});

