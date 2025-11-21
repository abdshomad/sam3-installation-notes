## Labeler Web App

End-to-end labeling tool inspired by Roboflow.

### Stack
- Backend: FastAPI + SQLModel (`labeler_app/backend`)
- Frontend: Vite + React + TypeScript (`labeler_app/frontend`)
- Storage: local disk under `labeler_app/storage`

### Backend
```bash
cd /home/aiserver/LABS/SAM3/sam3-installation-notes-abdshomad/labeler_app/backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd /home/aiserver/LABS/SAM3/sam3-installation-notes-abdshomad/labeler_app/frontend
npm install
npm run dev -- --host
```

Set `VITE_API_BASE_URL` (defaults to `http://127.0.0.1:8000/api`) to point at the backend.

### Features
- Project + dataset CRUD
- Label schema management with colors/hotkeys
- Image uploads with previews
- Bounding-box annotation workspace with class picker, image navigation, annotation list
- COCO export endpoints (`GET /api/export/{project_id}/coco`)

