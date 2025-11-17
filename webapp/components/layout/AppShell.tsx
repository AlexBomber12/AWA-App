"use client";

import Link from "next/link";
import { SessionProvider } from "next-auth/react";
import type { Session } from "next-auth";
import { usePathname } from "next/navigation";
import { type ReactNode, useMemo } from "react";

import { ReactQueryProvider } from "@/components/providers/ReactQueryProvider";
import { ToastProvider } from "@/components/providers/ToastProvider";
import { Button } from "@/components/ui";
import { type Action, type Resource, type Role, usePermissions } from "@/lib/permissions";
import { cn } from "@/lib/utils";

type NavItem = {
  href: string;
  label: string;
  permission?: {
    resource: Resource;
    action: Action;
  };
};

const toNavTestId = (label: string) =>
  label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard", permission: { resource: "dashboard", action: "view" } },
  { href: "/roi", label: "ROI", permission: { resource: "roi", action: "view" } },
  { href: "/sku", label: "SKU", permission: { resource: "sku", action: "view" } },
  { href: "/ingest", label: "Ingest", permission: { resource: "ingest", action: "view" } },
  { href: "/returns", label: "Returns", permission: { resource: "returns", action: "view" } },
  { href: "/inbox", label: "Inbox", permission: { resource: "inbox", action: "view" } },
  { href: "/decision", label: "Decision Engine", permission: { resource: "decision", action: "view" } },
  { href: "/settings", label: "Settings", permission: { resource: "settings", action: "view" } },
];

const appEnvLabel = (process.env.NEXT_PUBLIC_APP_ENV ?? "local").toUpperCase();
const viewerFallback: Role[] = ["viewer"];

const useSafePathname = () => {
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    return usePathname();
  } catch {
    return null;
  }
};

type AppShellProps = {
  children: ReactNode;
  initialSession?: Session | null;
  initialPath?: string;
};

export function AppShell({ children, initialSession, initialPath }: AppShellProps) {
  return (
    <SessionProvider session={initialSession}>
      <ReactQueryProvider>
        <ToastProvider>
          <AppShellContent initialPath={initialPath}>{children}</AppShellContent>
        </ToastProvider>
      </ReactQueryProvider>
    </SessionProvider>
  );
}

type AppShellContentProps = {
  children: ReactNode;
  initialPath?: string;
};

function AppShellContent({ children, initialPath }: AppShellContentProps) {
  const currentPathname = useSafePathname();
  const { roles, can } = usePermissions();
  const activeHref = useMemo(() => {
    if (initialPath) {
      return initialPath;
    }
    return currentPathname ?? "/dashboard";
  }, [initialPath, currentPathname]);

  const menuRoles = roles.length > 0 ? roles : viewerFallback;

  const visibleNavItems = useMemo(
    () =>
      NAV_ITEMS.filter((item) => {
        if (!item.permission) {
          return true;
        }

        return can({ ...item.permission, roles: menuRoles });
      }),
    [can, menuRoles]
  );

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <aside className="hidden border-r border-border bg-muted/30 lg:flex lg:w-64 lg:flex-col">
        <div className="px-6 py-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">AWA</p>
          <p className="text-lg font-semibold">Operator Console</p>
        </div>
        <nav className="flex-1 space-y-1 px-2 pb-6">
          {visibleNavItems.map((item) => {
            const isActive = activeHref.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                data-testid={`nav-${toNavTestId(item.label)}`}
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
              {visibleNavItems.map((item) => {
                const isActive = activeHref.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    data-testid={`nav-${toNavTestId(item.label)}`}
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
