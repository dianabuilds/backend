import { useEffect, useRef, useState, type InputHTMLAttributes } from "react";

import { getSuggestions, mergeTags } from "../utils/tagManager";

interface TagInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange"> {
  value?: string[];
  onChange?: (tags: string[]) => void;
}

export default function TagInput({
  value = [],
  onChange,
  placeholder = "Добавьте теги и нажмите Enter",
  id,
  className,
  ...rest
}: TagInputProps) {
  const [tags, setTags] = useState<string[]>(mergeTags(value));
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Sync internal state when value prop changes (e.g. after async load)
  useEffect(() => {
    const next = mergeTags(value || []);
    // Avoid unnecessary rerenders
    const same = next.length === tags.length && next.every((t, i) => t === tags[i]);
    if (!same) setTags(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [Array.isArray(value) ? value.join("\u0001") : String(value || "")]);

  const commit = (raw: string) => {
    const items = raw
      .split(/[,\s\n]+/g)
      .map((s) => s.trim())
      .filter(Boolean);
    if (items.length === 0) return;
    const next = mergeTags([...tags, ...items]);
    setTags(next);
    onChange?.(next);
    setInput("");
  };

  const removeAt = (idx: number) => {
    const next = tags.filter((_, i) => i !== idx);
    setTags(next);
    onChange?.(next);
  };

  return (
    <div
      className={`border rounded px-2 py-1 flex items-center flex-wrap gap-1 ${className || ""}`}
    >
      {tags.map((t, i) => (
        <span
          key={`${t}-${i}`}
          className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded"
        >
          {t}
          <button
            className="text-xs leading-none"
            onClick={() => removeAt(i)}
            title="Удалить тег"
          >
            ×
          </button>
        </span>
      ))}
      <input
        ref={inputRef}
        id={id}
        className="flex-1 min-w-[140px] py-1 outline-none"
        placeholder={placeholder}
        list="tag-suggestions"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            commit(input);
          } else if (e.key === "," && !e.shiftKey) {
            e.preventDefault();
            commit(input);
          } else if (e.key === " " && !e.shiftKey) {
            e.preventDefault();
            commit(input);
          } else if (
            e.key === "Backspace" &&
            input.length === 0 &&
            tags.length > 0
          ) {
            removeAt(tags.length - 1);
          }
        }}
        {...rest}
      />
      <datalist id="tag-suggestions">
        {getSuggestions(input).map((s) => (
          <option value={s} key={s} />
        ))}
      </datalist>
    </div>
  );
}
