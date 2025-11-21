from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


engine = create_engine(settings.database_url, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir.mkdir(parents=True, exist_ok=True)
    settings.tmp_dir.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
    with Session(engine) as session:
        yield session

