from fastapi import APIRouter, Depends

from app.api.deps import get_project_or_404
from app.schemas.project import NewProject, Project
from app.storage import store

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects():
    return store.list_all()


@router.post("", response_model=Project)
def create_project(body: NewProject):
    return store.create(body.name, body.client)


@router.get("/{pid}", response_model=Project)
def get_project(project: dict = Depends(get_project_or_404)):
    return project
