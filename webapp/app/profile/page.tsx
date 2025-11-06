import Link from "next/link";
import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";

import { authOptions } from "@/lib/auth";

const formatRoles = (roles: string[]) => (roles.length ? roles.join(", ") : "No roles assigned");

export default async function ProfilePage() {
  const session = await getServerSession(authOptions);

  if (!session) {
    const callbackUrl = encodeURIComponent("/profile");
    redirect(`/(auth)/login?callbackUrl=${callbackUrl}`);
  }

  const user = session.user ?? {};
  const roles = Array.isArray(user.roles) ? user.roles : [];

  return (
    <main>
      <h1>Profile</h1>
      <p>You are signed in via Keycloak.</p>
      <section>
        <p>
          <strong>Name:</strong> {user.name ?? "—"}
        </p>
        <p>
          <strong>Email:</strong> {user.email ?? "—"}
        </p>
        <p>
          <strong>Roles:</strong> {formatRoles(roles)}
        </p>
      </section>
      <p>
        <Link href="/(auth)/logout">Sign out</Link>
      </p>
    </main>
  );
}
