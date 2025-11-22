from collections.abc import Generator
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.entities import User, ProjectMember

security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    with get_session() as session:
        yield session


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.

    For now, returns None (no authentication required).
    In production, this would decode JWT and return User.
    """
    # TODO: Implement JWT token validation
    # For now, return None (anonymous access)
    return None


def require_role(required_role: str):
    """
    Dependency to require a specific role.

    Usage:
        @router.get("/admin")
        def admin_endpoint(user: User = Depends(require_role("admin"))):
            ...
    """
    def role_checker(
        user: Optional[User] = Depends(get_current_user),
    ) -> User:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role",
            )
        return user
    return role_checker


def require_project_member(min_role: str = "labeler"):
    """
    Dependency to require project membership with minimum role.

    Usage:
        @router.get("/projects/{project_id}/data")
        def get_data(
            project_id: int,
            member: ProjectMember = Depends(require_project_member("reviewer")),
        ):
            ...
    """
    def member_checker(
        project_id: int,
        user: Optional[User] = Depends(get_current_user),
        session: Session = Depends(get_db),
    ) -> ProjectMember:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        # Check if user is project member
        member = session.exec(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user.id,
            )
        ).first()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this project",
            )

        # Check role hierarchy: admin > reviewer > labeler
        role_hierarchy = {"admin": 3, "reviewer": 2, "labeler": 1}
        if role_hierarchy.get(member.role, 0) < role_hierarchy.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {min_role} role or higher",
            )

        return member
    return member_checker
