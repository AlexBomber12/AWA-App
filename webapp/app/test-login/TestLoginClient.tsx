"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { Button } from "@/components/ui";
import type { Role } from "@/lib/permissions/server";

const ROLE_PRESETS: Record<"admin" | "ops" | "viewer", Role[]> = {
  admin: ["viewer", "ops", "admin"],
  ops: ["viewer", "ops"],
  viewer: ["viewer"],
};

export function TestLoginClient() {
  const router = useRouter();
  const [status, setStatus] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleLogin = async (roles: Role[]) => {
    setStatus(null);
    const response = await fetch("/api/test-session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ roles }),
    });

    if (!response.ok) {
      setStatus("Unable to establish a test session. Check the server logs for details.");
      return;
    }

    startTransition(() => {
      router.push("/dashboard");
      router.refresh();
    });
  };

  const handleLogout = async () => {
    setStatus(null);
    await fetch("/api/test-session", { method: "DELETE" });
    startTransition(() => {
      router.push("/test-login");
      router.refresh();
    });
  };

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-xl flex-col justify-center gap-6 px-4 py-12">
      <div className="space-y-2 text-center">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">QA utility</p>
        <h1 className="text-3xl font-semibold">Test session launcher</h1>
        <p className="text-sm text-muted-foreground">
          These controls are only available locally and in CI to help Playwright log in without Keycloak.
        </p>
      </div>

      <div className="rounded-2xl border border-border bg-background p-6 shadow-sm" data-testid="test-login-panel">
        <p className="text-sm font-medium text-muted-foreground">Sign in as:</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <Button
            data-testid="test-login-viewer"
            variant="outline"
            disabled={isPending}
            onClick={() => void handleLogin(ROLE_PRESETS.viewer)}
          >
            Viewer
          </Button>
          <Button
            data-testid="test-login-ops"
            variant="outline"
            disabled={isPending}
            onClick={() => void handleLogin(ROLE_PRESETS.ops)}
          >
            Ops
          </Button>
          <Button
            data-testid="test-login-admin"
            variant="default"
            disabled={isPending}
            onClick={() => void handleLogin(ROLE_PRESETS.admin)}
          >
            Admin
          </Button>
        </div>

        <div className="mt-6 border-t border-dashed border-border pt-4">
          <Button
            data-testid="test-logout"
            variant="ghost"
            className="w-full"
            disabled={isPending}
            onClick={() => void handleLogout()}
          >
            Sign out
          </Button>
        </div>

        {status ? (
          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            {status}
          </div>
        ) : null}
      </div>
    </div>
  );
}
