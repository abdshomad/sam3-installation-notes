"""API routes for project member management."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import get_db, require_project_member
from app.models.entities import Project, ProjectMember, ProjectMemberRead, User

router = APIRouter(prefix="/projects/{project_id}/members", tags=["project-members"])


class ProjectMemberCreate(BaseModel):
    """Request model for adding a project member."""

    user_id: int
    role: str = Field(default="labeler", pattern="^(admin|reviewer|labeler)$")


class ProjectMemberUpdate(BaseModel):
    """Request model for updating a project member."""

    role: Optional[str] = Field(default=None, pattern="^(admin|reviewer|labeler)$")


@router.post("/", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED)
def add_project_member(
    project_id: int,
    payload: ProjectMemberCreate,
    member: ProjectMember = Depends(require_project_member(project_id, "admin")),
    session: Session = Depends(get_db),
) -> ProjectMember:
    """
    Add a user to a project (admin only).

    Requires admin role in the project.
    """
    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # Verify user exists
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if already a member
    existing = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.user_id,
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User is already a project member"
        )

    # Create project member
    project_member = ProjectMember(
        project_id=project_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    session.add(project_member)
    session.commit()
    session.refresh(project_member)
    return project_member


@router.get("/", response_model=list[ProjectMemberRead])
def list_project_members(
    project_id: int,
    member: ProjectMember = Depends(require_project_member(project_id, "labeler")),
    session: Session = Depends(get_db),
) -> list[ProjectMember]:
    """List all members of a project."""
    return session.exec(
        select(ProjectMember)
        .where(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.created_at)
    ).all()


@router.get("/{member_id}", response_model=ProjectMemberRead)
def get_project_member(
    project_id: int,
    member_id: int,
    member: ProjectMember = Depends(require_project_member(project_id, "labeler")),
    session: Session = Depends(get_db),
) -> ProjectMember:
    """Get project member by ID."""
    project_member = session.get(ProjectMember, member_id)
    if not project_member or project_member.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found"
        )
    return project_member


@router.patch("/{member_id}", response_model=ProjectMemberRead)
def update_project_member(
    project_id: int,
    member_id: int,
    payload: ProjectMemberUpdate,
    member: ProjectMember = Depends(require_project_member(project_id, "admin")),
    session: Session = Depends(get_db),
) -> ProjectMember:
    """Update project member role (admin only)."""
    project_member = session.get(ProjectMember, member_id)
    if not project_member or project_member.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found"
        )

    if payload.role is not None:
        project_member.role = payload.role

    session.add(project_member)
    session.commit()
    session.refresh(project_member)
    return project_member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project_member(
    project_id: int,
    member_id: int,
    member: ProjectMember = Depends(require_project_member(project_id, "admin")),
    session: Session = Depends(get_db),
) -> None:
    """Remove a user from a project (admin only)."""
    project_member = session.get(ProjectMember, member_id)
    if not project_member or project_member.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found"
        )

    session.delete(project_member)
    session.commit()

