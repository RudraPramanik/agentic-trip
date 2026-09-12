import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "agentic-trip",
  description: "Guest chat shell for the conversational trip OS",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
