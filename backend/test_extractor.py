"""Runnable check for step 1: python test_extractor.py

Two halves. The parser checks are free and deterministic. The extractor check costs one
Gemini call and is graded against the traps planted in sample_client/TRAPS.md.
"""

from collections import Counter
from pathlib import Path

from app.graph.pipeline import pipeline
from app.tools import transcript

SAMPLE = Path(__file__).resolve().parent.parent / "sample_client" / "call_1_kickoff.txt"


def check_parser():
    chunks = transcript.parse(SAMPLE.read_text(encoding="utf-8"), SAMPLE.name)

    assert 100 < len(chunks) < 200, f"suspicious chunk count: {len(chunks)}"
    assert len({c.id for c in chunks}) == len(chunks), "chunk ids must be unique"
    assert chunks[0].locator == "header" and "Priya Nair" in chunks[0].text

    by_locator = {c.locator: c for c in chunks}

    # the mentioned-once trap, and it wraps across three lines in the file —
    # if continuation handling is broken, the second half goes missing
    csv_line = by_locator["00:31:02"]
    assert csv_line.speaker == "Sameer Kulkarni", csv_line.speaker
    assert "daily CSV" in csv_line.text, csv_line.text
    assert "invoicing slips" in csv_line.text, "wrapped line was dropped"

    spoken = [c for c in chunks if c.speaker]
    notes = [c for c in chunks if c.locator == "note"]
    assert len(notes) >= 3, f"editor notes not detected: {len(notes)}"
    assert all(":" not in c.speaker for c in spoken), "speaker field caught too much"

    print(f"parser ok — {len(chunks)} chunks, {len(spoken)} spoken, {len(notes)} notes")
    return chunks


def check_extractor(chunks):
    state = pipeline.invoke({"project_id": "check", "chunks": chunks, "findings": []})
    findings = state["findings"]

    assert len(findings) >= 20, f"only {len(findings)} findings from a 41-minute call"

    real_ids = {c.id for c in chunks}
    assert all(f.cites for f in findings), "a finding survived with no citation"
    assert all(cite in real_ids for f in findings for cite in f.cites), "invented citation"

    blob = " ".join(f.text.lower() for f in findings)
    assert "csv" in blob, "missed the daily-CSV requirement (mentioned once, trap 3)"

    counts = Counter(f.type for f in findings)
    print(f"extractor ok — {len(findings)} findings: {dict(counts)}")

    for kind in ("pain", "requirement", "constraint", "question"):
        print(f"\n{kind.upper()}")
        for finding in [f for f in findings if f.type == kind][:6]:
            print(f"  - {finding.text}  [{', '.join(finding.cites)}]")


if __name__ == "__main__":
    check_extractor(check_parser())
