from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ProjectBase(SQLModel):
    name: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)


class Project(ProjectBase, TimestampMixin, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=220)

class ProjectRead(ProjectBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime


class LabelClassBase(SQLModel):
    name: str
    color: str = Field(default="#ff5f45")
    hotkey: Optional[str] = None


class LabelClass(LabelClassBase, TimestampMixin, table=True):
    __tablename__ = "label_classes"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_class_project_name"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    order_index: int = Field(default=0)

class LabelClassRead(LabelClassBase):
    id: int
    project_id: int
    order_index: int


class DatasetBase(SQLModel):
    name: str
    description: Optional[str] = None


class Dataset(DatasetBase, TimestampMixin, table=True):
    __tablename__ = "datasets"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, max_length=220)
    project_id: int = Field(foreign_key="projects.id")
    status: str = Field(default="ready", index=True)

class DatasetRead(DatasetBase):
    id: int
    slug: str
    project_id: int
    status: str
    created_at: datetime
    updated_at: datetime


class ImageAssetBase(SQLModel):
    original_filename: str
    width: Optional[int] = None
    height: Optional[int] = None


class ImageAsset(ImageAssetBase, TimestampMixin, table=True):
    __tablename__ = "image_assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id", index=True)
    file_path: str
    status: str = Field(default="unlabeled")

class ImageAssetRead(ImageAssetBase):
    id: int
    dataset_id: int
    file_path: str
    status: str
    created_at: datetime
    updated_at: datetime


class AnnotationBase(SQLModel):
    annotation_type: str = Field(default="bbox")
    geometry: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
    attributes: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)


class Annotation(AnnotationBase, TimestampMixin, table=True):
    __tablename__ = "annotations"

    id: Optional[int] = Field(default=None, primary_key=True)
    image_id: int = Field(foreign_key="image_assets.id")
    label_class_id: int = Field(foreign_key="label_classes.id")
    author: Optional[str] = Field(default=None, max_length=120)

class AnnotationRead(AnnotationBase):
    id: int
    image_id: int
    label_class_id: int
    author: Optional[str]
    created_at: datetime
    updated_at: datetime


class AnnotationCreate(AnnotationBase):
    image_id: int
    label_class_id: int
    author: Optional[str] = None


class TaskBase(SQLModel):
    status: str = Field(default="todo")
    assignee: Optional[str] = Field(default=None, max_length=120)
    qa_status: Optional[str] = None


class Task(TaskBase, TimestampMixin, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    image_id: int = Field(foreign_key="image_assets.id", unique=True)
    priority: int = Field(default=0)


class TaskRead(TaskBase):
    id: int
    image_id: int
    priority: int
    created_at: datetime
    updated_at: datetime


class TaskUpdate(SQLModel):
    status: Optional[str] = None
    assignee: Optional[str] = None
    qa_status: Optional[str] = None

