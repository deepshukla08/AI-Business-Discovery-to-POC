"use client";

import { useMemo, useState } from "react";
import Cites from "@/components/cites";
import type { Chunk, FindingType, Insight, RunResult } from "@/lib/types";

// The one place colour earns its keep: you scan 50 findings and want the pains to jump
// out without reading. Tinted backgrounds so the same classes work light and dark.
const TYPE_STYLE: Record<FindingType, string> = {
  pain: "bg-rose-500/12 text-rose-700 dark:text-rose-300",
  requirement: "bg-blue-500/12 text-blue-700 dark:text-blue-300",
  constraint: "bg-amber-500/12 text-amber-700 dark:text-amber-300",
  question: "bg-teal-500/12 text-teal-700 dark:text-teal-300",
  fact: "bg-zinc-500/12 text-zinc-600 dark:text-zinc-400",
};

const ORDER: FindingType[] = ["pain", "requirement", "constraint", "question", "fact"];

export default function FindingsView({
  result,
  projectId,
  chunks,
}: {
  result: RunResult;
  projectId: string;
  chunks: Map<string, Chunk>;
}) {
  const [types, setTypes] = useState<Set<FindingType>>(new Set());
  const [query, setQuery] = useState("");

  // insights are findings after merging; fall back to raw findings for older runs
  const items: Insight[] = useMemo(
    () =>
      result.insights?.length
        ? result.insights
        : result.findings.map((f) => ({ ...f, sources: f.source_id ? [f.source_id] : [] })),
    [result],
  );

  const counts = useMemo(() => {
    const tally = {} as Record<FindingType, number>;
    for (const item of items) tally[item.type] = (tally[item.type] ?? 0) + 1;
    return tally;
  }, [items]);

  const shown = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return items.filter(
      (item) =>
        (types.size === 0 || types.has(item.type)) &&
        (!needle || item.text.toLowerCase().includes(needle)),
    );
  }, [items, types, query]);

  function toggle(type: FindingType) {
    setTypes((current) => {
      const next = new Set(current);
      if (!next.delete(type)) next.add(type);
      return next;
    });
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3 rounded-2xl border border-line bg-surface p-4">
        <div className="flex flex-wrap items-center gap-1.5">
          {ORDER.filter((type) => counts[type]).map((type) => {
            const active = types.has(type);
            return (
              <button
                key={type}
                onClick={() => toggle(type)}
                className={`rounded-full px-2.5 py-1 text-[11px] transition ${TYPE_STYLE[type]} ${
                  active
                    ? "ring-2 ring-current ring-offset-2 ring-offset-surface"
                    : types.size
                      ? "opacity-40"
                      : ""
                }`}
              >
                {type} <span className="tnum opacity-60">{counts[type]}</span>
              </button>
            );
          })}
          {types.size > 0 && (
            <button
              onClick={() => setTypes(new Set())}
              className="px-1.5 text-[11px] text-muted hover:text-accent"
            >
              clear
            </button>
          )}
        </div>

        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search the evidence…"
          className="w-full rounded-lg border border-line bg-transparent px-3 py-1.5 text-sm outline-none focus:border-accent"
        />

        <p className="tnum text-[11px] text-muted">
          {shown.length} of {items.length} shown
          {result.insights?.length
            ? ` · merged down from ${result.findings.length} raw findings across ${result.chunks.length} chunks`
            : ""}
        </p>
      </div>

      {shown.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line px-6 py-12 text-center text-sm text-muted">
          Nothing matches.
        </p>
      ) : (
        <ul className="space-y-2">
          {shown.map((item, i) => (
            <li
              key={i}
              className="rounded-xl border border-line bg-surface px-4 py-3 transition hover:border-muted"
            >
              <div className="flex items-start gap-2.5">
                <span
                  className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] ${TYPE_STYLE[item.type]}`}
                >
                  {item.type}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm leading-relaxed">{item.text}</p>
                  <Cites cites={item.cites} chunks={chunks} projectId={projectId} />
                </div>
                {item.sources.length > 1 && (
                  <span
                    title={item.sources.join("\n")}
                    className="mt-0.5 shrink-0 rounded bg-accent-soft px-1.5 py-0.5 text-[10px] text-accent"
                  >
                    {item.sources.length}×
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
