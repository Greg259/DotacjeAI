import type { Metadata } from "next";

import { ProfileForm } from "@/components/profile-form";

export const metadata: Metadata = { title: "Nowy profil nieruchomości" };

export default function NewProfilePage() {
  return <section className="shell narrow-section"><p className="eyebrow">Profil nieruchomości</p><h1>Dodaj profil</h1><p className="lead compact">Zapisz dane potrzebne do późniejszego dopasowania dotacji.</p><ProfileForm /></section>;
}
