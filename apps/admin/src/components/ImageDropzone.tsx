import { useCallback, useEffect, useRef, useState } from 'react';

import { useAccount } from '../account/AccountContext';
import { accountApi } from '../api/accountApi';
import { extractUrlFromUploadResponse, resolveBackendUrl } from '../utils/url';

interface ImageDropzoneProps {
  value?: string | null;
  onChange?: (dataUrl: string | null) => void;
  className?: string;
  height?: number;
}

export default function ImageDropzone({
  value,
  onChange,
  className = '',
  height = 140,
}: ImageDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const { accountId } = useAccount();

  // Локальный URL для мгновенного превью после загрузки
  const [internalUrl, setInternalUrl] = useState<string | null>(resolveBackendUrl(value) ?? null);
  // Синхронизация при внешнем изменении value
  useEffect(() => {
    setInternalUrl(resolveBackendUrl(value) ?? null);
  }, [value]);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      const file = files[0];
      if (!file.type.startsWith('image/')) {
        setError('Можно загружать только изображения');
        return;
      }
      const form = new FormData();
      form.append('file', file);
      setError(null);
      try {
        const res = await accountApi.request('/admin/media', {
          method: 'POST',
          body: form,
          raw: true,
          accountId,
        });
        const url = extractUrlFromUploadResponse(res.data, res.response.headers);
        if (!url) {
          setError('Сервер не вернул URL загруженного файла');
          return;
        }
        // Обновляем локальное превью и поднимаем значение наверх
        setInternalUrl(url);
        onChange?.(url);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Не удалось загрузить изображение');
      }
    },
    [onChange, accountId],
  );

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const onClick = () => inputRef.current?.click();

  const displaySrc = resolveBackendUrl(internalUrl || value || null) || undefined;

  return (
    <div className={className}>
      {displaySrc ? (
        <div className="relative">
          <img
            src={displaySrc}
            alt=""
            className="w-full rounded border object-cover"
            style={{ height }}
            onError={() => setError('Не удалось отобразить изображение')}
          />
          <div className="absolute top-2 right-2 flex gap-2">
            <button
              type="button"
              className="text-xs px-2 py-1 rounded bg-white/90 border focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={() => {
                setInternalUrl(null);
                onChange?.(null);
              }}
              title="Remove"
              aria-label="Remove image"
            >
              Remove
            </button>
            <button
              type="button"
              className="text-xs px-2 py-1 rounded bg-white/90 border focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={onClick}
              title="Replace"
              aria-label="Replace image"
            >
              Replace
            </button>
          </div>
        </div>
      ) : (
        <div
          className={`rounded border-2 border-dashed ${dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300'} cursor-pointer flex items-center justify-center text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500`}
          style={{ height }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={onClick}
          role="button"
          tabIndex={0}
          aria-label="Upload image"
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onClick();
            }
          }}
        >
          <div className="text-center px-3">
            <div className="mx-auto mb-2 text-3xl">🖼️</div>
            <div className="font-medium mb-0.5">Перетащите изображение</div>
            <div className="text-xs text-gray-600">или нажмите, чтобы выбрать файл</div>
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
