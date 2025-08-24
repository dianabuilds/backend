// Minimal type shims for Editor.js tools without TypeScript definitions.
// This allows dynamic imports like `import("@editorjs/checklist")` to type-check.
import type { ToolConstructable } from "@editorjs/editorjs";

// Editor.js output structures used across the admin app
export interface OutputData {
  time?: number;
  version?: string;
  blocks: Block[];
}

export type Block =
  | ParagraphBlock
  | HeaderBlock
  | ListBlock
  | ImageBlock
  | ChecklistBlock
  | QuoteBlock
  | TableBlock
  | DelimiterBlock;

interface BaseBlock<T extends string, D> {
  id?: string;
  type: T;
  data: D;
}

export type ParagraphBlock = BaseBlock<"paragraph", { text: string }>;

export type HeaderBlock = BaseBlock<
  "header",
  { text: string; level?: number }
>;

export type ListBlock = BaseBlock<
  "list",
  { style?: "ordered" | "unordered"; items: Array<string | { content?: string; text?: string }> }
>;

export type ImageBlock = BaseBlock<
  "image",
  {
    file?: { url: string };
    url?: string;
    caption?: string;
    withBorder?: boolean;
    withBackground?: boolean;
    stretched?: boolean;
  }
>;

export type ChecklistBlock = BaseBlock<
  "checklist",
  { items: Array<{ text?: string; checked?: boolean }> }
>;

export type QuoteBlock = BaseBlock<
  "quote",
  { text: string; caption?: string }
>;

export type TableBlock = BaseBlock<
  "table",
  { content: unknown[][] }
>;

export type DelimiterBlock = BaseBlock<"delimiter", Record<string, never>>;

declare module "@editorjs/checklist" {
  const Checklist: ToolConstructable;
  export default Checklist;
}

declare module "@editorjs/image" {
  const ImageTool: ToolConstructable;
  export default ImageTool;
}

declare module "@editorjs/table" {
  const Table: ToolConstructable;
  export default Table;
}

declare module "@editorjs/quote" {
  const Quote: ToolConstructable;
  export default Quote;
}

declare module "@editorjs/delimiter" {
  const Delimiter: ToolConstructable;
  export default Delimiter;
}

declare module "@editorjs/list" {
  const List: ToolConstructable;
  export default List;
}

declare module "@editorjs/header" {
  const Header: ToolConstructable;
  export default Header;
}
