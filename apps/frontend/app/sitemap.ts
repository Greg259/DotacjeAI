import type { MetadataRoute } from "next";

import { getPrograms } from "@/lib/api";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = process.env.NEXT_PUBLIC_SITE_URL ?? "https://dotacjeai.eu";
  const staticPaths = [
    "",
    "/dotacje",
    "/region/mazowieckie",
    "/powiat/pruszkowski",
    "/gmina/nadarzyn",
    "/kategoria/fotowoltaika",
    "/kategoria/magazyny-energii",
    "/kategoria/pompy-ciepla",
  ];
  let programPaths: string[] = [];
  try {
    const programs = await getPrograms({ limit: "100" });
    programPaths = programs.items.map((program) => `/dotacje/${program.slug}`);
  } catch {
    // Statyczne adresy pozostają dostępne, gdy API jest chwilowo niedostępne.
  }
  return [...staticPaths, ...programPaths].map((path) => ({
    url: `${site}${path}`,
    changeFrequency: "daily",
    priority: path === "" ? 1 : path.startsWith("/dotacje/") ? 0.9 : 0.8,
  }));
}
