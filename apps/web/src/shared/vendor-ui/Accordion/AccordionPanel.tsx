// Import Dependencies
import { ReactNode, ComponentPropsWithoutRef, ElementType } from "react";

// Local Imports
import { Collapse } from "@ui/index.ts";
import { useAccordionContext } from "./Accordion.context.ts";
import { useAccordionItemContext } from "./AccordionItem.context.ts";
import { PolymorphicComponentProps } from "@/@types/polymorphic.tsx";

// ------------------------------------------------------------------------

type AccordionPanelOwnProps<E extends ElementType = "div"> = {
  children?: ReactNode | ((props: { open: boolean }) => ReactNode);
  className?: string | ((props: { open: boolean }) => string);
  collapseProps?: ComponentPropsWithoutRef<typeof Collapse>;
  component?: E;
}

export type AccordionPanelProps<E extends ElementType = "div"> =
  PolymorphicComponentProps<E, AccordionPanelOwnProps<E>>;

const AccordionPanel = (props: AccordionPanelProps) => {
  const { children, className, collapseProps, ...rest } = props;
  const ctx = useAccordionContext();
  const { value } = useAccordionItemContext();

  const isActive = ctx.isItemActive(value);

  return (
    <Collapse
      {...collapseProps}
      in={isActive}
      transitionDuration={ctx.transitionDuration}
      role="panel"
      id={`${ctx.panelId}-${value}`}
      aria-labelledby={`${ctx.buttonId}-${value}`}
    >
      <div
        className={
          typeof className === "function"
            ? className({ open: isActive })
            : className
        }
        {...rest}
      >
        {typeof children === "function"
          ? children({ open: isActive })
          : children}
      </div>
    </Collapse>
  );
};

export { AccordionPanel };
