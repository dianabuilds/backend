export type RenderResult = {
  html: string;
  status?: number;
  headers?: Record<string, string>;
  initialData?: unknown;
  head?: {
    headTags?: string;
    htmlAttributes?: string;
    bodyAttributes?: string;
  };
  entryClient?: string;
};

export type RenderFunction = (url: string) => Promise<RenderResult | null>;
