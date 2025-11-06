import styles from "./page.module.css";

const editorOrigin =
  process.env.NEXT_PUBLIC_LEGACY_SITE_EDITOR_URL ??
  "http://localhost:5173/management/site-editor";

export const dynamic = "force-static";

export default function LegacySiteEditorPage() {
  return (
    <main className={styles.container}>
      <section className={styles.panel}>
        <h1>Текущий редактор (SPA)</h1>
        <p>
          Этот экран подгружает существующую версию Site Editor из Vite-приложения.
          После миграции блоков в Next.js можно будет заменить встраивание нативными страницами.
        </p>
        <p className={styles.hint}>
          Источник по умолчанию:{" "}
          <code>{editorOrigin}</code>
        </p>
        <p>
          Измени переменную{" "}
          <code>NEXT_PUBLIC_LEGACY_SITE_EDITOR_URL</code> в окружении, чтобы
          указывать на staging/prod.
        </p>
      </section>
      <div className={styles.viewer}>
        <iframe
          title="Legacy Site Editor"
          src={editorOrigin}
          className={styles.frame}
          allow="clipboard-write; clipboard-read"
        />
      </div>
    </main>
  );
}
