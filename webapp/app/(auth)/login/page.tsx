'use client';

import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { signIn } from "next-auth/react";

const DEFAULT_CALLBACK = "/profile";

function LoginContent() {
  const searchParams = useSearchParams();
  const callbackUrl = useMemo(() => {
    const value = searchParams?.get("callbackUrl");
    return value && value.trim().length > 0 ? value : DEFAULT_CALLBACK;
  }, [searchParams]);

  return (
    <main>
      <h1>Sign in</h1>
      <p>Authenticate with the corporate Keycloak realm to access the AWA console.</p>
      <button type="button" onClick={() => signIn("keycloak", { callbackUrl })}>
        Continue with Keycloak
      </button>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main>Preparing login…</main>}>
      <LoginContent />
    </Suspense>
  );
}
