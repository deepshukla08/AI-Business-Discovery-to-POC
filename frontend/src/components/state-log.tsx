"use client";

/* ─────────────────────────────────────────────────────────────────────────────
 * TEMPORARY — debug only. Delete this file and its two lines in project-view.tsx.
 *
 * Renders the live front-end state on every render, without needing a run:
 * a panel in the corner, and the full object in the browser console.
 * ───────────────────────────────────────────────────────────────────────────── */

import { useState } from "react";

function summarise(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (Array.isArray(value)) return `${value.length} item${value.length === 1 ? "" : "s"}`;
  if (typeof value === "object") return `{${Object.keys(value as object).length} keys}`;
  if (typeof value === "string") return value.length > 34 ? `${value.slice(0, 34)}…` : value || '""';
  return String(value);
}

export default function StateLog({ state }: { state: Record<string, unknown> }) {
  const [open, setOpen] = useState(true);

  // fires on every render, including ones with no run in progress.
  // React StrictMode double-renders in dev, so expect pairs.
  console.log("%c[state]", "color:#6ea8fe;font-weight:600", state);

  return (
    <div className="fixed bottom-3 right-3 z-50 max-w-[320px] rounded-xl border border-line bg-surface/95 font-mono text-[10px] shadow-lg backdrop-blur">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left"
      >
        <span className="text-muted">state · debug</span>
        <span className="text-muted">{open ? "▾" : "▸"}</span>
      </button>

      {open && (
        <div className="slim max-h-[45vh] overflow-y-auto border-t border-line px-3 py-2">
          <table className="w-full">
            <tbody>
              {Object.entries(state).map(([key, value]) => (
                <tr key={key} className="align-top">
                  <td className="whitespace-nowrap pr-3 text-muted">{key}</td>
                  <td className="break-all">{summarise(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 border-t border-line pt-2 text-[9px] text-muted">
            full objects logged to the browser console
          </p>
        </div>
      )}
    </div>
  );
}
