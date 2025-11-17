import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

import { Breadcrumbs, type BreadcrumbItem } from "./Breadcrumbs";

const toTestId = (value: string) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  className?: string;
  children?: ReactNode;
  testId?: string;
};

export function PageHeader({
  title,
  description,
  actions,
  breadcrumbs,
  className,
  children,
  testId,
}: PageHeaderProps) {
  const resolvedTestId = testId ?? `page-header-${toTestId(title)}`;
  return (
    <div className={cn("mx-auto w-full max-w-6xl space-y-3", className)} data-testid={resolvedTestId}>
      {breadcrumbs && breadcrumbs.length > 0 ? (
        <Breadcrumbs items={breadcrumbs} className="text-xs uppercase tracking-wide" />
      ) : null}
      <div className="flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
        <div className="space-y-2">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
            {description ? <p className="text-base text-muted-foreground">{description}</p> : null}
          </div>
          {children}
        </div>
        {actions ? <div className="flex w-full justify-end sm:w-auto">{actions}</div> : null}
      </div>
    </div>
  );
}
