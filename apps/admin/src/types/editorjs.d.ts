// Minimal type shims for Editor.js tools without TypeScript definitions.
// This allows dynamic imports like `import("@editorjs/checklist")` to type-check.

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
  | ImageBlock;

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

declare module "@editorjs/checklist" {
  const Checklist: any;
  export default Checklist;
}

declare module "@editorjs/image" {
  const ImageTool: any;
  export default ImageTool;
}

declare module "@editorjs/table" {
  const Table: any;
  export default Table;
}

declare module "@editorjs/quote" {
  const Quote: any;
  export default Quote;
}

declare module "@editorjs/delimiter" {
  const Delimiter: any;
  export default Delimiter;
}

declare module "@editorjs/list" {
  const List: any;
  export default List;
}

declare module "@editorjs/header" {
  const Header: any;
  export default Header;
}
