type EditorData = {
  time?: number;
  version?: string;
  blocks?: Array<{
    id?: string;
    type: string;
    data: any;
  }>;
};

interface Props {
  value?: EditorData | null;
  className?: string;
}

/**
 * Render-only viewer for Editor.js data.
 * Supports: paragraph, header, list, checklist, quote, image, table, delimiter.
 */
export default function EditorJSViewer({ value, className }: Props) {
  const data = (value && typeof value === "object" ? value : { blocks: [] }) as EditorData;
  const blocks = Array.isArray(data.blocks) ? data.blocks : [];

  const renderHTML = (html?: string) => {
    return <span dangerouslySetInnerHTML={{ __html: html || "" }} />;
  };

  // Нормализация URL изображений (см. также в редакторе)
  const resolveUrl = (u?: string): string => {
    if (!u) return "";
    try {
      let base = "";
      const envBase = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
      if (envBase) {
        base = envBase;
      } else if (typeof window !== "undefined" && window.location) {
        const port = window.location.port;
        if (port && ["5173", "5174", "5175", "5176"].includes(port)) {
          base = `${window.location.protocol}//${window.location.hostname}:8000`;
        } else {
          base = `${window.location.protocol}//${window.location.host}`;
        }
      }
      const urlObj = new URL(u, base || (typeof window !== "undefined" ? window.location.origin : undefined));
      if (typeof window !== "undefined" && window.location?.protocol === "https:" && urlObj.protocol === "http:") {
        urlObj.protocol = "https:";
      }
      return urlObj.toString();
    } catch {
      return u || "";
    }
  };

  const renderBlock = (block: any, idx: number) => {
    const type = block?.type;
    const d = block?.data ?? {};

    switch (type) {
      case "paragraph":
        return (
          <p key={block.id || idx} className="leading-6">
            {renderHTML(d.text)}
          </p>
        );
      case "header": {
        const level = Math.min(Math.max(parseInt(String(d.level || 2), 10) || 2, 1), 6);
        const Tag: any = `h${level}`;
        const levelCls =
          level === 1
            ? "text-3xl font-bold"
            : level === 2
            ? "text-2xl font-bold"
            : level === 3
            ? "text-xl font-semibold"
            : level === 4
            ? "text-lg font-semibold"
            : "text-base font-semibold";
        return (
          <Tag key={block.id || idx} className={`${levelCls}`}>
            {renderHTML(d.text)}
          </Tag>
        );
      }
      case "list": {
        const ordered = (d.style || "").toLowerCase() === "ordered";
        const items = Array.isArray(d.items) ? d.items : [];
        const ListTag = (ordered ? "ol" : "ul") as "ul" | "ol";
        const listCls = ordered ? "list-decimal pl-5 space-y-1" : "list-disc pl-5 space-y-1";
        return (
          <ListTag key={block.id || idx} className={listCls}>
            {items.map((it: any, i: number) => (
              <li key={i}>{renderHTML(typeof it === "string" ? it : it?.content || it?.text || "")}</li>
            ))}
          </ListTag>
        );
      }
      case "checklist": {
        const items = Array.isArray(d.items) ? d.items : [];
        return (
          <ul key={block.id || idx} className="pl-1 space-y-1">
            {items.map((it: any, i: number) => (
              <li key={i} className="flex items-start gap-2">
                <input type="checkbox" checked={!!it.checked} readOnly className="mt-1" />
                <span>{renderHTML(it?.text)}</span>
              </li>
            ))}
          </ul>
        );
      }
      case "quote":
        return (
          <figure key={block.id || idx} className="my-2">
            <blockquote className="border-l-4 pl-4 italic opacity-90">{renderHTML(d.text)}</blockquote>
            {d.caption ? <figcaption className="text-sm opacity-70 mt-1">— {renderHTML(d.caption)}</figcaption> : null}
          </figure>
        );
      case "image": {
        const url = resolveUrl(d?.file?.url || d?.url);
        const caption = d?.caption;
        return (
          <figure key={block.id || idx} className="my-3">
            {url ? <img src={url} alt={typeof caption === "string" ? caption : ""} className="max-w-full rounded" /> : null}
            {caption ? <figcaption className="text-sm text-center opacity-70 mt-1">{renderHTML(caption)}</figcaption> : null}
          </figure>
        );
      }
      case "table": {
        const content: any[][] = Array.isArray(d?.content) ? d.content : [];
        return (
          <div key={block.id || idx} className="overflow-auto">
            <table className="min-w-full border border-gray-200 dark:border-gray-700 text-sm">
              <tbody>
                {content.map((row: any[], r: number) => (
                  <tr key={r} className="border-b border-gray-200 dark:border-gray-700">
                    {row.map((cell: any, c: number) => (
                      <td key={c} className="px-2 py-1 align-top border-r border-gray-200 dark:border-gray-700">
                        {renderHTML(typeof cell === "string" ? cell : cell?.text || "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }
      case "delimiter":
        return <hr key={block.id || idx} className="my-6 opacity-60" />;
      default:
        // Fallback: показать как есть
        return (
          <pre key={block.id || idx} className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto">
            {JSON.stringify(block, null, 2)}
          </pre>
        );
    }
  };

  return <article className={`space-y-3 ${className || ""}`}>{blocks.map(renderBlock)}</article>;
}
