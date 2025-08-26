import Cropper, { type Area } from "react-easy-crop";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api/client";
import { listFlags } from "../api/flags";
import { useCallback, useEffect, useRef, useState } from "react";

interface CoverChange {
  assetId: string | null;
  url: string | null;
  alt: string;
  meta: any | null;
}

interface NodeSidebarProps {
  node: {
    id: string;
    slug: string;
    author_id: string;
    is_public: boolean;
    node_type: string;
    cover_url: string | null;
    cover_asset_id: string | null;
    cover_alt: string;
    cover_meta: any | null;
  };
  onSlugChange?: (slug: string) => void;
  onCoverChange?: (data: CoverChange) => void;
}

export default function NodeSidebar({
  node,
  onSlugChange,
  onCoverChange,
}: NodeSidebarProps) {
  const { user } = useAuth();
  const role = user?.role;
  const canModerate = role === "admin" || role === "moderator";
  const canEditSlug = role === "admin";

  const [nodesCover, setNodesCover] = useState(false);
  useEffect(() => {
    (async () => {
      try {
        const flags = await listFlags();
        const f = flags.find((x) => x.key === "nodes_cover");
        setNodesCover(Boolean(f?.value));
      } catch {
        setNodesCover(false);
      }
    })();
  }, []);

  const fileRef = useRef<HTMLInputElement | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedArea, setCroppedArea] = useState<Area | null>(null);
  const [focal, setFocal] = useState<{ x: number; y: number }>(
    node.cover_meta && typeof node.cover_meta.focalX === "number"
      ? { x: node.cover_meta.focalX, y: node.cover_meta.focalY }
      : { x: 0.5, y: 0.5 },
  );

  useEffect(() => {
    if (!editing) return;
    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setCroppedArea(null);
    setFocal(
      node.cover_meta && typeof node.cover_meta.focalX === "number"
        ? { x: node.cover_meta.focalX, y: node.cover_meta.focalY }
        : { x: 0.5, y: 0.5 },
    );
  }, [editing, node.cover_meta]);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!/^image\/(jpeg|png|webp)$/i.test(file.type)) {
        setUploadError("Допустимы только изображения JPEG/PNG/WebP");
        return;
      }
      if (file.size > 8 * 1024 * 1024) {
        setUploadError("Размер файла не должен превышать 8 MB");
        return;
      }
      const img = new Image();
      img.onload = async () => {
        if (img.width < 960 || img.height < 540) {
          setUploadError("Минимальное разрешение 960×540");
          return;
        }
        setUploadError(null);
        const form = new FormData();
        form.append("file", file);
        try {
          const res = await api.request("/admin/media/assets", {
            method: "POST",
            body: form,
          });
          const data = res.data as any;
          const id = data?.id ?? data?.asset_id ?? data?.assetId ?? null;
          const url = data?.url ?? data?.file_url ?? data?.src ?? null;
          if (!id || !url) {
            setUploadError("Сервер не вернул ID или URL");
            return;
          }
          onCoverChange?.({
            assetId: id,
            url,
            alt: node.cover_alt,
            meta: { focalX: 0.5, focalY: 0.5, crop: { x: 0, y: 0, width: 1, height: 1 } },
          });
        } catch (e) {
          setUploadError(
            e instanceof Error ? e.message : "Не удалось загрузить изображение",
          );
        }
      };
      img.onerror = () => {
        setUploadError("Не удалось прочитать изображение");
      };
      img.src = URL.createObjectURL(file);
    },
    [node.cover_alt, onCoverChange],
  );

  const applyMeta = () => {
    const cropMeta = croppedArea
      ? {
          x: croppedArea.x / 100,
          y: croppedArea.y / 100,
          width: croppedArea.width / 100,
          height: croppedArea.height / 100,
        }
      : { x: 0, y: 0, width: 1, height: 1 };
    onCoverChange?.({
      assetId: node.cover_asset_id,
      url: node.cover_url,
      alt: node.cover_alt,
      meta: { focalX: focal.x, focalY: focal.y, crop: cropMeta },
    });
    setEditing(false);
  };

  return (
    <div className="w-64 border-l p-4 overflow-y-auto space-y-4">
      {nodesCover ? (
        <details open>
          <summary className="cursor-pointer font-semibold">Cover</summary>
          <div className="mt-2 space-y-2 text-sm">
            {node.cover_url ? (
              <div className="relative">
                <img
                  src={node.cover_url}
                  alt={node.cover_alt || ""}
                  className="w-full rounded border object-cover aspect-video"
                />
                <div className="absolute top-2 right-2 flex gap-1">
                  <button
                    type="button"
                    className="text-xs px-2 py-1 rounded bg-white/90 border"
                    onClick={() => fileRef.current?.click()}
                    title="Replace"
                  >
                    Replace
                  </button>
                  <button
                    type="button"
                    className="text-xs px-2 py-1 rounded bg-white/90 border"
                    onClick={() => setEditing(true)}
                    title="Edit"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="text-xs px-2 py-1 rounded bg-white/90 border"
                    onClick={() =>
                      onCoverChange?.({
                        assetId: null,
                        url: null,
                        alt: "",
                        meta: null,
                      })
                    }
                    title="Remove"
                  >
                    Remove
                  </button>
                </div>
              </div>
            ) : (
              <div
                className="border-2 border-dashed rounded h-32 flex items-center justify-center text-gray-500 cursor-pointer"
                onClick={() => fileRef.current?.click()}
              >
                Upload cover
              </div>
            )}
            {node.cover_url ? (
              <input
                type="text"
                className="w-full border rounded px-2 py-1 text-xs"
                placeholder="Alt text"
                value={node.cover_alt}
                onChange={(e) =>
                  onCoverChange?.({
                    assetId: node.cover_asset_id,
                    url: node.cover_url,
                    alt: e.target.value,
                    meta: node.cover_meta,
                  })
                }
              />
            ) : null}
            {uploadError && (
              <div className="text-xs text-red-600">{uploadError}</div>
            )}
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>
        </details>
      ) : null}

      <details open>
        <summary className="cursor-pointer font-semibold">Metadata</summary>
        <div className="mt-2 space-y-1 text-sm">
          <div>ID: {node.id}</div>
          <div>
            Slug: {canEditSlug && onSlugChange ? (
              <input
                className="w-full border rounded px-1 py-0.5 text-xs"
                value={node.slug}
                onChange={(e) => onSlugChange(e.target.value)}
              />
            ) : (
              node.slug || "-"
            )}
          </div>
          <div>Author: {node.author_id || "-"}</div>
        </div>
      </details>
      <details open>
        <summary className="cursor-pointer font-semibold">Auto-links</summary>
        <div className="mt-2 text-sm text-gray-500">No auto-links.</div>
      </details>
      <details open>
        <summary className="cursor-pointer font-semibold">Publication</summary>
        <div className="mt-2 space-y-1 text-sm">
          <div>Status: {node.is_public ? "Published" : "Draft"}</div>
          <div>Scheduling: —</div>
        </div>
      </details>
      <details open>
        <summary className="cursor-pointer font-semibold">Validation</summary>
        <div className="mt-2 text-sm text-gray-500">No validation errors.</div>
      </details>
      {canModerate ? (
        <details>
          <summary className="cursor-pointer font-semibold">Advanced</summary>
          <div className="mt-2 space-y-1 text-sm">
            <div>Type: {node.node_type}</div>
          </div>
        </details>
      ) : null}

      {editing && node.cover_url ? (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 p-4 rounded shadow-lg">
            <div
              className="relative w-[80vw] max-w-[640px] h-[45vw] max-h-[360px]"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setFocal({
                  x: (e.clientX - rect.left) / rect.width,
                  y: (e.clientY - rect.top) / rect.height,
                });
              }}
            >
              <Cropper
                image={node.cover_url}
                crop={crop}
                zoom={zoom}
                aspect={16 / 9}
                onCropChange={setCrop}
                onZoomChange={setZoom}
                onCropComplete={(_, area) => setCroppedArea(area)}
              />
              <div
                className="pointer-events-none absolute w-4 h-4 bg-white border rounded-full"
                style={{
                  left: `${focal.x * 100}%`,
                  top: `${focal.y * 100}%`,
                  transform: "translate(-50%, -50%)",
                }}
              />
            </div>
            <div className="mt-4 flex justify-end gap-2 text-sm">
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={() => setEditing(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={applyMeta}
              >
                Apply
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

