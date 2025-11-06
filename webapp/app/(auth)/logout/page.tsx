'use client';

import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { signOut } from "next-auth/react";

const DEFAULT_REDIRECT = "/";

function LogoutContent() {
  const searchParams = useSearchParams();
  const redirectTo = useMemo(() => {
    const value = searchParams?.get("callbackUrl");
    return value && value.trim().length > 0 ? value : DEFAULT_REDIRECT;
  }, [searchParams]);

  return (
    <main>
      <h1>Sign out</h1>
      <p>This will clear your session in the browser and redirect you back to the chosen page.</p>
      <button type="button" onClick={() => signOut({ callbackUrl: redirectTo })}>
        Sign out
      </button>
    </main>
  );
}

export default function LogoutPage() {
  return (
    <Suspense fallback={<main>Preparing logout…</main>}>
      <LogoutContent />
    </Suspense>
  );
}
