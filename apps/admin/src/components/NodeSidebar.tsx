/* eslint-disable @typescript-eslint/no-explicit-any */
import { useCallback, useEffect, useRef, useState } from 'react';
import Cropper, { type Area } from 'react-easy-crop';

import { listFlags } from '../api/flags';
import {
  patchNode,
  publishNode,
  archiveNode,
  duplicateNode,
  previewNode,
} from '../api/nodes';
import { wsApi } from '../api/wsApi';
import { useAuth } from '../auth/AuthContext';
import { compressImage } from '../utils/compressImage';

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
    authorId: string;
    createdAt: string;
    updatedAt: string;
    isPublic: boolean;
    publishedAt: string | null;
    nodeType: string;
    coverUrl: string | null;
    coverAssetId: string | null;
    coverAlt: string;
    coverMeta: any | null;
    allowFeedback: boolean;
    premiumOnly: boolean;
  };
  accountId: string;
  onSlugChange?: (slug: string, updatedAt?: string) => void;
  onCoverChange?: (data: CoverChange) => void;
  onStatusChange?: (isPublic: boolean, updatedAt?: string) => void;
  onScheduleChange?: (publishedAt: string | null, updatedAt?: string) => void;
  onAllowFeedbackChange?: (allow: boolean, updatedAt?: string) => void;
  onPremiumOnlyChange?: (premium: boolean, updatedAt?: string) => void;
}

export default function NodeSidebar({
  node,
  accountId,
  onSlugChange,
  onCoverChange,
  onStatusChange,
  onScheduleChange,
  onAllowFeedbackChange,
  onPremiumOnlyChange,
}: NodeSidebarProps) {
  const { user } = useAuth();
  const role = user?.role;
  const canModerate = role === 'admin' || role === 'moderator';
  const canEditSlug = role === 'admin';

  const [nodesCover, setNodesCover] = useState(false);
  useEffect(() => {
    (async () => {
      try {
        const flags = await listFlags();
        const f = flags.find((x) => x.key === 'nodes_cover');
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
    node.coverMeta && typeof node.coverMeta.focalX === 'number'
      ? { x: node.coverMeta.focalX, y: node.coverMeta.focalY }
      : { x: 0.5, y: 0.5 },
  );

  const [slugModal, setSlugModal] = useState(false);
  const [slugDraft, setSlugDraft] = useState(node.slug);
  const [slugSaving, setSlugSaving] = useState(false);
  const [slugError, setSlugError] = useState<string | null>(null);

  const [statusSaving, setStatusSaving] = useState(false);
  const [allowSaving, setAllowSaving] = useState(false);
  const [premiumSaving, setPremiumSaving] = useState(false);
  const [scheduleValue, setScheduleValue] = useState(
    node.publishedAt ? node.publishedAt.slice(0, 16) : '',
  );
  const [scheduleSaving, setScheduleSaving] = useState(false);

  useEffect(() => {
    setScheduleValue(node.publishedAt ? node.publishedAt.slice(0, 16) : '');
  }, [node.publishedAt]);

  useEffect(() => {
    if (!editing) return;
    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setCroppedArea(null);
    setFocal(
      node.coverMeta && typeof node.coverMeta.focalX === 'number'
        ? { x: node.coverMeta.focalX, y: node.coverMeta.focalY }
        : { x: 0.5, y: 0.5 },
    );
  }, [editing, node.coverMeta]);

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!/^image\/(jpeg|png|webp)$/i.test(file.type)) {
        setUploadError('Допустимы только изображения JPEG/PNG/WebP');
        return;
      }
      if (file.size > 8 * 1024 * 1024) {
        setUploadError('Размер файла не должен превышать 8 MB');
        return;
      }
      const img = new Image();
      img.onload = async () => {
        URL.revokeObjectURL(img.src);
        if (img.width < 960 || img.height < 540) {
          setUploadError('Минимальное разрешение 960×540');
          return;
        }
        setUploadError(null);
        try {
          const compressed = await compressImage(file);
          const form = new FormData();
          form.append('file', compressed);
          const res = await wsApi.request('/admin/media/assets', {
            method: 'POST',
            body: form,
            raw: true,
          });
          const data = res.data as any;
          const id = data?.id ?? data?.asset_id ?? data?.assetId ?? null;
          const url = data?.url ?? data?.file_url ?? data?.src ?? null;
          if (!id || !url) {
            setUploadError('Сервер не вернул ID или URL');
            return;
          }
          onCoverChange?.({
            assetId: id,
            url,
            alt: node.coverAlt,
            meta: { focalX: 0.5, focalY: 0.5, crop: { x: 0, y: 0, width: 1, height: 1 } },
          });
        } catch (e) {
          setUploadError(e instanceof Error ? e.message : 'Не удалось загрузить изображение');
        }
      };
      img.onerror = () => {
        URL.revokeObjectURL(img.src);
        setUploadError('Не удалось прочитать изображение');
      };
      img.src = URL.createObjectURL(file);
    },
    [node.coverAlt, onCoverChange],
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
      assetId: node.coverAssetId,
      url: node.coverUrl,
      alt: node.coverAlt,
      meta: { focalX: focal.x, focalY: focal.y, crop: cropMeta },
    });
    setEditing(false);
  };

  const handleStatusChange = async (checked: boolean) => {
    setStatusSaving(true);
    try {
      const res = await patchNode(accountId, node.id, {
        isPublic: checked,
        updatedAt: node.updatedAt,
      });
      const updated = res.updatedAt ?? node.updatedAt;
      const published = res.isPublic ?? checked;
      onStatusChange?.(published, updated);
    } finally {
      setStatusSaving(false);
    }
  };

  const handleAllowFeedbackChange = async (checked: boolean) => {
    setAllowSaving(true);
    try {
      const res = await patchNode(accountId, node.id, {
        allowFeedback: checked,
        updatedAt: node.updatedAt,
      });
      const updated = res.updatedAt ?? node.updatedAt;
      const allow = (res as any).allowFeedback ?? checked;
      onAllowFeedbackChange?.(allow, updated);
    } finally {
      setAllowSaving(false);
    }
  };

  const handlePremiumOnlyChange = async (checked: boolean) => {
    setPremiumSaving(true);
    try {
      const res = await patchNode(accountId, node.id, {
        premiumOnly: checked,
        updatedAt: node.updatedAt,
      });
      const updated = res.updatedAt ?? node.updatedAt;
      const premium = (res as any).premiumOnly ?? checked;
      onPremiumOnlyChange?.(premium, updated);
    } finally {
      setPremiumSaving(false);
    }
  };

  const handleScheduleChange = async (value: string) => {
    setScheduleValue(value);
    setScheduleSaving(true);
    try {
      const iso = value ? new Date(value).toISOString() : null;
      const res = await patchNode(accountId, node.id, {
        publishedAt: iso,
        updatedAt: node.updatedAt,
      });
      const updated = res.updatedAt ?? node.updatedAt;
      const publishedAt = res.publishedAt ?? iso;
      onScheduleChange?.(publishedAt, updated);
    } finally {
      setScheduleSaving(false);
    }
  };

  const handlePublish = async () => {
    await publishNode(accountId, Number(node.id));
    onStatusChange?.(true);
  };

  const handleHide = async () => {
    await patchNode(accountId, node.id, { isPublic: false, updatedAt: node.updatedAt });
    onStatusChange?.(false);
  };

  const handleArchive = async () => {
    await archiveNode(accountId, Number(node.id));
  };

  const handleMakePublic = async () => {
    await patchNode(accountId, node.id, { premiumOnly: false, updatedAt: node.updatedAt });
    onPremiumOnlyChange?.(false);
  };

  const handleMakePremium = async () => {
    await patchNode(accountId, node.id, { premiumOnly: true, updatedAt: node.updatedAt });
    onPremiumOnlyChange?.(true);
  };

  const handleDuplicate = async () => {
    await duplicateNode(accountId, Number(node.id));
  };

  const handlePreview = async () => {
    await previewNode(accountId, Number(node.id));
  };

  const copy = (v: string) => {
    if (typeof navigator !== 'undefined') {
      void navigator.clipboard?.writeText(v);
    }
  };

  const openSlugModal = () => {
    setSlugDraft(node.slug);
    setSlugError(null);
    setSlugModal(true);
  };

  const saveSlug = async () => {
    setSlugSaving(true);
    try {
      const res = await patchNode(accountId, node.id, {
        slug: slugDraft,
        updatedAt: node.updatedAt,
      });
      onSlugChange?.(res.slug ?? slugDraft, res.updatedAt);
      setSlugModal(false);
    } catch (e) {
      setSlugError(e instanceof Error ? e.message : String(e));
    } finally {
      setSlugSaving(false);
    }
  };

  return (
    <div className="w-64 border-l p-4 overflow-y-auto space-y-4">
      <details open>
        <summary className="cursor-pointer font-semibold">Actions</summary>
        <div className="mt-2 space-y-4 text-sm">
          <div>
            <div className="font-semibold">Visibility</div>
            <div className="mt-1 flex flex-col gap-1">
              <button type="button" className="underline text-left" onClick={handlePublish}>
                Publish
              </button>
              <button type="button" className="underline text-left" onClick={handleHide}>
                Hide
              </button>
              <button type="button" className="underline text-left" onClick={handleArchive}>
                Archive
              </button>
            </div>
          </div>
          <div>
            <div className="font-semibold">Access</div>
            <div className="mt-1 flex flex-col gap-1">
              <button type="button" className="underline text-left" onClick={handleMakePublic}>
                Public
              </button>
              <button type="button" className="underline text-left" onClick={handleMakePremium}>
                Premium
              </button>
            </div>
          </div>
          <div className="flex flex-col gap-1">
            <button type="button" className="underline text-left" onClick={handleDuplicate}>
              Duplicate
            </button>
            <button type="button" className="underline text-left" onClick={handlePreview}>
              Preview
            </button>
          </div>
        </div>
      </details>
      {nodesCover ? (
        <details open>
          <summary className="cursor-pointer font-semibold">Cover</summary>
          <div className="mt-2 space-y-2 text-sm">
            {node.coverUrl ? (
              <div className="relative">
                <img
                  src={node.coverUrl}
                  alt={node.coverAlt || ''}
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
                        alt: '',
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
            {node.coverUrl ? (
              <input
                type="text"
                className="w-full border rounded px-2 py-1 text-xs"
                placeholder="Alt text"
                value={node.coverAlt}
                onChange={(e) =>
                  onCoverChange?.({
                    assetId: node.coverAssetId,
                    url: node.coverUrl,
                    alt: e.target.value,
                    meta: node.coverMeta,
                  })
                }
              />
            ) : null}
            {uploadError && <div className="text-xs text-red-600">{uploadError}</div>}
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
          <div>
            <div className="text-xs mb-1">ID</div>
            <div className="flex gap-1">
              <input
                className="w-full border rounded px-1 py-0.5 text-xs"
                readOnly
                value={node.id}
              />
              <button
                type="button"
                className="text-xs px-2 py-0.5 border rounded"
                onClick={() => copy(node.id)}
              >
                Copy
              </button>
            </div>
          </div>
          <div>
            <div className="text-xs mb-1 flex items-center justify-between">
              <span>Slug</span>
              {canEditSlug ? (
                <button type="button" className="text-xs underline" onClick={openSlugModal}>
                  Edit slug
                </button>
              ) : null}
            </div>
            <div className="flex gap-1">
              <input
                className="w-full border rounded px-1 py-0.5 text-xs"
                readOnly
                value={node.slug}
              />
              <button
                type="button"
                className="text-xs px-2 py-0.5 border rounded"
                onClick={() => copy(node.slug)}
              >
                Copy
              </button>
            </div>
          </div>
          <div>Author: {node.authorId || '-'}</div>
          <div>Created: {node.createdAt ? new Date(node.createdAt).toLocaleString() : '-'}</div>
          <div>Updated: {node.updatedAt ? new Date(node.updatedAt).toLocaleString() : '-'}</div>
        </div>
      </details>
      <details open>
        <summary className="cursor-pointer font-semibold">Auto-links</summary>
        <div className="mt-2 text-sm text-gray-500">No auto-links.</div>
      </details>
      <details open>
        <summary className="cursor-pointer font-semibold">Publication</summary>
        <div className="mt-2 space-y-2 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={node.isPublic}
              onChange={(e) => handleStatusChange(e.target.checked)}
              disabled={statusSaving}
            />
            Published
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={node.allowFeedback}
              onChange={(e) => handleAllowFeedbackChange(e.target.checked)}
              disabled={allowSaving}
            />
            Allow comments
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={node.premiumOnly}
              onChange={(e) => handlePremiumOnlyChange(e.target.checked)}
              disabled={premiumSaving}
            />
            Premium only
          </label>
          {node.updatedAt !== node.createdAt ? (
            <div>
              <div className="text-xs mb-1">Schedule</div>
              <input
                type="datetime-local"
                className="w-full border rounded px-1 py-0.5 text-xs"
                value={scheduleValue}
                onChange={(e) => handleScheduleChange(e.target.value)}
                disabled={scheduleSaving}
              />
            </div>
          ) : null}
        </div>
      </details>
      {canModerate ? <div>Type: {node.nodeType}</div> : null}

      {slugModal ? (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-800 p-4 rounded shadow-lg w-80">
            <div className="text-sm mb-2">Changing slug may break existing links.</div>
            <input
              className="w-full border rounded px-2 py-1 text-sm"
              value={slugDraft}
              onChange={(e) => setSlugDraft(e.target.value)}
            />
            {slugError && <div className="text-xs text-red-600 mt-1">{slugError}</div>}
            <div className="mt-4 flex justify-end gap-2 text-sm">
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={() => setSlugModal(false)}
                disabled={slugSaving}
              >
                Cancel
              </button>
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={saveSlug}
                disabled={slugSaving}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {editing && node.coverUrl ? (
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
                image={node.coverUrl}
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
                  transform: 'translate(-50%, -50%)',
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
              <button type="button" className="px-2 py-1 border rounded" onClick={applyMeta}>
                Apply
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
