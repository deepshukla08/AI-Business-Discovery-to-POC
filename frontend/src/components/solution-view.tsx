"use client";

import Cites from "@/components/cites";
import type { ChangeKind, Chunk, Outline, Redesign } from "@/lib/types";

// what happened to each step, colour-coded so the shape of the change reads at a glance
const CHANGE_STYLE: Record<ChangeKind, string> = {
  removed: "bg-rose-500/12 text-rose-700 dark:text-rose-300",
  automated: "bg-blue-500/12 text-blue-700 dark:text-blue-300",
  simplified: "bg-teal-500/12 text-teal-700 dark:text-teal-300",
  new: "bg-amber-500/12 text-amber-700 dark:text-amber-300",
  unchanged: "bg-zinc-500/12 text-zinc-600 dark:text-zinc-400",
};

const PRIORITY_STYLE: Record<string, string> = {
  must: "bg-ink text-bg",
  should: "border border-ink/60 text-ink",
  later: "border border-dashed border-muted text-muted",
};

export default function SolutionView({
  redesign,
  outline,
  chunks,
  projectId,
}: {
  redesign: Redesign | null | undefined;
  outline: Outline | null | undefined;
  chunks: Map<string, Chunk>;
  projectId: string;
}) {
  if (!redesign) {
    return (
      <p className="rounded-2xl border border-dashed border-line px-6 py-12 text-center text-sm text-muted">
        This run predates the proposal stage. Run again to generate one.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <section className="goal-card rounded-2xl border border-line p-6">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
          The proposal
        </h2>
        <p className="mt-2.5 text-[15px] leading-[1.65]">{redesign.summary}</p>
      </section>

      <section className="rounded-2xl border border-line bg-surface p-6">
        <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
          How it would work instead
        </h2>
        <ol className="mt-4 space-y-4">
          {redesign.to_be.map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="tnum mt-0.5 w-4 shrink-0 text-right text-[11px] text-muted">
                {i + 1}
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-baseline gap-2">
                  <p className="text-sm">{step.step}</p>
                  <span
                    className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] ${CHANGE_STYLE[step.change]}`}
                  >
                    {step.change}
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-muted">{step.why}</p>
                <Cites cites={step.cites} chunks={chunks} projectId={projectId} />
              </div>
            </li>
          ))}
        </ol>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <section className="rounded-2xl border border-line bg-surface p-6">
          <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
            What this fixes
          </h2>
          <ul className="mt-3 space-y-3">
            {redesign.wins.map((win, i) => (
              <li key={i}>
                <p className="text-sm">{win.text}</p>
                <Cites cites={win.cites} chunks={chunks} projectId={projectId} />
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-2xl border border-dashed border-line bg-surface p-6">
          <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
            What it does not fix
          </h2>
          {redesign.not_solved.length === 0 ? (
            <p className="mt-3 text-xs text-muted">
              Nothing listed — treat that with suspicion rather than relief.
            </p>
          ) : (
            <ul className="mt-3 space-y-3">
              {redesign.not_solved.map((item, i) => (
                <li key={i}>
                  <p className="text-sm">{item.text}</p>
                  <Cites cites={item.cites} chunks={chunks} projectId={projectId} />
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {outline && (
        <>
          <section className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
              The application
            </h2>
            <p className="mt-2 text-lg font-semibold tracking-tight">{outline.app_name}</p>
            <p className="text-sm text-muted">{outline.one_liner}</p>

            <div className="mt-5 flex flex-wrap gap-2">
              {outline.roles.map((role) => (
                <div
                  key={role.name}
                  className="rounded-xl border border-line bg-raised px-3 py-2"
                >
                  <div className="text-xs font-medium">{role.name}</div>
                  <div className="text-[11px] text-muted">{role.does}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
              Features
            </h2>
            <ul className="mt-3 space-y-2.5">
              {outline.features.map((feature, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span
                    className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] ${
                      PRIORITY_STYLE[feature.priority] ?? PRIORITY_STYLE.later
                    }`}
                  >
                    {feature.priority}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm">{feature.name}</p>
                    <p className="text-xs text-muted">solves: {feature.solves}</p>
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
              Screens
            </h2>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {outline.screens.map((screen, i) => (
                <div key={i} className="rounded-xl border border-line p-4">
                  <div className="flex items-baseline justify-between gap-2">
                    <p className="text-sm font-medium">{screen.name}</p>
                    <span className="shrink-0 text-[10px] text-muted">{screen.role}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted">{screen.purpose}</p>
                  <ul className="mt-2.5 space-y-1">
                    {screen.elements.map((element, j) => (
                      <li key={j} className="text-[11px] text-muted">
                        · {element}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
              One job, end to end
            </h2>
            <ol className="mt-3 space-y-2">
              {outline.flow.map((step, i) => (
                <li key={i} className="flex gap-3 text-sm">
                  <span className="tnum w-4 shrink-0 text-right text-[11px] text-muted">
                    {i + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </section>
        </>
      )}
    </div>
  );
}
