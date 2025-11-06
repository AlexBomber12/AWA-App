import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AWA Console",
  description: "Authenticated web console for AWA operators.",
};

type RootLayoutProps = {
  children: React.ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
