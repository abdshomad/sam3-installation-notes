from fastapi import APIRouter

from app.api.routes import (
    annotations,
    batch,
    concepts,
    consensus,
    datasets,
    export,
    images,
    project_members,
    projects,
    tasks,
    users,
    video_tracking,
    videos,
)


api_router = APIRouter()
api_router.include_router(projects.router)
api_router.include_router(datasets.router)
api_router.include_router(images.router)
api_router.include_router(annotations.router)
api_router.include_router(tasks.router)
api_router.include_router(export.router)
api_router.include_router(concepts.router)
api_router.include_router(batch.router)
api_router.include_router(videos.router)
api_router.include_router(video_tracking.router)
api_router.include_router(users.router)
api_router.include_router(project_members.router)
api_router.include_router(consensus.router)

