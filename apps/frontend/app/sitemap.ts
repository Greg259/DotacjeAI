import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const site = process.env.NEXT_PUBLIC_SITE_URL ?? "https://dotacjeai.eu";
  return ["", "/dotacje", "/region/mazowieckie", "/gmina/nadarzyn"].map((path) => ({ url: `${site}${path}`, changeFrequency: "daily", priority: path === "" ? 1 : 0.8 }));
}
