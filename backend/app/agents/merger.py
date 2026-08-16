"""Agent 2 — collapse the same point made in different files into one insight.

No model call. Two extractors reading two transcripts will both report "drivers phone
Ravi every morning"; that is one problem, not two. And the number of *independent*
sources saying it is the best ranking signal we have, so it must be counted correctly.
"""

import re

from app.graph.state import DiscoveryState
from app.schemas.discovery import Finding, Insight

# words that carry no meaning for matching — everything else is signal
NOISE = {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "by", "can", "cannot",
    "do", "does", "each", "every", "for", "from", "has", "have", "in", "into", "is", "it",
    "its", "must", "no", "not", "of", "on", "or", "per", "s", "so", "that", "the", "their",
    "them", "then", "there", "they", "this", "to", "up", "via", "was", "were", "when",
    "which", "who", "will", "with", "would",
}

SIMILAR_ENOUGH = 0.4

# crude but earns its place: "assigns", "assignment" and "assignments" are the same idea,
# and three extractors will each pick a different one
SUFFIXES = ("ments", "ment", "ings", "ing", "ies", "ed", "es", "s")


def stem(word: str) -> str:
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def keywords(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {stem(w) for w in words if w not in NOISE and len(w) > 2}


def overlap(a: set[str], b: set[str]) -> float:
    """Jaccard. Robust to rephrasing and length, unlike comparing strings directly."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def merge(findings: list[Finding]) -> list[Insight]:
    # ponytail: O(n^2) over ~150 findings is ~11k set comparisons — microseconds. If a
    # client ever hands us thousands, switch to embeddings + a nearest-neighbour index.
    # Single-linkage: a finding joins a group if it resembles ANY member, not the group's
    # accumulated vocabulary — which only grows and drags every similarity score down.
    groups: list[tuple[list[set[str]], Insight]] = []

    for finding in findings:
        terms = keywords(finding.text)
        match = None
        for members, insight in groups:
            # only ever merge like with like: a pain and a requirement can describe the
            # same subject and still be different things to act on
            if insight.type != finding.type:
                continue
            if any(overlap(terms, member) >= SIMILAR_ENOUGH for member in members):
                match = (members, insight)
                break

        if match is None:
            groups.append(
                (
                    [terms],
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
        members.append(terms)
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
