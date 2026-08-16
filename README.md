# AI Business Discovery to POC

Turns the scattered mess a client hands you — meeting transcripts, WhatsApp exports, PDFs,
screenshots — into a **sourced business brief**, the **questions nobody answered**, a **better
way of working**, and a **clickable POC** of the proposed solution.

Every single claim it produces points back at the exact line someone said it.

---

## The problem this solves

A consultancy takes on a new client. Requirements arrive as two recorded calls, a WhatsApp
group where the ops manager vents at 11pm, a process document written in 2022, and screenshots
of the spreadsheet they actually run the business on.

Someone then spends **two or three days** reading all of it to produce a proposal. They do this
for every lead, and roughly half the leads never convert. When they rush it, things get missed —
a requirement buried at minute 31 of call one never reaches the quote, and surfaces six weeks
into the build as an argument about scope.

This compresses that into about ninety seconds, and does three things a tired human does badly:

1. **Reads everything at equal attention.** A person skims by hour three.
2. **Tracks what was never answered.** Nobody manually follows an unanswered question across
   three weeks of WhatsApp. Software can.
3. **Separates what the client asked for from what the evidence says they need.**

---

## Run it

Two terminals.

**Backend** — FastAPI, port 8000

```powershell
cd backend
py -m venv .venv                  # first time only
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # first time only
copy .env.example .env            # then paste your Gemini API key into it
uvicorn app.main:app --reload
```

Interactive API docs at http://localhost:8000/docs

**Frontend** — Next.js, port 3000

```powershell
cd frontend
npm install                       # first time only
npm run dev
```

Open http://localhost:3000, create a project, drag in everything from `samples/zippo/`, press
**Run discovery**.

A Gemini API key comes from https://aistudio.google.com/apikey — the free tier is enough.

---

## Try it on a sample client

Two fictional engagements, in deliberately unalike businesses — because a pipeline that only
works on logistics doesn't work.

| | **`samples/zippo/`** | **`samples/smilecraft/`** |
|---|---|---|
| Business | Mumbai last-mile delivery, 40 drivers | Three dental clinics in Pune |
| Shape of the pain | physical, time-critical, field staff | appointment-based, desk-bound, records-heavy |
| Runs on | one spreadsheet and one man's phone | practice software at two branches, a paper diary at the third |
| Files | 2 transcripts · WhatsApp · SOP PDF · spreadsheet screenshot | 2 transcripts · WhatsApp · policy PDF · appointment-book screenshot |
| Chunks | 378 | 263 |

Both are **graded test fixtures, not decoration.** Each carries the same five planted failures,
and each folder's `TRAPS.md` is the answer key:

| # | The trap | Zippo | SmileCraft |
|---|---|---|---|
| 1 | A question asked and never answered | daily order volume — "depends", twice | no-show rate — "depends on the day", twice |
| 2 | A document that contradicts reality | SOP: planning happens the evening before; Ravi does it at 5:45am | policy: double booking "not permitted"; the screenshot shows two |
| 3 | A requirement stated once and dismissed | accounts needs a daily CSV by 8pm | insurance pre-auth dies after 24 hours |
| 4 | Evidence only in the screenshot | a `Driver2` column, six spellings of "delivered" | two patients in one slot, `Conf` stuck on TBC, root canal written four ways, phone numbers missing |
| 5 | The stated want isn't the real need | asks for a customer tracking app | asks for a patient booking app |

The point of the second one is that the *right answer looks nothing like the first*. Zippo's
proposal is a dispatch board; SmileCraft's should be about confirmations, recalls and one patient
record — and if the pipeline produces a dispatch board for a dental clinic, it is pattern-matching
rather than reading.

Regenerate a sample's PDF and screenshot with
`pip install fpdf2 pillow && python samples/<name>/source/make_fixtures.py`.

---

## How it works

```
 5 files
    │  tools/ — regex, pypdf. No model. Milliseconds.
    ▼
 378 chunks          each carries a locator: 00:31:02 · 11/03/2024 9:41 am · p1 §3.1 · image
                    145 + 118 + 85 + 29 + 1 for the image
    │
    ├── extract(call_1)      ┐
    ├── extract(call_2)      │  one model call per source, in parallel
    ├── extract(whatsapp)    ├─ merged into state by operator.add
    ├── extract(pdf)         │
    └── extract(screenshot)  ┘  the PNG goes to the model as pixels
    │
    ▼
 ~150 findings       fact · pain · requirement · constraint · question, each citing chunk ids
    │
  merge              no model: collapses duplicates, counts independent corroboration
    ▼
 ~110 insights       "3 sources say this" is the ranking signal
    │
 synthesize          the brief: goal, current process, pains, requirements, constraints
    │
 find_gaps           unanswered · contradiction · never_discussed
    │
 ask_client       ⏸  STOPS. Everything below is a design decision.
    │               The consultant answers what they can, then it continues.
 redesign            as-is vs to-be, every step tagged removed/automated/simplified/new
    │
 outline             app name, roles, features, screens, end-to-end flow
    │
 prototype           one self-contained HTML file, validated before it is shown
```

Seven agents, one file each in `backend/app/agents/`, with prompts as editable `.md` files in
`agents/prompts/` rather than buried in Python.

---

## The decisions, and why

### Every claim must cite a chunk, and it's enforced in code

An LLM handed a pile of documents will happily produce a beautiful requirements document
containing three requirements nobody asked for. It reads well. It's wrong. And you can't tell
which parts, because it all sounds equally confident.

So the prompt asks for citations — and then `agents/citations.py` **strips any citation that
doesn't resolve to a real chunk id and discards whatever is left with none.** A hallucinated
source and a hallucinated claim are the same failure; neither survives.

One deliberate exception: a gap of kind `never_discussed` may be uncited, because you cannot
cite the absence of something. That exception is explicit in code, not an accident.

### Chunking is code, not a model

`tools/` never calls a model. `agents/` always does. Deciding whether a file is a WhatsApp
export is a regex, not a judgment — asking a model would cost a request, add a second, and be
occasionally wrong. It also makes routing unit-testable, which a model's choice never is.

The chunk boundary decides how precise a citation can be, so each format is split at its own
natural unit: an utterance, a message, a numbered clause. Chunking a PDF by page would mean the
best you could ever say is "somewhere on page 1".

### One model call per source, not one for everything

Splitting costs more requests. It buys three things: the model reads one document properly
instead of skimming five; `source_id` is true by construction (a single combined call stamped
every finding with whichever file parsed first, which would have poisoned the corroboration
ranking); and wall-clock becomes the slowest source rather than the sum.

### Screenshots go to the model as pixels

The alternative — OCR, or a "describe the image" pass first — gives you characters, or a
paragraph the model wrote about the image. Neither is the evidence. Sending the PNG directly
means one call, and clicking a citation shows **the actual screenshot**.

It also costs less than you'd expect: measured, that screenshot is 1,071 tokens — about a sixth
of the kickoff transcript.

### LangGraph, for the checkpointer

A linear pipeline doesn't need a graph. Durable state does.

State is written to a SQLite file after every node, keyed by project. A run killed halfway —
a browser refresh, a crash, a dropped connection — **resumes from the last completed node**
instead of repaying the five extract calls. Press Run again and the log says
`resuming from synthesize — earlier work is cached`.

The same machinery gives the pause: `ask_client` calls `interrupt()`, which checkpoints the whole
run and returns. The browser gets the open questions, the consultant answers what they can, and
`POST /run/answers` resumes with `Command(resume=...)` — nothing is replayed, it simply carries
on with the answers in state, and the redesigner is told the client's answers outrank the
evidence where they disagree.

Answering nothing is a supported choice, and a different one from never having been asked: the
unanswered questions stay on the list and visible in the brief.

Two details that are easy to get wrong:

- The checkpoint's **deserialisation allowlist** is pinned to our own schemas. LangGraph's
  default accepts any type it finds in the file and warns that permissive mode will stop working.
- On a resumed run the finished nodes emit no events, so the result is read from
  `pipeline.get_state()` rather than from what the stream handler accumulated. Building it from
  the events would silently drop everything the previous attempt produced.

The fan-out is the other half. `Send` spawns one extractor per source, and the
`Annotated[list, operator.add]` reducer on `findings` merges their results. Without that reducer
the last node to finish silently overwrites the others — a bug that produces fewer findings and
no error.

### JSON files on disk, no database

A POC holds a handful of projects and never queries across them. No joins, no search, no
concurrent writers. Postgres would add a server, a connection string, migrations, and setup
steps in this README, and buy nothing. SQLite arrives on its own when checkpointing lands,
because LangGraph needs it.

### A model fallback chain

The free tier allows **20 requests per day, per model**. `config.py` lists six Flash models;
`llm.py` walks the chain on both 503 (contended) and 429 (daily quota exhausted), so each entry
is a separate allowance. It does not retry a 429 on the same model — a daily quota won't clear
in two seconds.

This is a POC-scale answer to a billing constraint, not clever architecture. In production you
pay for one model and get one predictable quality bar.

### Per-agent thinking levels

`extract` runs at `LOW` — it classifies lines and copies ids. `find_gaps` runs at `HIGH` — it
reasons about absence and contradiction across every source at once. `prototype` runs at `HIGH`
because writing working code is the hardest thing here. Set at each call site, in the file you'd
be looking at anyway.

### The prototype is validated before it is shown

It's the only agent returning code rather than structured data, so a schema can't police it.
`prototyper.py` checks the output parses, isn't truncated, contains a script, and pulls nothing
from the network. If it fails, the UI says which check failed and shows the outline instead of
rendering a broken page and calling it a demo.

It renders in an iframe with `sandbox="allow-scripts"` and **no** `allow-same-origin`, so
model-written JavaScript runs in a unique origin and can't reach the page or the API.

---

## Layout

```
backend/app/
  main.py        assembles the app: CORS + routers
  config.py      env, paths, model chain
  api/           HTTP only — thin routers
    deps.py      shared 404 guard as a route dependency
    projects.py  inputs.py  run.py  health.py
  schemas/       pydantic shapes: Chunk, Finding, Brief, Gap, Redesign, Outline
  storage/       projects on disk (JSON + uploaded files)
  tools/         chunk · transcript · whatsapp · pdf · plain · ingest   ← no model calls
  agents/        extractor · merger · synthesizer · gap_finder ·
                 redesigner · outliner · prototyper · llm · citations   ← model calls
    prompts/     one .md per agent, editable without touching Python
  graph/         state.py (the shared object) · pipeline.py (the wiring)
  data/          uploads, run results, generated prototypes — gitignored

frontend/src/
  app/           routes
  components/    workspace UI: left rail collects, right pane shows
  lib/           types + typed backend client
```

---

## Checks

```powershell
cd backend; .\.venv\Scripts\python.exe test_tools.py      # every parser, vs the planted traps
cd backend; .\.venv\Scripts\python.exe test_pipeline.py   # merger + full graph, model stubbed
cd backend; .\.venv\Scripts\python.exe test_api.py        # inputs API
cd frontend; npm run build                                # typecheck + build

cd backend; .\.venv\Scripts\python.exe test_extractor.py  # agent 1        (1 Gemini call)
cd backend; .\.venv\Scripts\python.exe test_run.py        # upload → stream (3 Gemini calls)
```

The first four are free and deterministic. They cover the parsers against the exact traps in
`TRAPS.md`, the merge logic, and the graph wiring — including that a finding citing a fake chunk
id gets dropped while an uncited `never_discussed` gap survives.

A full five-source run costs **9 requests**.

---

## What is deliberately not built

- **No auth, no users, no multi-tenancy.** Single-user local tool.
- **No database.** See above.
- **No live reattach.** A refresh no longer wastes the work — press Run and it resumes from the
  last completed node — but you cannot watch a run you disconnected from. That needs the run
  moved into a background task with its own progress channel; resuming was the cheap 90% of it.
- **No `.docx` parser, no website fetching.** Unsupported inputs are **skipped with a visible
  reason in the run log** rather than silently contributing nothing. A website reference will use
  Gemini's built-in URL context tool rather than a parser of ours.
- **Merge similarity is word overlap, not embeddings.** Jaccard over stemmed keywords at a 0.4
  threshold, tuned against a handful of examples. Embeddings would catch "only one who knows the
  routes" ≈ "nobody else can do the allocation" — one batch request, ~30 lines, no vector
  database, and no RAG. The whole corpus is ~20,000 tokens and fits in a single prompt; adding
  retrieval here would be cargo-culting.
- **CORS is dev-origin only.** Not a deployment config.

---

## Status

All five things the assignment asks for are built and verified on real input:

| Assignment asks for | Status |
|---|---|
| 1. Take client inputs (≥3 types) | transcripts · WhatsApp · PDF · screenshots · pasted notes |
| 2. Understand the business need | brief: goal, current process, pains, requirements, constraints |
| 3. Identify what is missing or unclear | gap-finder: unanswered · contradiction · never_discussed |
| 4. Suggest a better process | redesign: as-is vs to-be, per-step change tags, and what it does *not* fix |
| 5. Create a solution outline + basic POC | outline: roles, features, screens, flow · generated clickable HTML |

Plus two things the assignment didn't ask for:

- **Checkpointing** — runs are written to SQLite after every node, so a killed run resumes
  instead of starting over.
- **A human in the loop** — the graph stops after gap analysis and will not design anything
  until the consultant has answered, or explicitly decided not to.
