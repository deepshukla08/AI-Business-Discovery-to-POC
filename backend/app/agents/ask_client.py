"""The pause. Not an agent — the point where the machine stops and waits for a human.

Everything downstream (the proposal, the app outline, the prototype) is a design decision.
Making those on top of unanswered questions is how consultancies end up rebuilding things.
So the graph stops here, hands the open questions back, and only continues once someone has
either answered them or explicitly decided to proceed without.

This is the one thing a chain of function calls could not do: interrupt() checkpoints the
entire run to disk and returns; resuming replays nothing, it simply carries on.
"""

from langgraph.types import interrupt

from app.graph.state import DiscoveryState
from app.schemas.discovery import Answer


def run(state: DiscoveryState) -> dict:
    gaps = state.get("gaps", [])
    if not gaps:
        return {"answers": []}

    # Blocks here. The value is handed to whoever is watching; the run is checkpointed
    # and this function returns only when resumed with Command(resume=...).
    replies = interrupt({"gaps": [gap.model_dump() for gap in gaps]})

    answered = [
        Answer(question=reply["question"], answer=reply["answer"])
        for reply in replies or []
        if reply.get("answer", "").strip()
    ]
    return {"answers": answered}
