import { useCallback, useRef, useState } from "react";

import { api } from "../api/client";

interface ImageDropzoneProps {
  value?: string | null;
  onChange?: (dataUrl: string | null) => void;
  className?: string;
  height?: number;
}

export default function ImageDropzone({
  value,
  onChange,
  className = "",
  height = 140,
}: ImageDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const resolveUrl = (data: any, headers: Headers): string | null => {
    let u: string | null =
      (data && (data.url || data.path || data.location)) ??
      (typeof data === "string" ? data : null) ??
      headers.get("Location");
    if (!u) return null;

    // Если путь относительный — префиксуем базой API, иначе Vite (517x) пойдёт на фронт и получит 404.
    const envBase = (import.meta as any)?.env?.VITE_API_BASE as
      | string
      | undefined;
    const backendBase =
      envBase ||
      (typeof window !== "undefined" &&
      ["5173", "5174", "5175", "5176"].includes(window.location.port || "")
        ? `${window.location.protocol}//${window.location.hostname}:8000`
        : "");

    if (u.startsWith("//")) u = window.location.protocol + u;
    else if (/^https?:\/\//i.test(u)) {
      // абсолютный — используем как есть
    } else if (u.startsWith("/")) {
      u = (backendBase || "") + u;
    } else {
      u = (backendBase || "") + "/" + u.replace(/^\.?\//, "");
    }
    return u;
  };

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!file.type.startsWith("image/")) {
        setError("Можно загружать только изображения");
        return;
      }
      const form = new FormData();
      form.append("file", file);
      setError(null);
      try {
        const res = await api.request("/admin/media", {
          method: "POST",
          body: form,
        });
        const url = resolveUrl(res.data, res.response.headers);
        if (!url) {
          setError("Сервер не вернул URL загруженного файла");
          return;
        }
        onChange?.(url);
      } catch (e) {
        setError(
          e instanceof Error ? e.message : "Не удалось загрузить изображение",
        );
      }
    },
    [onChange],
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const onClick = () => inputRef.current?.click();

  return (
    <div className={className}>
      {value ? (
        <div className="relative">
          <img
            src={value}
            alt=""
            className="w-full rounded border object-cover"
            style={{ height }}
            onError={() => setError("Не удалось отобразить изображение")}
          />
          <div className="absolute top-2 right-2 flex gap-2">
            <button
              type="button"
              className="text-xs px-2 py-1 rounded bg-white/90 border"
              onClick={() => onChange?.(null)}
              title="Remove"
            >
              Remove
            </button>
            <button
              type="button"
              className="text-xs px-2 py-1 rounded bg-white/90 border"
              onClick={onClick}
              title="Replace"
            >
              Replace
            </button>
          </div>
        </div>
      ) : (
        <div
          className={`rounded border-2 border-dashed ${dragOver ? "border-blue-400 bg-blue-50" : "border-gray-300"} cursor-pointer flex items-center justify-center text-sm text-gray-600`}
          style={{ height }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={onClick}
        >
          <div className="text-center px-3">
            <div className="mx-auto mb-2 text-3xl">🖼️</div>
            <div className="font-medium mb-0.5">Перетащите изображение</div>
            <div className="text-xs text-gray-500">
              или нажмите, чтобы выбрать файл
            </div>
            {error && <div className="mt-2 text-xs text-red-600">{error}</div>}
          </div>
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  );
}
