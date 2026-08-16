"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import BriefView from "@/components/brief-view";
import FindingsView from "@/components/findings-view";
import PrototypeView from "@/components/prototype-view";
import RunProgress from "@/components/run-progress";
import SolutionView from "@/components/solution-view";
import { api, formatSize, type ClientInput, type Project, type RunResult } from "@/lib/api";

// input kinds are equals, so they share one neutral chip and are told apart by the word
const KIND_CHIP = "bg-raised text-muted border border-line";

// The pipeline, one step at a time. `built` flips as each agent lands.
const STAGES: [string, boolean][] = [
  ["Ingest", true],
  ["Extract", true],
  ["Merge", true],
  ["Brief", true],
  ["Gaps", true],
  ["Redesign", true],
  ["Outline", true],
  ["Prototype", true],
];

type Tab = "files" | "paste" | "url";
type View = "brief" | "solution" | "prototype" | "evidence";

export default function ProjectView({ id }: { id: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [tab, setTab] = useState<Tab>("files");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [log, setLog] = useState<{ text: string; tone: "ok" | "skip" | "bad" }[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [view, setView] = useState<View>("brief");
  const [stage, setStage] = useState(0);
  const [stageDetail, setStageDetail] = useState("");

  const chunkIndex = useMemo(
    () => new Map((result?.chunks ?? []).map((c) => [c.id, c])),
    [result],
  );

  useEffect(() => {
    api.project(id).then(setProject).catch((e: Error) => setError(e.message));
    api.lastRun(id).then(setResult).catch(() => setResult(null)); // 404 = never run
  }, [id]);

  async function refresh() {
    setProject(await api.project(id));
  }

  async function act(action: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await action();
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function startRun() {
    setRunning(true);
    setLog([]);
    setError("");
    setStage(0);
    setStageDetail("");
    const say = (text: string, tone: "ok" | "skip" | "bad" = "ok") =>
      setLog((lines) => [...lines, { text, tone }]);

    // the friendly loader tracks the same events as the technical log, one level up
    let landed = 0;
    let expected = 0;

    const t0 = performance.now();
    const stamp = () => `+${((performance.now() - t0) / 1000).toFixed(2)}s`;

    try {
      await api.runDiscovery(id, (e) => {
        console.log(`%c[run ${stamp()}] ${e.event}`, "color:#6ea8fe;font-weight:600", e);

        if (e.event === "start") {
          const resuming = e.resuming?.length;
          say(
            resuming
              ? `resuming from ${e.resuming.join(", ")} — earlier work is cached`
              : `reading ${e.inputs} input${e.inputs === 1 ? "" : "s"}`,
          );
          setStage(0);
          setStageDetail(
            resuming
              ? "picking up where the last run stopped"
              : `${e.inputs} file${e.inputs === 1 ? "" : "s"} to read`,
          );
        }
        if (e.event === "parsed") {
          say(`${e.label} → ${e.chunks} chunks`);
          setStageDetail(`${e.label} — ${e.chunks} pieces`);
        }
        if (e.event === "skipped") {
          say(`${e.label} — ${e.reason}`, "skip");
          setStageDetail(`skipped ${e.label}`);
        }
        if (e.event === "node_start") {
          say(`extract ×${e.sources} in parallel…`);
          expected = e.sources;
          setStage(1);
          setStageDetail(`reading ${e.sources} sources at once`);
        }
        if (e.event === "node_done") {
          say(`${e.source} → ${e.findings} findings`);
          landed += 1;
          setStageDetail(`${e.source} done — ${landed} of ${expected}`);
        }
        if (e.event === "merged") {
          say(`merged — ${e.collapsed} duplicates gone, ${e.corroborated} corroborated`);
          setStage(3);
          setStageDetail(
            `${e.collapsed} duplicates collapsed, ${e.corroborated} confirmed by more than one source`,
          );
        }
        if (e.event === "brief") {
          say(`brief — ${e.steps} steps, ${e.pains} pains, ${e.requirements} requirements`);
          setStage(4);
          setStageDetail(`${e.pains} problems worth fixing`);
        }
        if (e.event === "gaps") {
          say(`${e.gaps} open questions`);
          setStage(5);
          setStageDetail(`${e.gaps} things the client never told us`);
        }
        if (e.event === "redesign") {
          say(`proposal — ${e.steps} steps, ${e.not_solved} pains left unsolved`);
          setStage(6);
          setStageDetail(`a ${e.steps}-step way of working`);
        }
        if (e.event === "outline") {
          say(`"${e.app_name}" — ${e.screens} screens, ${e.features} features`);
          setStage(7);
          setStageDetail(`${e.app_name} — ${e.screens} screens`);
        }
        if (e.event === "prototype") {
          say(
            e.ok
              ? `prototype — ${(e.bytes / 1024).toFixed(0)} KB`
              : `prototype rejected — ${e.faults.join("; ")}`,
            e.ok ? "ok" : "skip",
          );
          setStage(8);
          setStageDetail(e.ok ? "a clickable demo" : "generation failed its checks");
        }
        if (e.event === "error") {
          console.error("[run] failed:", e.message);
          say(e.message, "bad");
        }
        if (e.event === "done") {
          setResult({
            chunks: e.chunks,
            findings: e.findings,
            insights: e.insights,
            brief: e.brief,
            gaps: e.gaps,
            redesign: e.redesign,
            outline: e.outline,
            prototype: e.prototype,
            prototype_faults: e.prototype_faults,
          });
          setView("brief");
          say("done");

          console.groupCollapsed(
            `%c[run] state — ${e.chunks.length} chunks → ${e.findings.length} findings → ${e.insights.length} insights → ${e.gaps.length} gaps`,
            "color:#6ea8fe;font-weight:600",
          );
          console.log("brief", e.brief);
          console.log("gaps", e.gaps);
          console.table(
            e.findings.map((f) => ({
              type: f.type,
              finding: f.text,
              cites: f.cites.join(", "),
              source: f.source_id,
            })),
          );
          console.log("chunks", e.chunks);
          console.groupEnd();
        }
      });
      await refresh();
    } catch (e) {
      say((e as Error).message, "bad");
    } finally {
      setRunning(false);
    }
  }

  if (error && !project) return <p className="p-6 text-sm text-ink">{error}</p>;
  if (!project) return <p className="p-6 text-sm text-muted">Loading…</p>;

  const stagesDone = result?.gaps ? 5 : result ? 2 : 0;

  return (
    <div className="flex min-h-[calc(100vh-57px)] flex-col lg:flex-row">
      {/* ── left rail: everything you put in ─────────────────────────── */}
      <aside className="slim shrink-0 border-line lg:sticky lg:top-[57px] lg:h-[calc(100vh-57px)] lg:w-[340px] lg:overflow-y-auto lg:border-r">
        <div className="space-y-5 p-5">
          <div>
            <Link href="/" className="text-[11px] text-muted hover:text-accent">
              ← all projects
            </Link>
            <h1 className="mt-1.5 text-lg font-semibold leading-tight tracking-tight">
              {project.name}
            </h1>
            <p className="text-xs text-muted">{project.client || "no client set"}</p>
          </div>

          <div className="rounded-2xl border border-line bg-surface">
            <div className="flex gap-1 border-b border-line p-1.5">
              {(
                [
                  ["files", "Upload"],
                  ["paste", "Paste"],
                  ["url", "Website"],
                ] as [Tab, string][]
              ).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setTab(key)}
                  className={`flex-1 rounded-lg px-2 py-1.5 text-xs transition ${
                    tab === key ? "bg-accent-soft text-accent" : "text-muted hover:text-ink"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="p-3">
              {tab === "files" && (
                <FileDrop busy={busy} onFiles={(files) => act(() => api.uploadFiles(id, files))} />
              )}
              {tab === "paste" && (
                <PasteForm
                  busy={busy}
                  onSubmit={(label, content) => act(() => api.addText(id, label, content))}
                />
              )}
              {tab === "url" && (
                <UrlForm busy={busy} onSubmit={(url) => act(() => api.addUrl(id, url))} />
              )}
              {error && <p className="mt-2 text-[11px] text-ink">{error}</p>}
            </div>
          </div>

          <div>
            <div className="mb-2 flex items-baseline justify-between">
              <h2 className="text-[11px] font-medium uppercase tracking-wide text-muted">
                Client inputs
              </h2>
              <span className="text-[11px] text-muted">{project.inputs.length}</span>
            </div>
            {project.inputs.length === 0 ? (
              <p className="rounded-lg border border-dashed border-line px-3 py-6 text-center text-xs text-muted">
                Nothing yet. Add the messy stuff.
              </p>
            ) : (
              <ul className="space-y-1">
                {project.inputs.map((input) => (
                  <InputRow
                    key={input.id}
                    input={input}
                    onDelete={() => act(() => api.deleteInput(id, input.id))}
                  />
                ))}
              </ul>
            )}
          </div>

          <div className="space-y-2">
            <button
              onClick={startRun}
              disabled={running || !project.inputs.length}
              className="w-full rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-on-accent shadow-lg shadow-accent/20 transition hover:brightness-110 active:scale-[0.99] disabled:opacity-30 disabled:shadow-none"
              title={
                project.inputs.length
                  ? "Read everything and produce a brief"
                  : "Add at least one input first"
              }
            >
              {running ? "Running…" : result ? "Run again" : "Run discovery"}
            </button>
            {!running && !project.inputs.length && (
              <p className="text-center text-[11px] text-muted">
                Nothing collected yet — add a file, or paste text and press{" "}
                <span className="text-ink">Add notes</span>.
              </p>
            )}

            <div className="flex flex-wrap gap-1">
              {STAGES.map(([name, built], i) => (
                <span
                  key={name}
                  title={built ? "built" : "not built yet"}
                  className={`rounded px-1.5 py-0.5 text-[10px] ${
                    i < stagesDone
                      ? "bg-accent-soft text-accent"
                      : built
                        ? "border border-line text-muted"
                        : "border border-dashed border-line text-muted/50"
                  }`}
                >
                  {name}
                </span>
              ))}
            </div>

            {log.length > 0 && (
              <div className="slim max-h-56 overflow-y-auto rounded-lg bg-raised p-2.5 font-mono text-[10.5px] leading-relaxed">
                {log.map((line, i) => (
                  <div
                    key={i}
                    className={
                      line.tone === "bad"
                        ? "font-semibold text-ink underline decoration-dotted"
                        : line.tone === "skip"
                          ? "text-muted/60 italic"
                          : "text-muted"
                    }
                  >
                    {line.tone === "bad" ? "✕ " : "› "}
                    {line.text}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* ── right: everything that comes out ─────────────────────────── */}
      <section className="min-w-0 flex-1 p-5 lg:p-8">
        {running ? (
          <RunProgress at={stage} detail={stageDetail} />
        ) : !result ? (
          <div className="mx-auto max-w-md py-24 text-center">
            <p className="text-sm text-muted">
              Add the client&apos;s transcripts, chat exports, documents and screenshots on the
              left, then run discovery.
            </p>
            <p className="mt-2 text-xs text-muted/70">
              Everything produced here points back at the line it came from.
            </p>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-5">
            <div className="flex gap-1">
              {(
                [
                  ["brief", "Brief", result.gaps?.length ?? 0],
                  ["solution", "Solution", result.outline?.screens.length ?? 0],
                  ["prototype", "Prototype", result.prototype ? 1 : 0],
                  ["evidence", "Evidence", result.insights?.length ?? result.findings.length],
                ] as [View, string, number][]
              ).map(([key, label, count]) => (
                <button
                  key={key}
                  onClick={() => setView(key)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition ${
                    view === key
                      ? "border-accent bg-accent-soft text-accent"
                      : "border-line text-muted hover:text-ink"
                  }`}
                >
                  {label}
                  <span className="ml-1.5 text-[11px] opacity-60">{count}</span>
                </button>
              ))}
            </div>

            {view === "brief" &&
              (result.brief ? (
                <BriefView
                  brief={result.brief}
                  gaps={result.gaps ?? []}
                  chunks={chunkIndex}
                  projectId={id}
                />
              ) : (
                <p className="rounded-2xl border border-dashed border-line px-6 py-12 text-center text-sm text-muted">
                  This run predates the brief stage. Run again to generate one.
                </p>
              ))}

            {view === "solution" && (
              <SolutionView
                redesign={result.redesign}
                outline={result.outline}
                chunks={chunkIndex}
                projectId={id}
              />
            )}

            {view === "prototype" && (
              <PrototypeView
                projectId={id}
                ok={Boolean(result.prototype)}
                faults={result.prototype_faults ?? []}
                outline={result.outline}
              />
            )}

            {view === "evidence" && (
              <FindingsView result={result} projectId={id} chunks={chunkIndex} />
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function InputRow({ input, onDelete }: { input: ClientInput; onDelete: () => void }) {
  return (
    <li className="group flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-raised">
      <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] ${KIND_CHIP}`}>
        {input.kind}
      </span>
      <span className="min-w-0 flex-1 truncate text-xs" title={input.label}>
        {input.label}
      </span>
      <span className="shrink-0 text-[10px] text-muted">{formatSize(input.size)}</span>
      <button
        onClick={onDelete}
        aria-label={`Remove ${input.label}`}
        className="shrink-0 text-xs text-muted opacity-0 transition group-hover:opacity-100 hover:text-ink"
      >
        ✕
      </button>
    </li>
  );
}

function FileDrop({ busy, onFiles }: { busy: boolean; onFiles: (files: File[]) => void }) {
  const [over, setOver] = useState(false);
  const picker = useRef<HTMLInputElement>(null);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const files = Array.from(e.dataTransfer.files);
        if (files.length) onFiles(files);
      }}
      onClick={() => picker.current?.click()}
      className={`cursor-pointer rounded-lg border-2 border-dashed px-4 py-6 text-center transition ${
        over ? "border-accent bg-accent-soft" : "border-line hover:border-accent/50"
      }`}
    >
      <input
        ref={picker}
        type="file"
        multiple
        hidden
        onChange={(e) => {
          const files = Array.from(e.target.files ?? []);
          if (files.length) onFiles(files);
          e.target.value = "";
        }}
      />
      <p className="text-xs">{busy ? "Uploading…" : "Drop files, or click to choose"}</p>
      <p className="mt-1 text-[10px] text-muted">.txt .vtt · WhatsApp · PDF · screenshots</p>
    </div>
  );
}

function PasteForm({
  busy,
  onSubmit,
}: {
  busy: boolean;
  onSubmit: (label: string, content: string) => void;
}) {
  const [label, setLabel] = useState("");
  const [content, setContent] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!content.trim()) return;
        onSubmit(label.trim() || "Pasted notes", content);
        setLabel("");
        setContent("");
      }}
      className="space-y-2"
    >
      <input
        value={label}
        onChange={(e) => setLabel(e.target.value)}
        placeholder="Label — e.g. Call notes, 12 March"
        className="w-full rounded-lg border border-line bg-transparent px-2.5 py-1.5 text-xs outline-none focus:border-accent"
      />
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={7}
        placeholder="Paste a transcript, chat log, or your own notes…"
        className="slim w-full rounded-lg border border-line bg-transparent px-2.5 py-1.5 font-mono text-[11px] outline-none focus:border-accent"
      />
      {/* goes solid the moment there is something to add, so it stops looking optional */}
      <button
        type="submit"
        disabled={busy || !content.trim()}
        className={`w-full rounded-lg px-3 py-1.5 text-xs transition ${
          content.trim()
            ? "bg-ink text-bg hover:opacity-90"
            : "border border-line text-muted opacity-60"
        }`}
      >
        {content.trim() ? "Add notes →" : "Add notes"}
      </button>
    </form>
  );
}

function UrlForm({ busy, onSubmit }: { busy: boolean; onSubmit: (url: string) => void }) {
  const [url, setUrl] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!url.trim()) return;
        onSubmit(url.trim());
        setUrl("");
      }}
      className="space-y-2"
    >
      <input
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        type="url"
        placeholder="https://their-current-system.com"
        className="w-full rounded-lg border border-line bg-transparent px-2.5 py-1.5 text-xs outline-none focus:border-accent"
      />
      <p className="text-[10px] text-muted">
        Their existing site. Read to understand the current system, not to copy it.
      </p>
      <button
        type="submit"
        disabled={busy || !url.trim()}
        className={`w-full rounded-lg px-3 py-1.5 text-xs transition ${
          url.trim()
            ? "bg-ink text-bg hover:opacity-90"
            : "border border-line text-muted opacity-60"
        }`}
      >
        {url.trim() ? "Add reference →" : "Add reference"}
      </button>
    </form>
  );
}
