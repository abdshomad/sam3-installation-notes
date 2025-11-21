from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db

init_db()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/model")
def health_model() -> dict[str, str | bool]:
    """Check if SAM3 model is loaded and ready."""
    from app.services.sam3_model_manager import get_sam3_model_manager

    manager = get_sam3_model_manager()
    return {
        "status": "ready" if manager.is_ready() else "loading",
        "device": manager.get_device(),
        "loaded": manager.is_ready(),
    }

