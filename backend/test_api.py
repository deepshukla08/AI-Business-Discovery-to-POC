"""Runnable check for the inputs API: python test_api.py"""

import shutil

from fastapi.testclient import TestClient

from app.main import app
from app.storage import store

client = TestClient(app)


def main() -> None:
    project = client.post("/api/projects", json={"name": "Check", "client": "Acme"}).json()
    pid = project["id"]
    try:
        uploaded = client.post(
            f"/api/projects/{pid}/files",
            files=[
                ("files", ("whatsapp_chat.txt", b"[10/03/24, 21:14] Ravi: hi", "text/plain")),
                ("files", ("process.pdf", b"%PDF-fake", "application/pdf")),
                ("files", ("screen.png", b"\x89PNG-fake", "image/png")),
            ],
        ).json()
        assert [f["kind"] for f in uploaded] == ["whatsapp", "document", "screenshot"], uploaded

        client.post(f"/api/projects/{pid}/text", json={"label": "Call notes", "content": "hello"})
        client.post(f"/api/projects/{pid}/url", json={"url": "https://example.com"})

        full = client.get(f"/api/projects/{pid}").json()
        assert len(full["inputs"]) == 5, full
        assert {i["kind"] for i in full["inputs"]} == {
            "whatsapp",
            "document",
            "screenshot",
            "notes",
            "website",
        }

        stored = store.files_dir(pid) / uploaded[0]["stored_as"]
        assert stored.read_bytes().startswith(b"[10/03/24"), "uploaded bytes must hit disk"

        after = client.delete(f"/api/projects/{pid}/inputs/{uploaded[0]['id']}").json()
        assert len(after["inputs"]) == 4
        assert not stored.exists(), "deleting a record must delete its file"

        assert client.get("/api/projects/does-not-exist").status_code == 404
        print("api check passed")
    finally:
        shutil.rmtree(store.project_dir(pid), ignore_errors=True)


if __name__ == "__main__":
    main()
