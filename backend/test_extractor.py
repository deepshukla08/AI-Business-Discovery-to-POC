"""Does the extractor actually read? python test_extractor.py

Costs one Gemini call. The parsers are covered for free by test_tools.py; this is the only
check that grades a model's output, against the traps in samples/answers/zippo.md.
"""

from collections import Counter
from pathlib import Path

from app.agents import extractor
from app.tools import transcript

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "zippo" / "call_1_kickoff.txt"


def main() -> None:
    chunks = transcript.parse(SAMPLE.read_text(encoding="utf-8"), SAMPLE.name)
    findings = extractor.extract(chunks)

    assert len(findings) >= 20, f"only {len(findings)} findings from a 41-minute call"

    real_ids = {chunk.id for chunk in chunks}
    assert all(f.cites for f in findings), "a finding survived with no citation"
    assert all(cite in real_ids for f in findings for cite in f.cites), "invented citation"

    blob = " ".join(f.text.lower() for f in findings)
    # trap 3: said once, in passing, and dismissed by the person running the meeting
    assert "csv" in blob, "missed the daily-CSV requirement (mentioned once)"
    # trap 5: what Priya asked for is a fact about the ask, not a requirement
    assert "app" in blob, "missed the stated want entirely"

    counts = Counter(f.type for f in findings)
    print(f"extractor   {len(findings)} findings {dict(counts)}, every one cited")

    for kind in ("pain", "requirement", "constraint"):
        for finding in [f for f in findings if f.type == kind][:4]:
            print(f"  {kind:11} {finding.text[:74]}  [{', '.join(finding.cites)}]")


if __name__ == "__main__":
    main()
