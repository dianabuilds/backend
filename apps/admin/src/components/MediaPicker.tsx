import { useEffect, useState } from "react";
import { api } from "../api/client";
import ImageDropzone from "./ImageDropzone";
import TagInput from "./TagInput";
import { addToCatalog } from "../utils/tagManager";

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
  tags: string[];
  name?: string;
}

interface ApiMediaAsset {
  id: string;
  url: string;
  type: string;
  metadata_json?: { tags?: string[]; name?: string };
}

let mediaCache: MediaAsset[] | null = null;

export default function MediaPicker({ value, onChange, className = "", height = 140 }: Props) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<MediaAsset[]>([]);
  const [query, setQuery] = useState("");
  const [filterTags, setFilterTags] = useState<string[]>([]);

  useEffect(() => {
    if (!open) return;
    if (mediaCache) {
      setItems(mediaCache);
      return;
    }
    (async () => {
      try {
        const res = await api.get("/admin/media");
        const data = (res.data as ApiMediaAsset[]) || [];
        const mapped = data.map((d) => ({
          id: d.id,
          url: d.url,
          type: d.type,
          tags: d.metadata_json?.tags ?? [],
          name: d.metadata_json?.name ?? "",
        }));
        addToCatalog(mapped.flatMap((m: MediaAsset) => m.tags));
        mediaCache = mapped;
        setItems(mapped);
      } catch {
        setItems([]);
      }
    })();
  }, [open]);

  const filteredItems = items.filter((m) => {
    const matchesQuery = m.url.toLowerCase().includes(query.toLowerCase()) || m.name?.toLowerCase().includes(query.toLowerCase());
    const matchesTags = filterTags.every((t) => m.tags.includes(t));
    return matchesQuery && matchesTags;
  });

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
            <div className="mb-2 flex flex-col gap-2">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search"
                className="border px-2 py-1 rounded"
              />
              <TagInput value={filterTags} onChange={setFilterTags} placeholder="Filter tags" />
            </div>
            <div className="grid grid-cols-3 gap-2">
              {filteredItems.map((m) => (
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
