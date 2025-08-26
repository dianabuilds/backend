import type EditorJS from "@editorjs/editorjs";
import { useEffect, useRef } from "react";

import { api } from "../api/client";
import type { OutputData } from "../types/editorjs";

interface Props {
  value?: OutputData;
  onChange?: (data: OutputData) => void;
  className?: string;
  minHeight?: number;
  placeholder?: string;
  onReady?: (api: { save: () => Promise<OutputData> }) => void;
}

type ImageUploadResult = { success: 1; file: { url: string } } | { success: 0 };

export default function EditorJSEmbed({
  value,
  onChange,
  className,
  minHeight = 220,
  placeholder,
  onReady,
}: Props) {
  const holderId = useRef(`edjs-${Math.random().toString(36).slice(2)}`);
  const editorRef = useRef<EditorJS | null>(null);
  const changeTimer = useRef<number | null>(null);

  // Преобразуем относительный URL (/static/uploads/...) в абсолютный к backend origin (в dev 5173–5176) или VITE_API_BASE
  const resolveUrl = (u?: string): string => {
    if (!u) return "";
    try {
      // База для относительных ссылок: VITE_API_BASE или dev-мэппинг на :8000, иначе текущий origin
      let base = "";
      const envBase = (
        import.meta as { env?: Record<string, string | undefined> }
      )?.env?.VITE_API_BASE as string | undefined;
      if (envBase) {
        base = envBase;
      } else if (typeof window !== "undefined" && window.location) {
        const port = window.location.port;
        if (port && ["5173", "5174", "5175", "5176"].includes(port)) {
          // В dev всегда идём на http://:8000 (бэкенд без TLS), иначе возможен нерабочий https://:8000
          base = `http://${window.location.hostname}:8000`;
        } else {
          base = `${window.location.protocol}//${window.location.host}`;
        }
      }

      // Унифицировано резолвим и относительные, и абсолютные URL
      const urlObj = new URL(
        u,
        base ||
          (typeof window !== "undefined" ? window.location.origin : undefined),
      );

      // Важно: не меняем протокол принудительно.
      // Если backend доступен только по http, насильственная замена на https приведёт к невозможности загрузить изображение.
      return urlObj.toString();
    } catch {
      // На всякий случай возвращаем исходное значение
      return u;
    }
  };

  const extractUrl = (data: unknown): string => {
    if (typeof data === "string") return data;
    if (data && typeof data === "object") {
      const obj = data as Record<string, unknown>;
      const file = obj.file as Record<string, unknown> | undefined;
      if (typeof file?.url === "string") return file.url;
      if (typeof obj.url === "string") return obj.url;
      const inner = obj.data as Record<string, unknown> | undefined;
      const innerFile = inner?.file as Record<string, unknown> | undefined;
      if (typeof innerFile?.url === "string") return innerFile.url;
      const innerUrl = inner?.url;
      if (typeof innerUrl === "string") return innerUrl;
    }
    return "";
  };

  // removed waitForImage helper (unused)

  useEffect(() => {
    let destroyed = false;

    async function init() {
      const EditorJS = (await import("@editorjs/editorjs")).default;
      const Header = (await import("@editorjs/header")).default;
      const List = (await import("@editorjs/list")).default;
      const Checklist = (await import("@editorjs/checklist")).default;
      const ImageTool = (await import("@editorjs/image")).default;
      const Table = (await import("@editorjs/table")).default;
      const Quote = (await import("@editorjs/quote")).default;
      const Delimiter = (await import("@editorjs/delimiter")).default;

      if (destroyed) return;

      const instance = new EditorJS({
        holder: holderId.current,
        minHeight,
        placeholder: placeholder || "Напишите описание, легенду или сценарий…",
        data: value || {
          time: Date.now(),
          blocks: [{ type: "paragraph", data: { text: "" } }],
          version: "2.30.7",
        },
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
                async uploadByFile(file: File): Promise<ImageUploadResult> {
                  try {
                    const form = new FormData();
                    form.append("file", file);
                    const res = await api.request<unknown>("/admin/media", {
                      method: "POST",
                      body: form,
                    });
                    const rawUrl = extractUrl(res?.data);
                    const url = resolveUrl(rawUrl);
                    if (!url) throw new Error("Empty URL from /media");
                    const normalized: ImageUploadResult = {
                      success: 1,
                      file: { url },
                    };
                    return normalized;
                  } catch (e) {
                    console.error("Image upload failed:", e);
                    return { success: 0 };
                  }
                },
                async uploadByUrl(url: string): Promise<ImageUploadResult> {
                  try {
                    if (typeof url === "string" && url) {
                      const final = resolveUrl(url);
                      const normalized: ImageUploadResult = {
                        success: 1,
                        file: { url: final },
                      };
                      return normalized;
                    }
                  } catch (e) {
                    console.error("Image uploadByUrl failed:", e);
                  }
                  return { success: 0 };
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

        /* Изображения не выходят за границы и ограничены по высоте */
        #${holderId.current} img { max-width: 100%; max-height: 380px; object-fit: contain; }

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
          paddingLeft: "24px", // небольшой отступ, чтобы «плюсик» не упирался в левую границу
        }}
      />
    </>
  );
}
