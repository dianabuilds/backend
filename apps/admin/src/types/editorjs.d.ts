// Minimal type shims for Editor.js tools without TypeScript definitions.
// This allows dynamic imports like `import("@editorjs/checklist")` to type-check.

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
