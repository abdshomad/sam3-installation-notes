from slugify import slugify
from sqlmodel import Session, select


def unique_slug(session: Session, model, value: str, field_name: str = "slug") -> str:
    base = slugify(value) or "project"
    candidate = base
    counter = 1

    while session.exec(select(model).where(getattr(model, field_name) == candidate)).first():
        counter += 1
        candidate = f"{base}-{counter}"
    return candidate

