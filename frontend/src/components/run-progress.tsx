"use client";

import { useEffect, useState } from "react";

/** What each stage is called in language a consultant would use, not node names. */
export const STEPS: { doing: string; done: string }[] = [
  { doing: "Reading your files", done: "Read your files" },
  { doing: "Understanding each source", done: "Understood each source" },
  { doing: "Matching up what repeats", done: "Matched up what repeats" },
  { doing: "Writing the brief", done: "Wrote the brief" },
  { doing: "Working out what nobody told you", done: "Listed the open questions" },
  { doing: "Designing a simpler way of working", done: "Proposed a better process" },
  { doing: "Sketching the application", done: "Sketched the application" },
  { doing: "Building something you can click", done: "Built a clickable demo" },
];

export default function RunProgress({ at, detail }: { at: number; detail: string }) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const tick = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(tick);
  }, []);

  const pct = Math.round((at / STEPS.length) * 100);

  return (
    <div className="mx-auto max-w-md py-16">
      <div className="rounded-2xl border border-line bg-surface p-7">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-medium">
            {STEPS[at]?.doing ?? "Finishing up"}
            <span className="ml-0.5 inline-block animate-pulse">…</span>
          </h2>
          <span className="tnum text-[11px] text-muted">{seconds}s</span>
        </div>

        <p className="mt-1 min-h-[1.25rem] text-xs text-muted">{detail}</p>

        <div className="mt-4 h-1 overflow-hidden rounded-full bg-raised">
          <div
            className="h-full rounded-full bg-ink transition-[width] duration-700 ease-out"
            style={{ width: `${Math.max(pct, 4)}%` }}
          />
        </div>

        <ol className="mt-5 space-y-2.5">
          {STEPS.map((step, i) => {
            const done = i < at;
            const active = i === at;
            return (
              <li key={i} className="flex items-center gap-2.5">
                <span
                  className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[9px] ${
                    done
                      ? "bg-ink text-bg"
                      : active
                        ? "animate-pulse bg-ink/25"
                        : "border border-line"
                  }`}
                >
                  {done ? "✓" : ""}
                </span>
                <span
                  className={`text-xs ${
                    done ? "text-muted line-through decoration-line" : active ? "" : "text-muted/50"
                  }`}
                >
                  {done ? step.done : step.doing}
                </span>
              </li>
            );
          })}
        </ol>

        <p className="mt-5 text-[11px] text-muted/70">
          Each source is read separately, so this takes about as long as the biggest one.
        </p>
      </div>
    </div>
  );
}
