// Import Dependencies
import clsx from "clsx";
import { ComponentPropsWithoutRef, forwardRef, ForwardedRef } from "react";

// ----------------------------------------------------------------------

export type SkeletonProps = {
  animate?: boolean;
  className?: string;
} & ComponentPropsWithoutRef<"div">;

const Skeleton = forwardRef((
  props: SkeletonProps,
  ref: ForwardedRef<HTMLDivElement>
) => {
  const { animate = true, className, ...rest } = props;
  return (
    <div
      className={clsx(
        "skeleton relative overflow-hidden",
        animate && "animate-wave before:absolute before:inset-0",
        className,
      )}
      ref={ref}
      {...rest}
    />
  );
});

Skeleton.displayName = "Skeleton";

export { Skeleton };
/**
 * @group: ui-kit
 * @component: Skeleton
 * @status: draft
 * @docs: ts/demo/public/md/components/skeleton
 * @since: template-1.3.2
 */
