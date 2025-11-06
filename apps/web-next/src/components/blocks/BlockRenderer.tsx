import type { ReactElement } from "react";

import type { SitePageBlock } from "@caves/site-shared/site-page";

import styles from "./BlockRenderer.module.css";
import { CollectionBlock } from "./CollectionBlock";
import { HeroBlock } from "./HeroBlock";
import { PlaceholderBlock } from "./PlaceholderBlock";

type BlockComponent = (props: {
  block: SitePageBlock;
  position: number;
}) => ReactElement | null;

const COMPONENTS: Record<string, BlockComponent> = {
  hero: HeroBlock,
  dev_blog_list: CollectionBlock,
  article_list: CollectionBlock,
  quests_carousel: CollectionBlock,
  nodes_carousel: CollectionBlock,
  popular_carousel: CollectionBlock,
  editorial_picks: CollectionBlock,
  recommendations: CollectionBlock,
  custom_carousel: CollectionBlock,
};

type BlockRendererProps = {
  block: SitePageBlock;
  position: number;
};

export function BlockRenderer({
  block,
  position,
}: BlockRendererProps): ReactElement | null {
  if (block.enabled === false) {
    return null;
  }

  const Component = COMPONENTS[block.type] ?? PlaceholderBlock;

  return (
    <section className={styles.block} aria-live="polite">
      <Component block={block} position={position} />
    </section>
  );
}
