"""End-to-end check: upload files, stream a run, get cited findings back.

    python test_run.py

Costs one Gemini call. Exercises the exact path the browser takes.
"""

import json
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.storage import store

SAMPLE = Path(__file__).resolve().parent.parent / "samples" / "zippo"
client = TestClient(app)


def main() -> None:
    project = client.post("/api/projects", json={"name": "Run check", "client": "Zippo"}).json()
    pid = project["id"]

    try:
        transcript = (SAMPLE / "call_1_kickoff.txt").read_bytes()
        screenshot = (SAMPLE / "screenshot_dispatch_sheet.png").read_bytes()
        client.post(
            f"/api/projects/{pid}/files",
            files=[
                ("files", ("call_1_kickoff.txt", transcript, "text/plain")),
                ("files", ("screenshot_dispatch_sheet.png", screenshot, "image/png")),
            ],
        )
        client.post(
            f"/api/projects/{pid}/text",
            json={"label": "Consultant notes", "content": "Ravi is the single point of failure.\n\nBilling is a separate system."},
        )

        events = []
        with client.stream("POST", f"/api/projects/{pid}/run") as response:
            assert response.status_code == 200, response.status_code
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    events.append(event)
                    if event["event"] != "done":
                        print(f"  › {event}")

        kinds = [e["event"] for e in events]
        assert kinds[0] == "start", kinds
        # the run stops at ask_client and hands back the open questions — it does not
        # design anything until a human has answered or waved it through
        assert kinds[-1] == "awaiting", kinds[-1]

        # fan-out: one extractor per source, each reporting separately
        node_events = [e for e in events if e["event"] == "node_done"]
        assert len(node_events) == 3, f"expected one node per source: {node_events}"
        assert {e["source"] for e in node_events} == {
            "call_1_kickoff.txt",
            "Consultant notes",
            "screenshot_dispatch_sheet.png",
        }, node_events
        assert node_events[-1]["total"] == sum(e["findings"] for e in node_events)

        parsed = [e for e in events if e["event"] == "parsed"]
        assert len(parsed) == 3, f"transcript + notes + screenshot should parse: {parsed}"
        assert any(e["chunks"] > 100 for e in parsed), "transcript parsed too small"
        assert not [e for e in events if e["event"] == "skipped"], "nothing should skip now"

        done = events[-1]
        chunk_ids = {c["id"] for c in done["chunks"]}
        assert len(chunk_ids) == len(done["chunks"]), "chunk ids collided across sources"
        assert done["findings"], "no findings"
        assert all(
            cite in chunk_ids for f in done["findings"] for cite in f["cites"]
        ), "a finding cites a chunk that does not exist"

        # every finding must be stamped with the source it actually came from —
        # before the fan-out they were all labelled with whichever file parsed first
        chunk_source = {c["id"]: c["source_id"] for c in done["chunks"]}
        for finding in done["findings"]:
            for cite in finding["cites"]:
                assert chunk_source[cite] == finding["source_id"], (
                    f"{finding['source_id']} claims {cite}, which belongs to {chunk_source[cite]}"
                )

        # trap 4: this evidence exists ONLY in the screenshot. If vision contributes
        # nothing the text sources cannot already give us, it is not earning its place.
        from_image = [
            f for f in done["findings"] if f["source_id"] == "screenshot_dispatch_sheet.png"
        ]
        assert from_image, "the screenshot produced nothing"
        seen = " ".join(f["text"].lower() for f in from_image)
        assert "driver2" in seen or "second driver" in seen or "two driver" in seen, seen
        assert any(word in seen for word in ("status", "spelling", "inconsistent")), seen

        # the image is served back so the citation can show it
        image_chunk = next(c for c in done["chunks"] if c.get("media"))
        assert client.get(f"/api/projects/{pid}/files/{image_chunk['media']}").status_code == 200
        assert client.get(f"/api/projects/{pid}/files/../project.json").status_code in (400, 404)

        # the partial run survives a page refresh, and says it is still waiting
        saved = client.get(f"/api/projects/{pid}/run").json()
        assert len(saved["findings"]) == len(done["findings"])
        assert saved["awaiting"] is True, "the UI would not know to show the questions"
        assert saved["brief"], "the brief should be readable while paused"
        assert not saved["redesign"], "nothing may be designed before the human answers"

        print(
            f"run check passed — {len(done['chunks'])} chunks, "
            f"{len(done['findings'])} findings, paused on {len(done['gaps'])} questions"
        )
    finally:
        shutil.rmtree(store.project_dir(pid), ignore_errors=True)


if __name__ == "__main__":
    main()
