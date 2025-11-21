from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.entities import LabelClass, LabelClassBase, LabelClassRead, Project, ProjectBase, ProjectRead
from app.services.slugger import unique_slug

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectRead])
def list_projects(session: Session = Depends(get_db)) -> list[Project]:
    return session.exec(select(Project).order_by(Project.created_at.desc())).all()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectBase, session: Session = Depends(get_db)) -> Project:
    slug = unique_slug(session, Project, payload.name, field_name="slug")
    project = Project(name=payload.name, description=payload.description, slug=slug)
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: Session = Depends(get_db)) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/{project_id}/classes", response_model=LabelClassRead, status_code=status.HTTP_201_CREATED)
def create_label_class(
    project_id: int, payload: LabelClassBase, session: Session = Depends(get_db)
) -> LabelClass:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    existing = session.exec(
        select(LabelClass).where(LabelClass.project_id == project_id, LabelClass.name == payload.name)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Class already exists")

    order_index = (
        session.exec(select(LabelClass).where(LabelClass.project_id == project_id).order_by(LabelClass.order_index.desc())).first()
    )
    next_index = (order_index.order_index + 1) if order_index else 0
    label_class = LabelClass(project_id=project_id, order_index=next_index, **payload.model_dump())
    session.add(label_class)
    session.commit()
    session.refresh(label_class)
    return label_class


@router.get("/{project_id}/classes", response_model=list[LabelClassRead])
def list_label_classes(project_id: int, session: Session = Depends(get_db)) -> list[LabelClass]:
    return session.exec(select(LabelClass).where(LabelClass.project_id == project_id).order_by(LabelClass.order_index)).all()

