## Image Labeling Web App Plan

### Vision
- Deliver a browser-based annotation experience comparable to Roboflow for bounding boxes, polygons, and segmentation masks.
- Support dataset/project management, versioned label schemas, task assignment, and export formats (COCO, YOLO, Segments).
- Integrate with SAM3 inference helpers to pre-fill masks or suggestions in later phases.

### Architecture
- **Frontend**: Vite + React + TypeScript, Zustand for client state, React Query for data fetching, Konva/Canvas for drawing tools, Tailwind for styling. Deployed as static assets served by FastAPI.
- **Backend**: FastAPI + SQLModel (SQLite persistence). Provides REST + WebSocket for collaborative locking and live updates. Media stored on disk under `labeler_app/storage`, referenced via signed URLs.
- **Worker tier (future)**: Background tasks (RQ/Celery) for pre-labeling with SAM3, bulk import/export, QA automation.
- **Storage layout**
  - `/labeler_app/storage/uploads/<project_id>/<image_id>.jpg`
  - `/labeler_app/storage/exports/<project_id>/<timestamp>.zip`

### Core Data Model
| Entity | Fields |
| --- | --- |
| Project | id, name, description, created_at, updated_at |
| LabelClass | id, project_id, name, color, hotkey |
| Dataset | id, project_id, name, status |
| ImageAsset | id, dataset_id, path, width, height, metadata |
| Annotation | id, image_id, label_class_id, type, geometry JSON, attributes, created_by |
| Task | id, image_id, assignee, status, qa_status |
| Comment | id, image_id, user_id, body |

### API Surface (initial)
- `POST /projects`, `GET /projects`, `GET /projects/{id}`
- `POST /projects/{id}/classes`
- `POST /datasets`, `POST /datasets/{id}/upload` (multipart)
- `GET /images?dataset_id=`
- `POST /annotations`, `GET /annotations?image_id=`
- `PATCH /tasks/{id}` for workflow
- `GET /export/{project_id}?format=coco|yolo`
- `WebSocket /ws/projects/{id}` for task claiming + annotation streaming

### Frontend Views
- **Dashboard**: list projects/datasets, progress metrics.
- **Label Schema Builder**: manage classes/colors/hotkeys.
- **Dataset Manager**: drag-drop uploads, preview images, processing status.
- **Labeling Workspace**:
  - Toolbar: select/pan/box/polygon/mask/eraser, zoom, snap, undo/redo.
  - Sidebar: class picker, attributes, history, comments.
  - Timeline for multi-frame/video (stretch goal).
- **Review/QA**: filter tasks by status, accept/reject, bulk actions.

### Iteration Backlog
1. MVP (current sprint)
   - CRUD for projects/datasets/images/classes
   - Image upload + storage
   - Labeling workspace with bounding boxes + polygons
   - Task assignment + status
   - Export to COCO JSON
2. Assisted labeling
   - Hook SAM3 inference for mask suggestions
   - Smart polygon auto-complete
3. Collaboration & QA
   - Comments, activity log, conflict detection
   - Role-based access (admin, labeler, reviewer)
4. Advanced exports/integrations
   - YOLO, Pascal VOC, Roboflow import/export parity
   - Webhooks + API tokens

### Tech Debt / Risks
- Need to scope binary storage (local disk vs S3) before scaling.
- Annotation diff/merge logic for concurrent edits not yet defined.
- Performance tuning for large polygon/mask data pending (might require WebGL).

### Next Steps
1. Scaffold backend FastAPI app under `labeler_app/backend`.
2. Define SQLModel schemas + Alembic migrations.
3. Build REST endpoints + tests.
4. Scaffold Vite React frontend, implement workspace UI.

