"""LangGraph nodes — the units that think.

One file per node, each a plain function `(state) -> dict of state updates`:

    extractor.py   one source  -> atomic findings, each citing a chunk
    synthesizer.py findings    -> goal, current process, pain points, requirements
    gap_finder.py  everything  -> what the client never told us
    redesigner.py  brief       -> a simpler way of working
    outliner.py    redesign    -> features, roles, screens, flow
    prototyper.py  outline     -> a self-contained clickable HTML demo

Nodes call the model. Deterministic work (parsing, fetching) belongs in app/tools.
"""
