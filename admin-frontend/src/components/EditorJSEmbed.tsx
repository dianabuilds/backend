import { useEffect, useRef } from "react";

type EditorData = any;

interface Props {
  value?: EditorData;
  onChange?: (data: EditorData) => void;
  className?: string;
  minHeight?: number;
  placeholder?: string;
}

export default function EditorJSEmbed({ value, onChange, className, minHeight = 220, placeholder }: Props) {
  const holderId = useRef(`edjs-${Math.random().toString(36).slice(2)}`);
  const editorRef = useRef<any>(null);
  const changeTimer = useRef<number | null>(null);

  useEffect(() => {
    let destroyed = false;

    async function init() {
      const EditorJS = (await import("@editorjs/editorjs")).default as any;
      const Header = (await import("@editorjs/header")).default as any;
      const List = (await import("@editorjs/list")).default as any;
      const Checklist = (await import("@editorjs/checklist")).default as any;
      const ImageTool = (await import("@editorjs/image")).default as any;
      const Table = (await import("@editorjs/table")).default as any;
      const Quote = (await import("@editorjs/quote")).default as any;
      const Delimiter = (await import("@editorjs/delimiter")).default as any;

      if (destroyed) return;

      const instance = new EditorJS({
        holder: holderId.current,
        minHeight,
        placeholder: placeholder || "Напишите описание, легенду или сценарий…",
        data: value || { time: Date.now(), blocks: [{ type: "paragraph", data: { text: "" } }], version: "2.30.7" },
        tools: {
          header: Header,
          list: List,
          checklist: Checklist,
          table: Table,
          quote: Quote,
          delimiter: Delimiter,
          image: {
            class: ImageTool,
            config: {
              uploader: {
                uploadByFile(file: File) {
                  return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = () => resolve({ success: 1, file: { url: String(reader.result) } });
                    reader.onerror = reject;
                    reader.readAsDataURL(file);
                  });
                },
              },
            },
          },
        },
        onChange: async () => {
          if (!onChange) return;
          if (changeTimer.current) window.clearTimeout(changeTimer.current);
          changeTimer.current = window.setTimeout(async () => {
            try {
              const data = await instance.save();
              onChange(data);
            } catch {
              // ignore
            }
          }, 400);
        },
      });

      editorRef.current = instance;
    }

    init();

    return () => {
      destroyed = true;
      if (changeTimer.current) window.clearTimeout(changeTimer.current);
      if (editorRef.current && editorRef.current.destroy) {
        editorRef.current.destroy();
        editorRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [holderId.current]);

  useEffect(() => {}, [value]);

  return <div id={holderId.current} className={`edjs-wrap ${className || ""}`} />;
}
