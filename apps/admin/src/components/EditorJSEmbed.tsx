import type EditorJS from "@editorjs/editorjs";
import { useCallback,useEffect, useRef, useState } from "react";

import { wsApi } from "../api/wsApi";
import type { OutputData } from "../types/editorjs";
import { compressImage } from "../utils/compressImage";
import { resolveUrl } from "../utils/resolveUrl";
import { useAccount } from "../workspace/WorkspaceContext";

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
  minHeight = 480,
  placeholder,
  onReady,
}: Props) {
  const holderId = useRef(`edjs-${Math.random().toString(36).slice(2)}`);
  const editorRef = useRef<EditorJS | null>(null);
  const changeTimer = useRef<number | null>(null);
  const lastRendered = useRef<string>("");
  const applyingExternal = useRef(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  const { accountId } = useAccount();

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

  // Унифицированный помощник отрисовки данных в EditorJS
  const renderEditor = useCallback(async (inst: any, data: OutputData) => {
    try {
      if (inst?.isReady && typeof inst.isReady.then === "function") {
        await inst.isReady;
      }
      if (inst?.render) {
        await inst.render(data as any);
      } else {
        const blocks = (data as any)?.blocks || (data as any)?.data?.blocks;
        if (Array.isArray(blocks) && inst?.blocks?.render) {
          await inst.blocks.render(blocks);
        }
      }
    } catch (e) {
      // логируем, но не прерываем поток — важнее не ломать ввод пользователя
      console.error("EditorJS render failed", e);
    }
  }, []);

  useEffect(() => {
    let destroyed = false;

    async function init() {
      try {
        const EditorJS = (await import("@editorjs/editorjs")).default;
        const Header = (await import("@editorjs/header")).default;
        const List = (await import("@editorjs/list")).default;
        const Checklist = (await import("@editorjs/checklist")).default;
        const ImageTool = (await import("@editorjs/image")).default;
        const Table = (await import("@editorjs/table")).default;
        const Quote = (await import("@editorjs/quote")).default;
        const Delimiter = (await import("@editorjs/delimiter")).default;

        if (destroyed) return;

        const initialData: OutputData = (value as OutputData) || {
          time: Date.now(),
          blocks: [{ type: "paragraph", data: { text: "" } }],
          version: "2.30.7",
        };

        const instance = new EditorJS({
        holder: holderId.current,
        minHeight,
        placeholder: placeholder || "Напишите описание, легенду или сценарий…",
        data: initialData,
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
                    const compressed = await compressImage(file);
                    const form = new FormData();
                    form.append("file", compressed);
                    const res = await wsApi.request<any>("/admin/media", {
                      method: "POST",
                      body: form,
                      raw: true,
                      accountId,
                    });
                    const rawUrl = extractUrl((res as any)?.data ?? res);
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
          if (applyingExternal.current) return; // skip feedback when we render externally
          if (changeTimer.current) window.clearTimeout(changeTimer.current);
          changeTimer.current = window.setTimeout(async () => {
            try {
              const data = (await instance.save()) as unknown as OutputData;
              onChange(data);
              try {
                lastRendered.current = JSON.stringify(data);
              } catch {
                // ignore
              }
            } catch {
              // ignore
            }
          }, 400);
        },
      });

      editorRef.current = instance;
      // Зафиксируем исходные данные, чтобы избежать немедленного повторного render(value)
      try {
        lastRendered.current = JSON.stringify(initialData);
      } catch {
        // ignore
      }
      try {
          onReady?.({
            save: async () => (await instance.save()) as unknown as OutputData,
          });
      } catch {
        // ignore
      }
      // Помечаем, что инстанс готов к синхронизации с актуальным value
      setInitialized(true);
      } catch (e) {
        if (destroyed) return;
        console.error("EditorJS failed to load", e);
        setLoadError(e instanceof Error ? e.message : String(e));
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

  // Одноразовая синхронизация после инициализации редактора на случай,
  // когда value уже успело прийти до того, как EditorJS был создан.
  useEffect(() => {
    if (!initialized) return;
    const inst = editorRef.current;
    if (!inst || !value) return;
    let incoming = "";
    try {
      incoming = JSON.stringify(value);
    } catch {
      // ignore
    }
    if (!incoming || incoming === lastRendered.current) return;
    applyingExternal.current = true;
    const doRender = async () => {
      await renderEditor(inst, value as OutputData);
      lastRendered.current = incoming;
      applyingExternal.current = false;
    };
    void doRender();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialized]);

  // When value prop changes after async load, re-render the editor content
  useEffect(() => {
    const inst = editorRef.current;
    if (!inst || !value) return;
    let incoming = "";
    try {
      incoming = JSON.stringify(value);
    } catch {
      // ignore
    }
    if (!incoming || incoming === lastRendered.current) return;
    applyingExternal.current = true;
    const doRender = async () => {
      await renderEditor(inst, value as OutputData);
      lastRendered.current = incoming;
      applyingExternal.current = false;
    };
    void doRender();
  }, [value, renderEditor]);

  if (loadError) {
    return (
      <div className={className || ""}>
        Не удалось загрузить редактор: {loadError}
      </div>
    );
  }

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
