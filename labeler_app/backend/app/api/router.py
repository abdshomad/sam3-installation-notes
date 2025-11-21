from fastapi import APIRouter

from app.api.routes import annotations, datasets, export, images, projects, tasks


api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(datasets.router)
api_router.include_router(images.router)
api_router.include_router(annotations.router)
api_router.include_router(tasks.router)
api_router.include_router(export.router)

