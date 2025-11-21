# Labeller Smoke Test Plan

- **Test Name:** `labeller-smoke`
- **Goal:** Verify that core labeling workflows (project setup → dataset prep → annotation) function end-to-end.
- **Pre-requisites:** `./run-sam-3-labeller.sh` succeeds, backend running on `127.0.0.1:8000`, frontend dev server on `127.0.0.1:5173`.
- **Screenshot Folder:** `labeler_app/screenshots/labeller-smoke/`

| Step | Description | Actions | Expected Result | Screenshot |
| --- | --- | --- | --- | --- |
| 01 | Projects dashboard loads | Visit `http://127.0.0.1:5173/projects` after servers start | Project list + creation form visible | `01-projects-dashboard.png` |
| 02 | Create project | Fill “Labeller Smoke Test” + description, submit | New project card appears | `02-create-project.png` |
| 03 | Configure schema | Inside project: create dataset “Smoke Dataset” and label class “Box” | Dataset card + class chips visible | `03-configure-schema.png` |
| 04 | Dataset gallery | Open dataset, upload `assets/images/test_image.jpg`, refresh | Image card rendered in grid | `04-dataset-gallery.png` |
| 05 | Labeler annotation | Open labeler, select class, draw bbox on sample image | Annotation list shows new bbox overlay | `05-labeler-annotation.png` |

