## Labeler Backend

FastAPI + SQLModel service powering the Roboflow-like labeling experience.

### Setup
```bash
cd /home/aiserver/LABS/SAM3/sam3-installation-notes-abdshomad/labeler_app/backend
uv sync
```

### Run
```bash
cd /home/aiserver/LABS/SAM3/sam3-installation-notes-abdshomad
uv run uvicorn labeler_app.backend.app.main:app --reload
```

Visit http://127.0.0.1:8000/docs for interactive API docs.

### Storage
Artifacts persist under `labeler_app/storage`, with uploads inside project/dataset folders and COCO exports under `exports/`.

