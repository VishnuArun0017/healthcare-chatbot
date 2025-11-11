import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Health Assistant - AI-Powered Health Information",
  description: "Get reliable health information and guidance. Not a substitute for professional medical advice.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}