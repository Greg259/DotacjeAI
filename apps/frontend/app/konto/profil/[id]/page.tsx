import type { Metadata } from "next";

import { ProfileForm } from "@/components/profile-form";

export const metadata: Metadata = { title: "Edycja profilu nieruchomości" };

export default async function EditProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <section className="shell narrow-section"><p className="eyebrow">Profil nieruchomości</p><h1>Edytuj profil</h1><ProfileForm profileId={id} /></section>;
}
