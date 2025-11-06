import Link from "next/link";
import type { Route } from "next";
import styles from "./not-found.module.css";

export default function NotFound() {
  return (
    <main className={styles.container}>
      <h1>Страница не найдена</h1>
      <p>
        Похоже, такой slug ещё не опубликован. Проверьте, что страница
        существует в Site Editor и имеет опубликованную версию.
      </p>
      <Link href={"/" as Route} className={styles.link}>
        Вернуться на главную
      </Link>
    </main>
  );
}
