import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://dotacjeai.eu"),
  title: { default: "DotacjeAI", template: "%s | DotacjeAI" },
  description: "Zweryfikowane dotacje dla domów i mieszkań na Mazowszu.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pl">
      <body>
        <header className="site-header">
          <div className="shell header-inner">
            <Link className="brand" href="/">Dotacje<span>AI</span></Link>
            <nav aria-label="Główna nawigacja">
              <Link href="/dotacje">Wszystkie dotacje</Link>
              <Link href="/region/mazowieckie">Mazowieckie</Link>
              <Link href="/gmina/nadarzyn">Nadarzyn</Link>
            </nav>
          </div>
        </header>
        <main>{children}</main>
        <footer><div className="shell">DotacjeAI · Dane wyłącznie z oficjalnych źródeł · Zawsze sprawdź regulamin programu.</div></footer>
      </body>
    </html>
  );
}
