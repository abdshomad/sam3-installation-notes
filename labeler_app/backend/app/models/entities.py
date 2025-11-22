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
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class Project(ProjectBase, TimestampMixin, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=220)

class ProjectRead(ProjectBase):
    id: int
    slug: str
    confidence_threshold: float
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
    presence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    concept_text: Optional[str] = Field(default=None, max_length=500)
    exemplar_crop: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)
    is_ai_generated: bool = Field(default=False)


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
    presence_score: Optional[float]
    concept_text: Optional[str]
    exemplar_crop: Optional[Dict[str, Any]]
    is_ai_generated: bool
    created_at: datetime
    updated_at: datetime


class AnnotationCreate(AnnotationBase):
    image_id: int
    label_class_id: int
    author: Optional[str] = None
    presence_score: Optional[float] = None
    concept_text: Optional[str] = None
    exemplar_crop: Optional[Dict[str, Any]] = None
    is_ai_generated: bool = False


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


class VideoAssetBase(SQLModel):
    original_filename: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None


class VideoAsset(VideoAssetBase, TimestampMixin, table=True):
    __tablename__ = "video_assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id", index=True)
    file_path: str
    hls_path: Optional[str] = None
    status: str = Field(default="processing")
    asset_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)


class VideoAssetRead(VideoAssetBase):
    id: int
    dataset_id: int
    file_path: str
    hls_path: Optional[str]
    status: str
    asset_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class MaskletBase(SQLModel):
    obj_id: int
    video_id: int
    frame_start: int
    frame_end: int


class Masklet(MaskletBase, TimestampMixin, table=True):
    __tablename__ = "masklets"

    id: Optional[int] = Field(default=None, primary_key=True)
    memory_bank_snapshot: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)
    annotations: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)


class MaskletRead(MaskletBase):
    id: int
    memory_bank_snapshot: Optional[Dict[str, Any]]
    annotations: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=200)
    is_active: bool = Field(default=True)


class User(UserBase, TimestampMixin, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: Optional[str] = Field(default=None, max_length=255)
    role: str = Field(default="labeler", max_length=50)  # admin, reviewer, labeler


class UserRead(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProjectMemberBase(SQLModel):
    role: str = Field(default="labeler", max_length=50)  # admin, reviewer, labeler


class ProjectMember(ProjectMemberBase, TimestampMixin, table=True):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_user"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)


class ProjectMemberRead(ProjectMemberBase):
    id: int
    project_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

