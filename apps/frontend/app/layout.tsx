import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import { ThemeToggle } from "@/components/theme-toggle";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://dotacjeai.eu"),
  title: { default: "DotacjeAI", template: "%s | DotacjeAI" },
  description: "Zweryfikowane dotacje dla osób prywatnych i przedsiębiorstw.",
};

const themeScript = `(() => { try { const saved = localStorage.getItem('dotacjeai-theme'); const system = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; const theme = saved === 'dark' || saved === 'light' ? saved : system; document.documentElement.dataset.theme = theme; document.documentElement.style.colorScheme = theme; } catch (_) {} })();`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pl" suppressHydrationWarning>
      <head><script dangerouslySetInnerHTML={{ __html: themeScript }} /></head>
      <body>
        <a className="skip-link" href="#main-content">Przejdź do treści</a>
        <header className="site-header">
          <div className="shell header-inner">
            <Link className="brand" href="/">Dotacje<span>AI</span></Link>
            <div className="header-actions">
              <nav aria-label="Główna nawigacja">
                <Link href="/dotacje">Programy</Link>
                <Link href="/region/mazowieckie">Regiony</Link>
                <Link href="/konto">Moje konto</Link>
              </nav>
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main id="main-content">{children}</main>
        <footer><div className="shell footer-inner"><span>DotacjeAI · Dane z oficjalnych źródeł · Zawsze sprawdź regulamin programu.</span><span><Link href="/regulamin">Regulamin</Link> · <Link href="/prywatnosc">Prywatność</Link></span></div></footer>
      </body>
    </html>
  );
}
