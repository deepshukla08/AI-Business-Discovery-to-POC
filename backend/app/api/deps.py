from fastapi import HTTPException

from app.storage import store


def get_project_or_404(pid: str) -> dict:
    """Route dependency: resolves {pid} from the path or fails the request."""
    project = store.load(pid)
    if not project:
        raise HTTPException(404, "project not found")
    return project
