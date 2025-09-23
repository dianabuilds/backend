import { createSafeContext } from "@utils/createSafeContext.tsx";

type AccordionContextType = {
  isItemActive: (value: string) => boolean;
  onChange: (value: string) => void;
  buttonId: string;
  panelId: string;
  transitionDuration?: number;
  loop?: boolean;
}

export const [AccordionContextProvider, useAccordionContext] =
  createSafeContext<AccordionContextType>(
    "useAccordionContext must be used within AccordionProvider",
  );
