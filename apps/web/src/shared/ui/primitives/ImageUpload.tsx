import React from 'react';

type ImageUploadProps = {
  value?: File | null;
  onChange: (file: File | null, previewUrl?: string) => void;
  label?: string;
  className?: string;
  disabled?: boolean;
};

export function ImageUpload({ value, onChange, label, className = '', disabled = false }: ImageUploadProps) {
  const [preview, setPreview] = React.useState<string | undefined>();
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (!value) {
      setPreview(undefined);
      if (!disabled) onChange(null);
      return;
    }
    if (disabled) return;
    const reader = new FileReader();
    reader.onload = () => {
      const data = String(reader.result || '');
      setPreview(data);
      onChange(value, data);
    };
    reader.readAsDataURL(value);
  }, [value, disabled, onChange]);

  const triggerUpload = () => {
    if (disabled) return;
    inputRef.current?.click();
  };

  const clear = () => {
    if (disabled) return;
    setPreview(undefined);
    onChange(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className={`input-root ${className}`}>
      {label && (
        <label className="input-label">
          <span className="input-label">{label}</span>
        </label>
      )}
      <div className={`input-wrapper ${label ? 'mt-1.5' : ''}`}>
        <div className={`rounded-lg border border-dashed ${disabled ? 'border-gray-200 bg-gray-50 text-gray-400 dark:border-dark-600 dark:bg-dark-700 dark:text-dark-300' : 'border-gray-300'} p-3 text-center`}>
          {preview ? (
            <div className="space-y-2">
              {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
              <img src={preview} alt="Preview" className="mx-auto max-h-40 rounded" />
              <div className="flex justify-center gap-2">
                <button className="btn-base btn bg-gray-150 text-gray-900 hover:bg-gray-200 disabled:opacity-60" type="button" onClick={triggerUpload} disabled={disabled}>
                  Replace
                </button>
                <button className="btn-base btn bg-red-600 text-white hover:bg-red-700 disabled:opacity-60" type="button" onClick={clear} disabled={disabled}>
                  Remove
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-sm text-gray-600 dark:text-dark-200">Drop an image here or choose a file.</div>
              <button className="btn-base btn disabled:opacity-60" type="button" onClick={triggerUpload} disabled={disabled}>
                Choose file
              </button>
            </div>
          )}
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => onChange(e.currentTarget.files?.[0] || null)}
            disabled={disabled}
          />
        </div>
      </div>
    </div>
  );
}
