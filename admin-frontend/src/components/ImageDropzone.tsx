import { useCallback, useRef, useState } from "react";
import { api } from "../api/client";

interface ImageDropzoneProps {
  value?: string | null;
  onChange?: (dataUrl: string | null) => void;
  className?: string;
  height?: number;
}

export default function ImageDropzone({ value, onChange, className = "", height = 140 }: ImageDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!file.type.startsWith("image/")) return;
      const form = new FormData();
      form.append("file", file);
      try {
        const res = await api.request<{ url: string }>("/media", { method: "POST", body: form });
        onChange?.(res.data?.url || null);
      } catch {
        // ignore upload errors
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
          <img src={value} alt="" className="w-full rounded border object-cover" style={{ height }} />
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
            <div className="text-xs text-gray-500">или нажмите, чтобы выбрать файл</div>
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
