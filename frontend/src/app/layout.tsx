import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import StatusPill from "@/components/status-pill";
import ThemeToggle, { THEME_SCRIPT } from "@/components/theme-toggle";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Business Discovery to POC",
  description: "Turn scattered client inputs into a sourced business brief and a POC.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      data-theme="dark"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} />
      </head>
      <body className="font-sans flex min-h-full flex-col">
        <header className="sticky top-0 z-20 border-b border-line bg-surface/85 backdrop-blur">
          <div className="flex items-center justify-between gap-4 px-5 py-3">
            <Link href="/" className="min-w-0">
              <div className="truncate text-sm font-semibold tracking-tight">
                AI Business Discovery to POC
              </div>
              <div className="truncate text-[11px] text-muted">
                scattered inputs → business brief → proposed solution
              </div>
            </Link>
            <div className="flex shrink-0 items-center gap-2">
              <StatusPill />
              <ThemeToggle />
            </div>
          </div>
        </header>

        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
