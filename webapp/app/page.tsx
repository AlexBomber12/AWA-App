import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>AWA Web Console</h1>
      <p>
        Sign in with your AWA Keycloak account to manage repricing, restock planning, and other
        operational workflows.
      </p>
      <ul>
        <li>
          <Link href="/(auth)/login">Login</Link>
        </li>
        <li>
          <Link href="/profile">View profile</Link>
        </li>
        <li>
          <Link href="/(auth)/logout">Logout</Link>
        </li>
      </ul>
    </main>
  );
}
