import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { AppShell } from "@/components/layout";
import { getServerAuthSession } from "@/lib/auth";

import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: {
    template: "%s | AWA Operator Console",
    default: "AWA Operator Console",
  },
  description: "Amazon Wholesale Analytics web console bootstrap.",
};

type RootLayoutProps = {
  children: React.ReactNode;
};

export default async function RootLayout({ children }: RootLayoutProps) {
  const session = await getServerAuthSession();

  return (
    <html lang="en">
      <body className={inter.className}>
        <AppShell initialSession={session}>{children}</AppShell>
      </body>
    </html>
  );
}
