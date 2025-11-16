import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

type PageBodyProps = {
  children: ReactNode;
  className?: string;
  fullWidth?: boolean;
};

export function PageBody({ children, className, fullWidth = false }: PageBodyProps) {
  return (
    <section
      className={cn(
        "mt-6 w-full",
        fullWidth ? undefined : "mx-auto max-w-6xl",
        "space-y-6",
        className
      )}
    >
      {children}
    </section>
  );
}
