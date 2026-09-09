import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Dalizebo Platform Beta 0.1",
  description: "Dalizebo Imperial Platform Beta",
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