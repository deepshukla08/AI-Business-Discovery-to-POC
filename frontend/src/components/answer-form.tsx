"use client";

import { useState } from "react";
import Cites from "@/components/cites";
import type { Chunk, Gap, GapKind } from "@/lib/types";

const GAP_STYLE: Record<GapKind, [string, string]> = {
  contradiction: ["bg-rose-500/12 text-rose-700 dark:text-rose-300", "sources disagree"],
  unanswered: ["bg-amber-500/12 text-amber-700 dark:text-amber-300", "asked, never answered"],
  never_discussed: ["bg-teal-500/12 text-teal-700 dark:text-teal-300", "never came up"],
};

export default function AnswerForm({
  gaps,
  chunks,
  projectId,
  onSubmit,
}: {
  gaps: Gap[];
  chunks: Map<string, Chunk>;
  projectId: string;
  onSubmit: (answers: { question: string; answer: string }[]) => void;
}) {
  const [replies, setReplies] = useState<Record<number, string>>({});
  const filled = Object.values(replies).filter((r) => r.trim()).length;

  function send() {
    onSubmit(
      gaps
        .map((gap, i) => ({ question: gap.question, answer: (replies[i] ?? "").trim() }))
        .filter((r) => r.answer),
    );
  }

  return (
    <div className="space-y-4">
      <section className="goal-card rounded-2xl border border-line p-6">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
          Paused — {gaps.length} question{gaps.length === 1 ? "" : "s"} for the client
        </h2>
        <p className="mt-2.5 text-sm leading-relaxed">
          The brief is written. Nothing below it has been designed yet, because a proposal built
          on guesses is how projects get rebuilt. Answer what you know and continue.
        </p>
      </section>

      <ol className="space-y-3">
        {gaps.map((gap, i) => {
          const [style, label] = GAP_STYLE[gap.kind] ?? GAP_STYLE.never_discussed;
          return (
            <li key={i} className="rounded-2xl border border-line bg-surface p-5">
              <div className="flex flex-wrap items-baseline gap-2">
                <span className={`rounded px-2 py-0.5 text-[11px] ${style}`}>{label}</span>
                <p className="text-sm font-medium">{gap.question}</p>
              </div>
              <p className="mt-1 text-xs text-muted">{gap.why_it_matters}</p>
              <Cites cites={gap.cites} chunks={chunks} projectId={projectId} />
              <textarea
                value={replies[i] ?? ""}
                onChange={(e) => setReplies({ ...replies, [i]: e.target.value })}
                rows={2}
                placeholder="What the client said — or leave blank if you still don't know"
                className="slim mt-3 w-full rounded-lg border border-line bg-transparent px-3 py-2 text-sm outline-none focus:border-ink"
              />
            </li>
          );
        })}
      </ol>

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={send}
          className="rounded-xl bg-ink px-4 py-2.5 text-sm font-medium text-bg transition hover:opacity-90"
        >
          {filled
            ? `Continue with ${filled} answer${filled === 1 ? "" : "s"}`
            : "Continue without answering"}
        </button>
        <p className="text-xs text-muted">
          {filled
            ? "Anything left blank stays on the open-questions list."
            : "Deciding to proceed unanswered is a choice — it stays visible in the brief."}
        </p>
      </div>
    </div>
  );
}
