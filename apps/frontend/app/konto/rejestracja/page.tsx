import type { Metadata } from "next";

import { AuthForm } from "@/components/auth-form";

export const metadata: Metadata = { title: "Rejestracja" };

export default function RegistrationPage() {
  return <section className="shell narrow-section"><p className="eyebrow">Konto testowe</p><h1>Utwórz konto</h1><p className="lead compact">Na tym etapie konto działa bez adresu i potwierdzenia e-mail. E-mail zintegrujemy w kolejnym sprincie.</p><AuthForm mode="register" /></section>;
}
