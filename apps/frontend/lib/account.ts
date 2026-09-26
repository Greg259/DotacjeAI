export function csrfToken(): string {
  const item = document.cookie
    .split("; ")
    .find((value) => value.startsWith("dotacjeai_csrf="));
  return item ? decodeURIComponent(item.split("=").slice(1).join("=")) : "";
}

export async function apiRequest(path: string, init: RequestInit = {}) {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers.set("X-CSRF-Token", csrfToken());
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(path, { ...init, headers, credentials: "same-origin" });
}

export async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail[0]?.msg ?? "Nieprawidłowe dane.";
  } catch {}
  return "Operacja nie powiodła się. Spróbuj ponownie.";
}
