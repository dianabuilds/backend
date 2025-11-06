import type { SiteBlock, SiteBlockBinding } from "@caves/site-shared/site-page";

import styles from "./global-blocks-panel.module.css";

type GlobalBlockEntry = {
  block: SiteBlock;
  binding?: SiteBlockBinding | null;
};

type GlobalBlocksPanelProps = {
  entries: GlobalBlockEntry[];
};

export function GlobalBlocksPanel({ entries }: GlobalBlocksPanelProps) {
  if (entries.length === 0) {
    return null;
  }

  return (
    <section className={styles.container}>
      <header>
        <h3>Общие блоки</h3>
        <p className={styles.hint}>
          Показаны блоки со scope <code>shared</code>, которые подтягиваются в
          страницу из библиотеки.
        </p>
      </header>
      <div className={styles.list}>
        {entries.map(({ block, binding }, index) => {
          const locale = binding?.locale ?? block.locale ?? "—";
          const section = binding?.section ?? block.sections?.[0] ?? "—";
          const key = binding?.key ?? block.key ?? block.id ?? `shared-${index}`;
          return (
            <article key={key} className={styles.item}>
              <header className={styles.itemHeader}>
                <div>
                  <h4>{block.title ?? key}</h4>
                  <p className={styles.key}>key: {key}</p>
                </div>
                <p className={styles.version}>v{block.version}</p>
              </header>
              <dl className={styles.meta}>
                <dt>section</dt>
                <dd>{section}</dd>
                <dt>locale</dt>
                <dd>{locale}</dd>
                <dt>requires publisher</dt>
                <dd>{block.requiresPublisher ? "Да" : "Нет"}</dd>
                <dt>updated</dt>
                <dd>{formatTime(block.updatedAt) ?? "—"}</dd>
                <dt>status</dt>
                <dd>{block.status}</dd>
                {binding ? (
                  <>
                    <dt>position</dt>
                    <dd>{binding.position}</dd>
                  </>
                ) : null}
              </dl>
              <details className={styles.details}>
                <summary>payload</summary>
                <pre>{JSON.stringify(block.data, null, 2)}</pre>
              </details>
              {Object.keys(block.meta ?? {}).length > 0 ? (
                <details className={styles.details}>
                  <summary>meta</summary>
                  <pre>{JSON.stringify(block.meta, null, 2)}</pre>
                </details>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}

function formatTime(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}
