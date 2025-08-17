import { useEffect, useRef } from "react";
import { api } from "../api/client";

type EditorData = any;

interface Props {
  value?: EditorData;
  onChange?: (data: EditorData) => void;
  className?: string;
  minHeight?: number;
  placeholder?: string;
  onReady?: (api: { save: () => Promise<any> }) => void;
}

export default function EditorJSEmbed({ value, onChange, className, minHeight = 220, placeholder, onReady }: Props) {
  const holderId = useRef(`edjs-${Math.random().toString(36).slice(2)}`);
  const editorRef = useRef<any>(null);
  const changeTimer = useRef<number | null>(null);

  // Преобразуем относительный URL (/static/uploads/...) в абсолютный к backend origin (в dev 5173–5176) или VITE_API_BASE
  const resolveUrl = (u?: string): string => {
    if (!u) return "";
    try {
      // База для относительных ссылок: VITE_API_BASE или dev-мэппинг на :8000, иначе текущий origin
      let base = "";
      const envBase = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
      if (envBase) {
        base = envBase;
      } else if (typeof window !== "undefined" && window.location) {
        const port = window.location.port;
        if (port && ["5173", "5174", "5175", "5176"].includes(port)) {
          base = `${window.location.protocol}//${window.location.hostname}:8000`;
        } else {
          base = `${window.location.protocol}//${window.location.host}`;
        }
      }

      // Унифицировано резолвим и относительные, и абсолютные URL
      const urlObj = new URL(u, base || (typeof window !== "undefined" ? window.location.origin : undefined));

      // Избегаем mixed content: если страница по HTTPS, а ссылка http — апгрейдим до https
      if (typeof window !== "undefined" && window.location?.protocol === "https:" && urlObj.protocol === "http:") {
        urlObj.protocol = "https:";
      }
      return urlObj.toString();
    } catch {
      // На всякий случай возвращаем исходное значение
      return u;
    }
  };

  // removed waitForImage helper (unused)

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
                async uploadByFile(file: File) {
                  try {
                    const form = new FormData();
                    form.append("file", file);
                    const res = await api.request<any>("/media", {
                      method: "POST",
                      body: form,
                    });
                    const data = res.data ?? {};
                    // Если сервер уже вернул формат ImageTool -> отдаем «как есть»
                    if (data && typeof data === "object" && data.success === 1 && data.file?.url) {
                      const normalized = { ...data, file: { ...data.file, url: resolveUrl(data.file.url) } };
                      if (import.meta?.env?.MODE !== "production") {
                        console.debug("[EditorJS:image] uploadByFile response (pass-through)", normalized);
                      }
                      return normalized as any;
                    }
                    // Иначе нормализуем к ожидаемому формату
                    const rawUrl = data.file?.url || data.url || "";
                    const url = resolveUrl(rawUrl);
                    if (!url) throw new Error("Empty URL from /media");
                    const normalized = { success: 1, file: { url } };
                    if (import.meta?.env?.MODE !== "production") {
                      console.debug("[EditorJS:image] uploadByFile response (normalized)", normalized);
                    }
                    return normalized as any;
                  } catch (e) {
                    console.error("Image upload failed:", e);
                    return { success: 0 } as any;
                  }
                },
                async uploadByUrl(url: string) {
                  try {
                    if (typeof url === "string" && url) {
                      const final = resolveUrl(url);
                      const normalized = { success: 1, file: { url: final } };
                      if (import.meta?.env?.MODE !== "production") {
                        console.debug("[EditorJS:image] uploadByUrl", normalized);
                      }
                      return normalized as any;
                    }
                  } catch (e) {
                    console.error("Image uploadByUrl failed:", e);
                  }
                  return { success: 0 } as any;
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
      try {
        onReady?.({ save: () => instance.save() });
      } catch {
        // ignore
      }
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

  return (
    <>
      <style>{`
        /* Контент и тулбар не шире контейнера */
        #${holderId.current} .ce-block__content,
        #${holderId.current} .ce-toolbar__content { max-width: 100%; }

        /* Изображения не выходят за границы */
        #${holderId.current} img { max-width: 100%; height: auto; }

        /* Смещаем тулбар («плюсик») внутрь контейнера */
        #${holderId.current} .ce-toolbar { left: 8px !important; }
      `}</style>
      <div
        id={holderId.current}
        className={`edjs-wrap w-full box-border ${className || ""}`}
        style={{
          maxWidth: "100%",
          overflow: "visible",
          position: "relative",
          paddingLeft: "24px" // небольшой отступ, чтобы «плюсик» не упирался в левую границу
        }}
      />
    </>
  );
}
