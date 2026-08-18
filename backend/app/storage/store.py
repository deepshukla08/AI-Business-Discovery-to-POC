"""Project storage: one folder per project, project.json + files/ inside it.

ponytail: JSON on disk, no database. A discovery POC has a handful of projects and
never queries across them. Swap to SQLite the day that stops being true.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import DATA_DIR

# extension -> the kind of client input it represents (drives UI badges and, later, the parser)
KINDS = {
    ".txt": "transcript",
    ".vtt": "transcript",
    ".md": "document",
    ".pdf": "document",
    ".docx": "document",
    ".png": "screenshot",
    ".jpg": "screenshot",
    ".jpeg": "screenshot",
    ".webp": "screenshot",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(length: int = 8) -> str:
    return uuid.uuid4().hex[:length]


def guess_kind(filename: str) -> str:
    name = filename.lower()
    ext = Path(name).suffix
    if ext in (".txt", ".vtt") and "whatsapp" in name:
        return "whatsapp"
    return KINDS.get(ext, "document")


def project_dir(pid: str) -> Path:
    return DATA_DIR / pid


def files_dir(pid: str) -> Path:
    return project_dir(pid) / "files"


def save(project: dict) -> dict:
    path = project_dir(project["id"]) / "project.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(project, indent=2), encoding="utf-8")
    return project


def load(pid: str) -> dict | None:
    path = project_dir(pid) / "project.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def create(name: str, client: str = "") -> dict:
    pid = new_id(12)
    files_dir(pid).mkdir(parents=True, exist_ok=True)
    return save(
        {
            "id": pid,
            "name": name,
            "client": client,
            "created_at": now(),
            "inputs": [],
            "status": "collecting",
        }
    )


def list_all() -> list[dict]:
    projects = [json.loads(p.read_text(encoding="utf-8")) for p in DATA_DIR.glob("*/project.json")]
    return sorted(projects, key=lambda p: p["created_at"], reverse=True)


def write_file(pid: str, filename: str, body: bytes) -> str:
    """Store bytes under a unique name so two files called notes.txt can coexist."""
    stored_as = f"{new_id()}_{filename}"
    (files_dir(pid) / stored_as).write_bytes(body)
    return stored_as


def prototype_path(pid: str) -> Path:
    return project_dir(pid) / "prototype.html"


def save_prototype(pid: str, html: str) -> Path:
    path = prototype_path(pid)
    path.write_text(html, encoding="utf-8")
    return path


def save_run(pid: str, result: dict) -> dict:
    (project_dir(pid) / "run.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    project = load(pid)
    project["status"] = "analysed"
    save(project)
    return result


def load_run(pid: str) -> dict | None:
    path = project_dir(pid) / "run.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def add_input(pid: str, record: dict) -> dict:
    project = load(pid)
    record["id"] = new_id()
    record["added_at"] = now()
    project["inputs"].append(record)
    save(project)
    return record


def remove_input(pid: str, input_id: str) -> dict:
    project = load(pid)
    for record in project["inputs"]:
        if record["id"] == input_id and record.get("stored_as"):
            (files_dir(pid) / record["stored_as"]).unlink(missing_ok=True)
    project["inputs"] = [i for i in project["inputs"] if i["id"] != input_id]
    return save(project)
