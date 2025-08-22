import { useEffect, useState } from "react";
import { api } from "../api/client";
import ImageDropzone from "./ImageDropzone";

interface Props {
  value?: string | null;
  onChange?: (url: string | null) => void;
  className?: string;
  height?: number;
}

interface MediaAsset {
  id: string;
  url: string;
  type: string;
}

export default function MediaPicker({ value, onChange, className = "", height = 140 }: Props) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<MediaAsset[]>([]);

  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        const res = await api.get("/admin/media");
        setItems((res.data as MediaAsset[]) || []);
      } catch {
        setItems([]);
      }
    })();
  }, [open]);

  return (
    <div className={className}>
      <ImageDropzone value={value} onChange={onChange} height={height} />
      <button
        type="button"
        className="mt-2 text-xs px-2 py-1 rounded border"
        onClick={() => setOpen(true)}
      >
        Browse
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 p-4 rounded shadow max-h-[80vh] overflow-auto">
            <div className="grid grid-cols-3 gap-2">
              {items.map((m) => (
                <img
                  key={m.id}
                  src={m.url}
                  className="w-32 h-32 object-cover cursor-pointer"
                  onClick={() => {
                    onChange?.(m.url);
                    setOpen(false);
                  }}
                />
              ))}
            </div>
            <button
              type="button"
              className="mt-4 px-2 py-1 border rounded text-sm"
              onClick={() => setOpen(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
