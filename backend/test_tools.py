"""Runnable check for every parser: python test_tools.py

No model calls, so this is free and instant. Graded against the traps planted in
samples/answers/ — if a locator drifts, every citation downstream becomes a lie.
"""

from pathlib import Path

from app.tools import pdf, plain, transcript, whatsapp

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "zippo"


def check_transcript():
    path = SAMPLE / "call_1_kickoff.txt"
    chunks = transcript.parse(path.read_text(encoding="utf-8"), path.name)
    by_locator = {c.locator: c for c in chunks}

    assert len(chunks) == 145, len(chunks)
    assert chunks[0].locator == "header"
    # trap 3: mentioned once, and it wraps across three lines in the file
    csv = by_locator["00:31:02"]
    assert csv.speaker == "Sameer Kulkarni" and "invoicing slips" in csv.text
    print(f"transcript  {len(chunks):4} chunks   trap 3 (daily CSV) intact")


def check_whatsapp():
    path = SAMPLE / "whatsapp_export_zippo.txt"
    chunks = whatsapp.parse(path.read_text(encoding="utf-8"), path.name)

    # 90 date-prefixed lines in the file: 85 messages + 5 system lines
    assert len(chunks) == 85, len(chunks)
    assert all(c.speaker for c in chunks), "a system line leaked in as a message"
    joined = " ".join(c.text for c in chunks)
    assert "created group" not in joined and "end-to-end encrypted" not in joined
    assert not any(c.text[:2].isdigit() and "/" in c.text[:8] for c in chunks), (
        "a message starts with a date — the split failed"
    )

    # trap 1: the dodged volume question, asked twice, answered "depends" twice
    dodges = [c for c in chunks if c.text.strip().lower() == "depends"]
    assert len(dodges) == 2, [c.locator for c in dodges]
    assert dodges[0].locator == "06/03/2024 11:47 am", dodges[0].locator
    assert dodges[0].speaker == "Ravi Deshmukh"

    assert any("<Media omitted>" in c.text for c in chunks), "media markers dropped"
    print(f"whatsapp    {len(chunks):4} messages trap 1 (dodged twice) intact")


def check_pdf():
    chunks = pdf.parse(SAMPLE / "current_process.pdf", "current_process.pdf")
    by_locator = {c.locator: c for c in chunks}

    assert len(chunks) > 15, f"clauses not split: {len(chunks)}"
    assert all(c.text for c in chunks)

    # trap 2: the stale document that contradicts what people actually do
    assert "previous evening" in by_locator["p1 §3.1"].text, by_locator["p1 §3.1"].text
    assert "Delivery Register" in by_locator["p1 §5.1"].text
    assert "weekly" in by_locator["p2 §6.2"].text
    # wrapped lines rejoined — this sentence breaks mid-way in the raw extraction
    assert "operations filing cabinet" in by_locator["p1 §5.2"].text
    print(f"pdf         {len(chunks):4} clauses  trap 2 (stale SOP) intact at §3.1")


def check_plain():
    chunks = plain.parse("First para.\n\nSecond para\nwith a wrapped line.\n", "notes.txt")
    assert len(chunks) == 2 and chunks[1].locator == "para 2"
    assert "wrapped line" in chunks[1].text
    print(f"plain       {len(chunks):4} paras")


def check_ids_unique():
    sources = [
        transcript.parse((SAMPLE / "call_1_kickoff.txt").read_text(encoding="utf-8"), "a", id_seed="a"),
        transcript.parse((SAMPLE / "call_2_followup.txt").read_text(encoding="utf-8"), "b", id_seed="b"),
        whatsapp.parse((SAMPLE / "whatsapp_export_zippo.txt").read_text(encoding="utf-8"), "c", id_seed="c"),
        pdf.parse(SAMPLE / "current_process.pdf", "d", id_seed="d"),
    ]
    ids = [c.id for source in sources for c in source]
    assert len(set(ids)) == len(ids), "chunk ids collide across sources"
    print(f"ids         {len(ids):4} chunks   all unique across 4 sources")


def check_routing():
    """The dispatcher picks by content, not filename. Still no model calls."""
    import shutil

    from app.storage import store
    from app.tools import ingest

    project = store.create("routing check")
    pid = project["id"]
    try:
        expected = {
            # a WhatsApp export deliberately saved under a name that hides what it is
            "team_chat.txt": ("whatsapp_export_zippo.txt", 85),
            "call_1_kickoff.txt": ("call_1_kickoff.txt", 145),
            "current_process.pdf": ("current_process.pdf", 29),
        }
        for label, (fixture, count) in expected.items():
            record = store.add_input(
                pid,
                {
                    "kind": store.guess_kind(label),
                    "source": "file",
                    "label": label,
                    "stored_as": store.write_file(pid, label, (SAMPLE / fixture).read_bytes()),
                    "size": 0,
                },
            )
            chunks, skipped = ingest.parse_input(pid, record)
            assert not skipped, f"{label}: {skipped}"
            assert len(chunks) == count, f"{label}: got {len(chunks)}, expected {count}"

        # an image cannot be split, so it becomes exactly one chunk carrying the file
        image = store.add_input(
            pid,
            {
                "kind": "screenshot",
                "source": "file",
                "label": "sheet.png",
                "stored_as": store.write_file(
                    pid, "sheet.png", (SAMPLE / "screenshot_dispatch_sheet.png").read_bytes()
                ),
                "size": 0,
            },
        )
        chunks, skipped = ingest.parse_input(pid, image)
        assert not skipped and len(chunks) == 1, (skipped, chunks)
        assert chunks[0].locator == "image" and chunks[0].media, chunks[0]

        # something we genuinely have no parser for must still say so
        other = store.add_input(
            pid,
            {
                "kind": "document",
                "source": "file",
                "label": "contract.docx",
                "stored_as": store.write_file(pid, "contract.docx", b"PK\x03\x04fake"),
                "size": 0,
            },
        )
        _, skipped = ingest.parse_input(pid, other)
        assert skipped, "unsupported formats must skip loudly"

        print("routing        5 inputs  content beats filename; .docx skipped honestly")
    finally:
        shutil.rmtree(store.project_dir(pid), ignore_errors=True)


if __name__ == "__main__":
    check_transcript()
    check_whatsapp()
    check_pdf()
    check_plain()
    check_ids_unique()
    check_routing()
    print("\nall parsers ok")
