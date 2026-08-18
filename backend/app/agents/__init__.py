"""The units that think. One file per graph node, plus two shared helpers.

    extractor.py    one source      -> findings, each citing a chunk        (model)
    merger.py       all findings    -> deduped insights + corroboration     (embeddings)
    synthesizer.py  insights        -> the discovery brief                  (model)
    gap_finder.py   brief + insights-> what the client never told us        (model)
    ask_client.py   gaps            -> STOPS and waits for a human          (no model)
    redesigner.py   brief + answers -> a simpler way of working             (model)
    outliner.py     redesign        -> features, roles, screens, flow       (model)
    prototyper.py   outline         -> a self-contained clickable demo      (model)

    llm.py          the only file that talks to Gemini
    citations.py    the rule every agent is held to, enforced in code

Each node is a plain function `run(state) -> dict of state updates`. Nodes return data and
touch nothing else — no files, no database — which is what lets the whole graph be tested
with the model stubbed and no side effects.

Prompts live in prompts/*.md so they can be edited without opening Python.
"""
