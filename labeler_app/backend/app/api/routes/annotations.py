from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.entities import Annotation, AnnotationCreate, AnnotationRead, ImageAsset, LabelClass

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.get("/", response_model=list[AnnotationRead])
def list_annotations(image_id: int, session: Session = Depends(get_db)) -> list[Annotation]:
    return session.exec(select(Annotation).where(Annotation.image_id == image_id).order_by(Annotation.created_at)).all()


@router.post("/", response_model=AnnotationRead, status_code=status.HTTP_201_CREATED)
def create_annotation(payload: AnnotationCreate, session: Session = Depends(get_db)) -> Annotation:
    image = session.get(ImageAsset, payload.image_id)
    label_class = session.get(LabelClass, payload.label_class_id)
    if not image or not label_class:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image or label class")

    annotation = Annotation(**payload.model_dump())
    session.add(annotation)
    session.commit()
    session.refresh(annotation)
    return annotation


@router.delete("/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_annotation(annotation_id: int, session: Session = Depends(get_db)) -> None:
    annotation = session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    session.delete(annotation)
    session.commit()

