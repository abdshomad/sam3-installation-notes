from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.entities import ImageAsset, Task, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=list[TaskRead])
def list_tasks(status_filter: str | None = None, session: Session = Depends(get_db)) -> list[Task]:
    query = select(Task)
    if status_filter:
        query = query.where(Task.status == status_filter)
    return session.exec(query.order_by(Task.priority.desc(), Task.created_at)).all()


@router.post("/{image_id}", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(image_id: int, session: Session = Depends(get_db)) -> Task:
    image = session.get(ImageAsset, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    task = session.exec(select(Task).where(Task.image_id == image_id)).first()
    if task:
        return task

    task = Task(image_id=image_id)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, session: Session = Depends(get_db)) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

