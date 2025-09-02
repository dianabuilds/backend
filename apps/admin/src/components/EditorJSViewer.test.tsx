import "@testing-library/jest-dom";
import { render } from "@testing-library/react";

import EditorJSViewer from "./EditorJSViewer";

describe("EditorJSViewer", () => {
  it("strips scripts and event handlers", () => {
    const data = {
      blocks: [
        {
          type: "paragraph",
          data: {
            text: 'hello<img src="x" onerror="alert(1)"><script>alert("x")</script>',
          },
        },
      ],
    };
    const { container } = render(<EditorJSViewer value={data} />);
    expect(container.querySelector("script")).toBeNull();
    const img = container.querySelector("img");
    expect(img).not.toHaveAttribute("onerror");
  });
});
