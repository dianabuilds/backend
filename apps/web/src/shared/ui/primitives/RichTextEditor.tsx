import React from 'react';

type RteProps = {
  value: string; // HTML
  onChange: (html: string) => void;
  label?: string;
  placeholder?: string;
  className?: string;
  modules?: Record<string, any>;
  readOnly?: boolean;
};

const DEFAULT_MODULES = {
  toolbar: [
    ['bold', 'italic', 'underline', 'strike'],
    ['blockquote', 'code-block'],
    [{ header: 1 }, { header: 2 }],
    [{ list: 'ordered' }, { list: 'bullet' }],
    [{ script: 'sub' }, { script: 'super' }],
    [{ indent: '-1' }, { indent: '+1' }],
    [{ direction: 'rtl' }],
    [{ size: ['small', false, 'large', 'huge'] }],
    [{ header: [1, 2, 3, 4, 5, 6, false] }],
    [{ color: [] }, { background: [] }],
    [{ font: [] }],
    [{ align: [] }, 'image'],
    ['clean'],
  ],
};

export function RichTextEditor({ value, onChange, label, placeholder, className = '', modules, readOnly = false }: RteProps) {
  const editorRef = React.useRef<HTMLDivElement>(null);
  const quillRef = React.useRef<any>(null);
  const onChangeRef = React.useRef(onChange);
  const readOnlyRef = React.useRef(readOnly);

  React.useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  React.useEffect(() => {
    readOnlyRef.current = readOnly;
  }, [readOnly]);

  React.useEffect(() => {
    let mounted = true;
    const editorEl = editorRef.current;
    (async () => {
      const Quill = (await import('quill')).default;
      if (!mounted || !editorEl) return;
      const toolbarModules = modules || DEFAULT_MODULES;
      const q = new Quill(editorEl, {
        theme: 'snow',
        placeholder: placeholder || 'Enter your content…',
        modules: toolbarModules,
        readOnly,
      });
      quillRef.current = q;
      q.on('text-change', () => {
        if (readOnlyRef.current) return;
        onChangeRef.current(q.root.innerHTML);
      });
    })();
    return () => {
      mounted = false;
      if (quillRef.current) {
        quillRef.current.off('text-change');
        quillRef.current = null;
      }
      if (editorEl) {
        editorEl.innerHTML = '';
      }
    };
  }, [modules, placeholder, readOnly]);

  React.useEffect(() => {
    const q = quillRef.current;
    if (!q) return;
    if (value !== q.root.innerHTML) {
      const sel = q.getSelection();
      q.clipboard.dangerouslyPasteHTML(value || '');
      if (sel) q.setSelection(sel);
    }
  }, [value]);

  React.useEffect(() => {
    const q = quillRef.current;
    if (!q) return;
    q.enable(!readOnly);
    try {
      const toolbar = q.getModule('toolbar');
      if (toolbar?.container) toolbar.container.style.display = readOnly ? 'none' : '';
    } catch {}
  }, [readOnly]);

  return (
    <div className={`input-root ${className}`}>
      {label && (
        <label className="input-label">
          <span className="input-label">{label}</span>
        </label>
      )}
      <div className={`input-wrapper ${label ? 'mt-1.5' : ''}`}>
        <div
          className={`rounded-lg border ${
            readOnly
              ? 'border-gray-200 bg-gray-50 dark:border-dark-600 dark:bg-dark-700'
              : 'border-gray-300 dark:border-dark-450 bg-white dark:bg-dark-650'
          }`}
        >
          <div ref={editorRef} className="min-h-40" />
        </div>
      </div>
    </div>
  );
}

