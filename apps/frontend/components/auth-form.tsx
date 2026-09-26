"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { errorMessage } from "@/lib/account";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const payload: Record<string, unknown> = {
      username: form.get("username"),
      password: form.get("password"),
    };
    if (mode === "register") {
      payload.accept_terms = form.get("accept_terms") === "on";
      payload.accept_privacy = form.get("accept_privacy") === "on";
    }
    const response = await fetch(`/api/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      setError(await errorMessage(response));
      setBusy(false);
      return;
    }
    router.push("/konto");
    router.refresh();
  }

  const registration = mode === "register";
  return (
    <form className="account-form" onSubmit={submit}>
      <label>
        Nazwa użytkownika
        <input name="username" minLength={3} maxLength={40} autoComplete="username" required />
      </label>
      <label>
        Hasło
        <input
          name="password"
          type="password"
          minLength={12}
          maxLength={128}
          autoComplete={registration ? "new-password" : "current-password"}
          required
        />
        {registration && <small>Minimum 12 znaków. Nie używaj hasła z innego serwisu.</small>}
      </label>
      {registration && (
        <>
          <label className="check-row">
            <input name="accept_terms" type="checkbox" required />
            Akceptuję <Link href="/regulamin">regulamin korzystania z wersji testowej</Link>.
          </label>
          <label className="check-row">
            <input name="accept_privacy" type="checkbox" required />
            Zapoznałem się z <Link href="/prywatnosc">informacją o prywatności</Link>.
          </label>
        </>
      )}
      {error && <p className="form-error" role="alert">{error}</p>}
      <button className="button" disabled={busy} type="submit">
        {busy ? "Zapisywanie…" : registration ? "Utwórz konto" : "Zaloguj się"}
      </button>
      <p>
        {registration ? "Masz już konto? " : "Nie masz konta? "}
        <Link className="text-link" href={registration ? "/konto/logowanie" : "/konto/rejestracja"}>
          {registration ? "Zaloguj się" : "Załóż konto"}
        </Link>
      </p>
    </form>
  );
}
