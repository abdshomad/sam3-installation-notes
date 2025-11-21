"""API routes for user management and authentication."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, select

from app.api.deps import get_db, get_current_user, require_role
from app.models.entities import User, UserRead

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    """Request model for creating a user."""

    email: EmailStr
    name: str = Field(max_length=200)
    password: str = Field(min_length=8)
    role: str = Field(default="labeler", pattern="^(admin|reviewer|labeler)$")


class UserUpdate(BaseModel):
    """Request model for updating a user."""

    name: Optional[str] = Field(default=None, max_length=200)
    role: Optional[str] = Field(default=None, pattern="^(admin|reviewer|labeler)$")
    is_active: Optional[bool] = None


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_role("admin")),
    session: Session = Depends(get_db),
) -> User:
    """
    Create a new user (admin only).

    In production, password should be hashed using passlib.
    """
    # Check if user already exists
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists"
        )

    # TODO: Hash password using passlib
    # For now, store plain text (NOT for production!)
    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=payload.password,  # Should be hashed
        role=payload.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
def get_current_user_info(
    current_user: Optional[User] = Depends(get_current_user),
) -> User:
    """Get current authenticated user information."""
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return current_user


@router.get("/", response_model=list[UserRead])
def list_users(
    current_user: User = Depends(require_role("admin")),
    session: Session = Depends(get_db),
) -> list[User]:
    """List all users (admin only)."""
    return session.exec(select(User).order_by(User.created_at.desc())).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    session: Session = Depends(get_db),
) -> User:
    """Get user by ID (admin only)."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(require_role("admin")),
    session: Session = Depends(get_db),
) -> User:
    """Update user (admin only)."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

