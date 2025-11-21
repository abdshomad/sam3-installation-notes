from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.entities import Dataset, DatasetBase, DatasetRead, Project
from app.services.slugger import unique_slug

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetBase, project_id: int, session: Session = Depends(get_db)) -> Dataset:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    slug = unique_slug(session, Dataset, payload.name)
    dataset = Dataset(
        name=payload.name,
        description=payload.description,
        slug=slug,
        project_id=project_id,
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset


@router.get("/", response_model=list[DatasetRead])
def list_datasets(project_id: int | None = None, session: Session = Depends(get_db)) -> list[Dataset]:
    query = select(Dataset)
    if project_id:
        query = query.where(Dataset.project_id == project_id)
    return session.exec(query.order_by(Dataset.created_at.desc())).all()


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, session: Session = Depends(get_db)) -> Dataset:
    dataset = session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset

