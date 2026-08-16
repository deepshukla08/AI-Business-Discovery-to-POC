"use client";

import { useEffect, useState } from "react";

type Theme = "dark" | "light";

/** Runs before paint so the page never flashes the wrong theme. Dark is the default. */
export const THEME_SCRIPT = `(function(){try{var t=localStorage.getItem('theme')||'dark';document.documentElement.dataset.theme=t}catch(e){document.documentElement.dataset.theme='dark'}})()`;

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    setTheme((document.documentElement.dataset.theme as Theme) ?? "dark");
  }, []);

  function flip() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("theme", next);
    setTheme(next);
  }

  return (
    <button
      onClick={flip}
      title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      aria-label="Toggle theme"
      className="rounded-lg border border-line px-2 py-1 text-xs text-muted transition hover:border-accent hover:text-accent"
    >
      {theme === "dark" ? "☾" : "☀"}
    </button>
  );
}
