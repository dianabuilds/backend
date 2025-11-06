type SSRContext = {
  route: string;
  slug: string;
  locale?: string | null;
};

type SuccessExtra = {
  status: number;
  source: string;
  etag?: string | null;
  blocks?: number;
  fallbacks?: number;
};

const MS_IN_NS = 1_000_000;

export function createSSRLogger(context: SSRContext) {
  const startedAt = process.hrtime.bigint();
  const timestamp = new Date().toISOString();
  let finished = false;

  const finish = (payload: {
    level: "info" | "error";
    status: number;
    message?: string;
    errorStack?: string;
    source?: string;
    etag?: string | null;
    blocks?: number;
    fallbacks?: number;
  }) => {
    if (finished) {
      return;
    }
    finished = true;
    const duration = Number(process.hrtime.bigint() - startedAt) / MS_IN_NS;
    const logEntry = {
      ...context,
      ...payload,
      durationMs: Math.round(duration * 1000) / 1000,
      timestamp,
    };
    if (payload.level === "error") {
      console.error("[ssr]", JSON.stringify(logEntry));
    } else {
      console.info("[ssr]", JSON.stringify(logEntry));
    }
  };

  return {
    success(extra: SuccessExtra) {
      finish({
        level: "info",
        status: extra.status,
        source: extra.source,
        etag: extra.etag ?? null,
        blocks: extra.blocks,
        fallbacks: extra.fallbacks,
      });
    },
    miss() {
      finish({
        level: "info",
        status: 404,
        message: "Page not found",
      });
    },
    error(error: unknown) {
      const message = error instanceof Error ? error.message : String(error);
      const errorStack =
        error instanceof Error && typeof error.stack === "string"
          ? error.stack
          : undefined;
      finish({
        level: "error",
        status: 500,
        message,
        errorStack,
      });
    },
  };
}
