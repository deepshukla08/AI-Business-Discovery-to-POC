"""Agent 2 — collapse the same point made in different files into one insight.

Two extractors reading two transcripts will both report "drivers phone Ravi every
morning"; that is one problem, not two. And the number of *independent* sources saying it
is the best ranking signal we have, so it must be counted correctly.

Sameness is judged by embedding the findings and comparing vectors. Word overlap was tried
first and measurably does not work — on a real run these two scored 0.29 and 0.30:

    "Several appointment entries are missing patient phone numbers."
    "Phone numbers are missing on 6 of 11 booked rows in the screenshot."

while this pair, which is NOT the same point, scored 0.33:

    "Baner branch uses a paper diary."   /   "The Baner branch opens at 9 am."

No threshold separates those. Cosine on embeddings puts the true pairs at 0.85-0.90 and
the false one at 0.79, which does.
"""

import math
import re

from app.agents import llm
from app.graph.state import DiscoveryState
from app.schemas.discovery import Finding, Insight

# Measured on real findings: the closest true pair sits at 0.851 and the most adversarial
# false pair ("drivers phone Ravi for assignments" vs "customers phone Ravi for status")
# at 0.840. The margin is thin, so the same-type rule below still does real work.
SAME_MEANING = 0.85

# Fallback only, when the embedding service is unavailable. Deliberately strict: it fails
# toward leaving duplicates, which you can see, rather than merging two different findings
# into one, which silently deletes evidence.
SAME_WORDS = 0.5

NOISE = {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "by", "can", "cannot",
    "do", "does", "each", "every", "for", "from", "has", "have", "in", "into", "is", "it",
    "its", "must", "no", "not", "of", "on", "or", "per", "s", "so", "that", "the", "their",
    "them", "then", "there", "they", "this", "to", "up", "via", "was", "were", "when",
    "which", "who", "will", "with", "would",
}
SUFFIXES = ("ments", "ment", "ings", "ing", "ies", "ed", "es", "s")


def stem(word: str) -> str:
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {stem(w) for w in words if w not in NOISE and len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    size = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / size if size else 0.0


def merge(findings: list[Finding]) -> list[Insight]:
    vectors = llm.embed([f.text for f in findings]) if findings else []
    if vectors is None:
        words = [keywords(f.text) for f in findings]
        alike = lambda i, j: jaccard(words[i], words[j]) >= SAME_WORDS  # noqa: E731
    else:
        alike = lambda i, j: cosine(vectors[i], vectors[j]) >= SAME_MEANING  # noqa: E731

    # ponytail: O(n^2) over ~150 findings is ~11k comparisons — milliseconds. If a client
    # ever hands us thousands, switch to a nearest-neighbour index over the same vectors.
    # Single-linkage: a finding joins a group if it resembles ANY member, not the group's
    # average, which drifts as the group grows.
    groups: list[tuple[list[int], Insight]] = []

    for index, finding in enumerate(findings):
        match = None
        for members, insight in groups:
            # only ever merge like with like: a pain and a requirement can describe the
            # same subject and still be different things to act on
            if insight.type != finding.type:
                continue
            if any(alike(index, member) for member in members):
                match = (members, insight)
                break

        if match is None:
            groups.append(
                (
                    [index],
                    Insight(
                        type=finding.type,
                        text=finding.text,
                        cites=list(finding.cites),
                        sources=[finding.source_id] if finding.source_id else [],
                    ),
                )
            )
            continue

        members, insight = match
        members.append(index)
        insight.cites += [c for c in finding.cites if c not in insight.cites]
        if finding.source_id and finding.source_id not in insight.sources:
            insight.sources.append(finding.source_id)
        # keep the fuller wording — the longer statement usually carries the detail
        if len(finding.text) > len(insight.text):
            insight.text = finding.text

    # corroboration first: something three independent sources mention outranks
    # something said once, however vividly
    return sorted(
        (insight for _, insight in groups),
        key=lambda i: (len(i.sources), len(i.cites)),
        reverse=True,
    )


def run(state: DiscoveryState) -> dict:
    """LangGraph node."""
    return {"insights": merge(state["findings"])}
