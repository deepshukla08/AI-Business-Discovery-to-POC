"use client";

import Cites from "@/components/cites";
import type { Brief, Chunk, Cited, Gap, GapKind } from "@/lib/types";

const GAP_STYLE: Record<GapKind, [string, string]> = {
  contradiction: ["bg-rose-500/12 text-rose-700 dark:text-rose-300", "sources disagree"],
  unanswered: ["bg-amber-500/12 text-amber-700 dark:text-amber-300", "asked, never answered"],
  never_discussed: ["bg-teal-500/12 text-teal-700 dark:text-teal-300", "never came up"],
};

export default function BriefView({
  brief,
  gaps,
  chunks,
  projectId,
}: {
  brief: Brief;
  gaps: Gap[];
  chunks: Map<string, Chunk>;
  projectId: string;
}) {
  return (
    <div className="space-y-4">
      <section className="goal-card rounded-2xl border border-accent/25 p-6">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-accent">
          The goal
        </h2>
        <p className="mt-2.5 text-[15px] leading-[1.65]">{brief.goal.text}</p>
        <Cites cites={brief.goal.cites} chunks={chunks} projectId={projectId} />
      </section>

      {brief.current_process.length > 0 && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
            How it works today
          </h2>
          <ol className="mt-3 space-y-3">
            {brief.current_process.map((step, i) => (
              <li key={i} className="flex gap-3">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-raised text-[11px] text-muted">
                  {i + 1}
                </span>
                <div className="min-w-0">
                  <p className="text-sm">{step.text}</p>
                  <Cites cites={step.cites} chunks={chunks} projectId={projectId} />
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      <CitedList title="What hurts" items={brief.pain_points} chunks={chunks} projectId={projectId} ranked />
      <CitedList title="Requirements" items={brief.requirements} chunks={chunks} projectId={projectId} />
      <CitedList title="Constraints" items={brief.constraints} chunks={chunks} projectId={projectId} />
      <CitedList
        title="What they asked for"
        note="Their words — kept separate from what the evidence says they need."
        items={brief.stated_wants}
        chunks={chunks}
        projectId={projectId}
      />

      {gaps.length > 0 && (
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
            What we still need to ask
          </h2>
          <p className="mt-1 text-xs text-muted">
            {gaps.length} open question{gaps.length === 1 ? "" : "s"}. Quoting the work before
            these are answered means guessing.
          </p>
          <ul className="mt-4 space-y-4">
            {gaps.map((gap, i) => {
              const [style, label] = GAP_STYLE[gap.kind] ?? GAP_STYLE.never_discussed;
              return (
                <li key={i}>
                  <div className="flex flex-wrap items-baseline gap-2">
                    <span className={`rounded px-2 py-0.5 text-[11px] ${style}`}>{label}</span>
                    <p className="text-sm font-medium">{gap.question}</p>
                  </div>
                  <p className="mt-1 text-xs text-muted">{gap.why_it_matters}</p>
                  <Cites cites={gap.cites} chunks={chunks} projectId={projectId} />
                </li>
              );
            })}
          </ul>
        </section>
      )}
    </div>
  );
}

function CitedList({
  title,
  note,
  items,
  chunks,
  projectId,
  ranked = false,
}: {
  title: string;
  note?: string;
  items: Cited[];
  chunks: Map<string, Chunk>;
  projectId: string;
  ranked?: boolean;
}) {
  if (!items.length) return null;

  return (
    <section className="rounded-2xl border border-line bg-surface p-6">
      <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">{title}</h2>
      {note && <p className="mt-1 text-xs text-muted">{note}</p>}
      <ul className="mt-3 space-y-3">
        {items.map((item, i) => (
          <li key={i} className="flex gap-3">
            {ranked && (
              <span className="mt-0.5 w-4 shrink-0 text-right text-[11px] text-muted">
                {i + 1}
              </span>
            )}
            <div className="min-w-0">
              <p className="text-sm">{item.text}</p>
              <Cites cites={item.cites} chunks={chunks} projectId={projectId} />
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
