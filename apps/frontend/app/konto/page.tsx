import type { Metadata } from "next";

import { AccountDashboard } from "@/components/account-dashboard";

export const metadata: Metadata = { title: "Moje konto" };

export default function AccountPage() {
  return <section className="shell section"><AccountDashboard /></section>;
}
