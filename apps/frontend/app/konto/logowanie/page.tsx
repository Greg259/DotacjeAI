import type { Metadata } from "next";

import { AuthForm } from "@/components/auth-form";

export const metadata: Metadata = { title: "Logowanie" };

export default function LoginPage() {
  return <section className="shell narrow-section"><p className="eyebrow">Konto</p><h1>Zaloguj się</h1><p className="lead compact">Użyj nazwy użytkownika i hasła. Adres e-mail nie jest jeszcze wymagany.</p><AuthForm mode="login" /></section>;
}
