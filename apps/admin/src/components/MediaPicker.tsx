import { useEffect, useState } from "react";

import { useAccount } from "../account/AccountContext";
import { accountApi } from "../api/accountApi";
import { addToCatalog } from "../utils/tagManager";
import { resolveBackendUrl } from "../utils/url";
import ImageDropzone from "./ImageDropzone";
import TagInput from "./TagInput";

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

export default function MediaPicker({
  value,
  onChange,
  className = "",
  height = 140,
}: Props) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<MediaAsset[]>([]);
  const [query, setQuery] = useState("");
  const [filterTags, setFilterTags] = useState<string[]>([]);
  const { accountId } = useAccount();

  useEffect(() => {
    if (!open || !accountId) return;
    if (mediaCache) {
      setItems(mediaCache);
      return;
    }
    (async () => {
      try {
        const data =
          (await accountApi.get<ApiMediaAsset[]>("/admin/media", { accountId })) || [];
        const mapped = data.map((d) => ({
          id: d.id,
          url: resolveBackendUrl(d.url) || d.url,
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
    const matchesQuery =
      m.url.toLowerCase().includes(query.toLowerCase()) ||
      m.name?.toLowerCase().includes(query.toLowerCase());
    const matchesTags = filterTags.every((t) => m.tags.includes(t));
    return matchesQuery && matchesTags;
  });

  return (
    <div className={className}>
      <ImageDropzone value={value} onChange={onChange} height={height} />
      <button
        type="button"
        className="mt-2 text-xs px-2 py-1 rounded border bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
        onClick={() => setOpen(true)}
        aria-label="Browse media"
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
              <TagInput
                value={filterTags}
                onChange={setFilterTags}
                placeholder="Filter tags"
              />
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
              className="mt-4 px-2 py-1 border rounded text-sm bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={() => setOpen(false)}
              aria-label="Close media picker"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
