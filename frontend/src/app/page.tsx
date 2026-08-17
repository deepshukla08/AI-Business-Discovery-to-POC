"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function Home() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [name, setName] = useState("");
  const [client, setClient] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.projects().then(setProjects).catch((e: Error) => setError(e.message));
  }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    setError("");
    try {
      const created = await api.createProject(name.trim(), client.trim());
      setProjects([created, ...(projects ?? [])]);
      setName("");
      setClient("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-10 px-6 py-10">
      <section>
        <h1 className="text-2xl font-semibold tracking-tight">Discovery projects</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          One project per client engagement. Drop in the transcripts, chat exports, documents and
          screenshots you collected, and the agent turns them into a sourced brief.
        </p>
      </section>

      <section className="rounded-xl border border-line bg-surface p-5">
        <h2 className="text-sm font-medium">New project</h2>
        <form onSubmit={create} className="mt-3 flex flex-col gap-3 sm:flex-row">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Project name — e.g. Dispatch modernisation"
            className="flex-1 rounded-lg border border-line bg-transparent px-3 py-2 text-sm outline-none focus:border-accent"
          />
          <input
            value={client}
            onChange={(e) => setClient(e.target.value)}
            placeholder="Client (optional)"
            className="rounded-lg border border-line bg-transparent px-3 py-2 text-sm outline-none focus:border-accent sm:w-56"
          />
          <button
            type="submit"
            disabled={busy || !name.trim()}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-on-accent shadow-lg shadow-accent/20 transition hover:brightness-110 disabled:opacity-40 disabled:shadow-none"
          >
            {busy ? "Creating…" : "Create"}
          </button>
        </form>
        {error && (
          <p className="mt-3 text-xs font-medium text-ink underline decoration-dotted">{error}</p>
        )}
      </section>

      <section>
        {projects === null ? (
          <p className="text-sm text-muted">Loading…</p>
        ) : projects.length === 0 ? (
          <div className="rounded-xl border border-dashed border-line px-6 py-12 text-center">
            <p className="text-sm text-muted">No projects yet. Create one above to get started.</p>
          </div>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {projects.map((p) => (
              <li key={p.id}>
                <Link
                  href={`/projects/${p.id}`}
                  className="block rounded-xl border border-line bg-surface p-4 transition hover:border-accent"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium">{p.name}</div>
                      <div className="truncate text-xs text-muted">{p.client || "no client set"}</div>
                    </div>
                    <span className="shrink-0 rounded-full bg-accent-soft px-2 py-0.5 text-[11px] text-accent">
                      {p.status}
                    </span>
                    {/* status doubles as progress: collecting → analysed */}
                  </div>
                  <div className="mt-4 text-xs text-muted">
                    {p.inputs.length} input{p.inputs.length === 1 ? "" : "s"} ·{" "}
                    {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
