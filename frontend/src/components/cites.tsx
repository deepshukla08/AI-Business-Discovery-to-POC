"use client";

import { useState } from "react";
import { API } from "@/lib/api";
import type { Chunk } from "@/lib/types";

/** Citation chips. Click one to see the exact source behind a claim — the line someone
 *  said, the clause in the document, or the screenshot itself. */
export default function Cites({
  cites,
  chunks,
  projectId,
}: {
  cites: string[];
  chunks: Map<string, Chunk>;
  projectId: string;
}) {
  const [open, setOpen] = useState<string | null>(null);
  const shown = open ? chunks.get(open) : undefined;

  if (!cites.length) return null;

  return (
    <>
      <div className="mt-1.5 flex flex-wrap gap-1.5">
        {cites.map((cite) => {
          const chunk = chunks.get(cite);
          const isOpen = open === cite;
          return (
            <button
              key={cite}
              onClick={() => setOpen(isOpen ? null : cite)}
              title={chunk?.source_id ?? "unknown source"}
              className={`rounded border px-1.5 py-0.5 font-mono text-[10px] transition ${
                isOpen
                  ? "border-accent bg-accent-soft text-accent"
                  : "border-line text-muted hover:border-accent hover:text-accent"
              }`}
            >
              {chunk?.media ? "🖼 image" : (chunk?.locator ?? cite)}
            </button>
          );
        })}
      </div>

      {shown && (
        <div className="mt-2 border-l-2 border-accent bg-accent-soft/40 px-3 py-2 text-xs">
          <div className="mb-1 text-[10px] text-muted">
            {shown.source_id} · {shown.locator}
            {shown.speaker ? ` · ${shown.speaker}` : ""}
          </div>
          {shown.media ? (
            // the evidence is the screenshot itself, not a description of it
            <a
              href={`${API}/api/projects/${projectId}/files/${shown.media}`}
              target="_blank"
              rel="noreferrer"
            >
              <img
                src={`${API}/api/projects/${projectId}/files/${shown.media}`}
                alt={shown.source_id}
                className="max-w-full rounded border border-line"
              />
            </a>
          ) : (
            shown.text
          )}
        </div>
      )}
    </>
  );
}
