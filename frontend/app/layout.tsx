/* eslint-disable react-refresh/only-export-components */
import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "AI Credit Committee", description: "Credit underwriting demo" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
