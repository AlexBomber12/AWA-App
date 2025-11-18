import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { TestLoginClient } from "./TestLoginClient";

export const metadata: Metadata = {
  title: "Test login",
};

export default function TestLoginPage() {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }

  return <TestLoginClient />;
}
