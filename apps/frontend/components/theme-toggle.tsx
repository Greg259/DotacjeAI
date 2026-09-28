"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "dark" : "light");
  }, []);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    document.documentElement.style.colorScheme = next;
    window.localStorage.setItem("dotacjeai-theme", next);
    setTheme(next);
  }

  return (
    <button
      aria-label={theme === "dark" ? "Włącz jasny motyw" : "Włącz ciemny motyw"}
      className="theme-toggle"
      onClick={toggleTheme}
      title={theme === "dark" ? "Jasny motyw" : "Ciemny motyw"}
      type="button"
    >
      <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
      <span className="theme-label">{theme === "dark" ? "Jasny" : "Ciemny"}</span>
    </button>
  );
}
