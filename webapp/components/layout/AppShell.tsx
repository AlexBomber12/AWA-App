"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useMemo } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/roi", label: "ROI" },
  { href: "/sku", label: "SKU" },
  { href: "/ingest", label: "Ingest" },
  { href: "/returns", label: "Returns" },
  { href: "/inbox", label: "Inbox" },
  { href: "/decision", label: "Decision" },
  { href: "/settings", label: "Settings" },
];

const appEnvLabel = (process.env.NEXT_PUBLIC_APP_ENV ?? "local").toUpperCase();

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const activeHref = useMemo(() => pathname ?? "/dashboard", [pathname]);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="hidden border-r border-border bg-muted/30 lg:flex lg:w-64 lg:flex-col">
        <div className="px-6 py-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">AWA</p>
          <p className="text-lg font-semibold">Operator Console</p>
        </div>
        <nav className="flex-1 space-y-1 px-2 pb-6">
          {NAV_ITEMS.map((item) => {
            const isActive = activeHref.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-muted/60",
                  isActive ? "bg-muted text-foreground" : "text-muted-foreground"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="flex flex-col gap-4 border-b border-border bg-background/90 px-4 py-4 shadow-sm backdrop-blur lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Amazon Wholesale Analytics
            </p>
            <h1 className="text-2xl font-semibold">Operator Console</h1>
          </div>
          <div className="flex flex-col items-start gap-2 text-sm lg:flex-row lg:items-center">
            <span className="rounded-full border border-brand/40 bg-brand/10 px-3 py-1 font-medium text-brand">
              {appEnvLabel}
            </span>
            <Button variant="outline" size="sm">
              UI systems arriving soon
            </Button>
          </div>
        </header>
        <div className="flex flex-1 flex-col lg:flex-row">
          <div className="border-b border-border bg-muted/50 px-4 py-2 lg:hidden">
            <div className="flex items-center gap-3 overflow-x-auto">
              {NAV_ITEMS.map((item) => {
                const isActive = activeHref.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "rounded-full px-3 py-1 text-xs font-medium",
                      isActive
                        ? "bg-brand text-brand-foreground"
                        : "bg-background text-muted-foreground border border-border"
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
          <main className="flex-1 overflow-y-auto bg-muted/30 px-4 py-8 lg:px-10">{children}</main>
        </div>
      </div>
    </div>
  );
}
