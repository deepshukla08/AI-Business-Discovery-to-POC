"""Collecting the client's mess: uploaded files, pasted notes, a website reference."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import get_project_or_404
from app.schemas.project import ClientInput, Project, TextInput, UrlInput
from app.storage import store

router = APIRouter(prefix="/api/projects/{pid}", tags=["inputs"])


@router.post("/files", response_model=list[ClientInput])
async def upload_files(
    pid: str,
    files: list[UploadFile] = File(...),
    project: dict = Depends(get_project_or_404),
):
    added = []
    for upload in files:
        name = upload.filename or "unnamed"
        body = await upload.read()
        added.append(
            store.add_input(
                pid,
                {
                    "kind": store.guess_kind(name),
                    "source": "file",
                    "label": name,
                    "stored_as": store.write_file(pid, name, body),
                    "size": len(body),
                },
            )
        )
    return added


@router.post("/text", response_model=ClientInput)
def add_text(pid: str, body: TextInput, project: dict = Depends(get_project_or_404)):
    encoded = body.content.encode()
    return store.add_input(
        pid,
        {
            "kind": "notes",
            "source": "paste",
            "label": body.label or "Pasted notes",
            "stored_as": store.write_file(pid, "pasted.txt", encoded),
            "size": len(encoded),
        },
    )


@router.post("/url", response_model=ClientInput)
def add_url(pid: str, body: UrlInput, project: dict = Depends(get_project_or_404)):
    return store.add_input(
        pid,
        {
            "kind": "website",
            "source": "url",
            "label": body.url,
            "url": body.url,
            "size": 0,
        },
    )


@router.delete("/inputs/{input_id}", response_model=Project)
def delete_input(pid: str, input_id: str, project: dict = Depends(get_project_or_404)):
    return store.remove_input(pid, input_id)


@router.get("/files/{stored_as}")
def get_file(pid: str, stored_as: str, project: dict = Depends(get_project_or_404)):
    """Serves an uploaded file — the UI uses it to show a screenshot behind a citation."""
    if "/" in stored_as or "\\" in stored_as or ".." in stored_as:
        raise HTTPException(400, "bad filename")
    path = store.files_dir(pid) / stored_as
    if not path.exists():
        raise HTTPException(404, "file not found")
    return FileResponse(path)
