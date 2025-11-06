import type { ReactElement } from "react";

import type { SitePageBlock } from "@caves/site-shared/site-page";

import styles from "./BlockRenderer.module.css";

export function PlaceholderBlock({
  block,
}: {
  block: SitePageBlock;
  position: number;
}): ReactElement {
  return (
    <div className={styles.placeholder}>
      <strong>Пока нет готового рендера для блока «{block.type}».</strong>
      <span>
        Параметры блока можно посмотреть в Site Editor. Ниже показан текущий
        payload.
      </span>
      <pre>{JSON.stringify(block, null, 2)}</pre>
    </div>
  );
}
