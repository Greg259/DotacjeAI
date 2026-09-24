import type { ProgramDetail, ProgramListResponse } from "./types";

const apiBase = process.env.API_INTERNAL_URL ?? "http://localhost:8000/api";

type FilterValue = string | string[] | undefined;

export async function getPrograms(
  filters: Record<string, FilterValue> = {},
): Promise<ProgramListResponse> {
  const query = new URLSearchParams();
  for (const [key, rawValue] of Object.entries(filters)) {
    const value = Array.isArray(rawValue) ? rawValue[0] : rawValue;
    if (value) query.set(key, value);
  }
  const response = await fetch(`${apiBase}/programs?${query}`, { cache: "no-store" });
  if (!response.ok) throw new Error("Nie udało się pobrać listy dotacji.");
  return response.json();
}

export async function getProgram(slug: string): Promise<ProgramDetail | null> {
  const response = await fetch(`${apiBase}/programs/${encodeURIComponent(slug)}`, {
    cache: "no-store",
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Nie udało się pobrać programu.");
  return response.json();
}
