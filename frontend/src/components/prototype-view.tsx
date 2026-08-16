"use client";

import { API } from "@/lib/api";
import type { Outline } from "@/lib/types";

export default function PrototypeView({
  projectId,
  ok,
  faults,
  outline,
}: {
  projectId: string;
  ok: boolean;
  faults: string[];
  outline: Outline | null | undefined;
}) {
  const url = `${API}/api/projects/${projectId}/prototype`;

  if (!ok) {
    return (
      <div className="space-y-4">
        <section className="rounded-2xl border border-dashed border-line bg-surface p-6">
          <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
            No usable prototype
          </h2>
          {faults.length ? (
            <>
              <p className="mt-2 text-sm">
                The model returned something, but it failed its checks — so it is not being
                shown rather than rendering a broken page and calling it a demo.
              </p>
              <ul className="mt-3 space-y-1">
                {faults.map((fault, i) => (
                  <li key={i} className="text-xs text-muted">
                    · {fault}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-muted">
                Run again — generation is the least deterministic step in the pipeline.
              </p>
            </>
          ) : (
            <p className="mt-2 text-sm text-muted">
              This run predates the prototype stage. Run again to generate one.
            </p>
          )}
        </section>

        {outline && (
          <section className="rounded-2xl border border-line bg-surface p-6">
            <h2 className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted">
              What it would have been
            </h2>
            <p className="mt-2 text-sm font-medium">{outline.app_name}</p>
            <ul className="mt-2 space-y-1">
              {outline.screens.map((screen, i) => (
                <li key={i} className="text-xs text-muted">
                  · {screen.name} — {screen.purpose}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col gap-2">
      <div className="flex shrink-0 items-center gap-2">
        <p className="min-w-0 flex-1 truncate text-[11px] text-muted">
          Throwaway by design — fake data, no backend, refreshing resets it.
        </p>
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 rounded-lg border border-line px-3 py-1.5 text-xs text-muted transition hover:border-ink hover:text-ink"
        >
          Open in new tab
        </a>
        <a
          href={url}
          download="prototype.html"
          className="shrink-0 rounded-lg border border-line px-3 py-1.5 text-xs text-muted transition hover:border-ink hover:text-ink"
        >
          Download
        </a>
      </div>

      <div className="min-h-0 flex-1 overflow-hidden rounded-xl border border-line bg-white">
        <iframe
          src={url}
          title="Generated prototype"
          // model-written code: scripts may run, but with no access to this page or our API
          sandbox="allow-scripts"
          className="block h-full w-full border-0"
        />
      </div>
    </div>
  );
}
