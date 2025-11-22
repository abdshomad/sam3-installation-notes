# Test Plan: Integration & End-to-End Tests

## Overview

This document defines the test plan for integration and end-to-end tests that span multiple phases of the SAM 3 Labeling App. These tests verify complete workflows from frontend to backend, ensuring all components work together correctly.

**Target Coverage**: All critical user journeys 100%  
**Test Type**: Integration + End-to-End (E2E)

## Test Categories

### 1. Complete Image Annotation Workflow

#### Test Suite: `tests/e2e/test_image_annotation_workflow.py` or `tests/e2e/image-annotation.spec.ts`

**Test Scenario**: User annotates images using concept-based prompting

**Test Cases**:

1. **Text Prompt Workflow**
   - ✅ User logs in (when auth implemented)
   - ✅ User navigates to dataset
   - ✅ User selects image
   - ✅ User enters text prompt in Concept Command Bar
   - ✅ System creates annotations with masks
   - ✅ Annotations displayed on canvas
   - ✅ Confidence scores displayed
   - ✅ User can select/deselect annotations
   - ✅ User can delete annotations

2. **Exemplar Prompt Workflow**
   - ✅ User selects image
   - ✅ User clicks "Crop Exemplar" button
   - ✅ User selects crop region on canvas
   - ✅ System creates annotations from exemplar
   - ✅ Annotations displayed on canvas
   - ✅ User can refine annotations

3. **Batch Labeling Workflow**
   - ✅ User opens Batch Labeling Dialog
   - ✅ User enters concept text
   - ✅ User configures threshold and options
   - ✅ User submits batch job
   - ✅ System processes images asynchronously
   - ✅ User monitors job progress
   - ✅ Job completes and annotations created
   - ✅ User navigates through images to verify annotations

4. **Export Workflow**
   - ✅ User annotates multiple images
   - ✅ User navigates to export page
   - ✅ User selects export format (COCO, SA-Co, YOLO)
   - ✅ System generates export file
   - ✅ User downloads export file
   - ✅ Export file format validated

**Test Tools**:
- Backend: pytest with FastAPI TestClient + real database
- Frontend: Playwright or Cypress for E2E browser testing

**Test Data**:
- Test project with dataset and images
- Various image types for annotation
- User authentication tokens (when implemented)

---

### 2. Complete Video Annotation Workflow

#### Test Suite: `tests/e2e/test_video_annotation_workflow.py` or `tests/e2e/video-annotation.spec.ts`

**Test Scenario**: User annotates videos using masklet tracking (when frontend implemented)

**Test Cases** (Planned):

1. **Video Upload & Processing**
   - ⏳ User uploads video file
   - ⏳ System processes video (metadata, keyframes, HLS)
   - ⏳ Video asset created in database
   - ⏳ User navigates to video annotation page

2. **Video Tracking Workflow**
   - ⏳ User opens video in annotation interface
   - ⏳ System starts tracking session
   - ⏳ User adds prompt to frame (text/point/box)
   - ⏳ User triggers forward tracking
   - ⏳ System generates masklets frame-by-frame
   - ⏳ Masklets displayed on video timeline
   - ⏳ Masklets displayed on video frames
   - ⏳ User can scrub through frames
   - ⏳ User can navigate to specific frame

3. **Correction Workflow**
   - ⏳ User identifies incorrect masklet at frame
   - ⏳ User corrects mask on canvas
   - ⏳ User selects propagation direction
   - ⏳ System propagates correction
   - ⏳ Masklets updated in timeline
   - ⏳ Masklets updated on video frames

4. **Track Management Workflow**
   - ⏳ User tracks multiple objects
   - ⏳ User selects multiple masklets
   - ⏳ User merges tracks
   - ⏳ User splits track at frame
   - ⏳ Track operations reflected in timeline

5. **Video Export Workflow**
   - ⏳ User completes video annotation
   - ⏳ User exports to COCO-Video format
   - ⏳ User exports to MOT Challenge format
   - ⏳ Export files validated

**Test Tools**:
- Backend: pytest with FastAPI TestClient + real video processing
- Frontend: Playwright/Cypress (when frontend implemented)

**Test Data**:
- Test videos (short, low resolution for fast testing)
- Video with clear objects for tracking

---

### 3. Multi-User Collaboration Workflow

#### Test Suite: `tests/e2e/test_collaboration_workflow.py` or `tests/e2e/collaboration.spec.ts`

**Test Scenario**: Multiple users collaborate on annotation project (when frontend implemented)

**Test Cases** (Planned):

1. **Project Setup Workflow**
   - ⏳ Admin creates project
   - ⏳ Admin adds members (reviewer, labeler)
   - ⏳ Members receive project access
   - ⏳ Members can access project resources

2. **Consensus Annotation Workflow**
   - ⏳ Admin assigns task to multiple labelers
   - ⏳ Labeler 1 annotates image with text prompt
   - ⏳ Labeler 2 annotates same image with text prompt
   - ⏳ System calculates consensus (IoU)
   - ⏳ Reviewer views consensus status
   - ⏳ System auto-merges annotations (if IoU > threshold)
   - ⏳ Reviewer reviews flagged annotations (if IoU < threshold)

3. **Review Workflow**
   - ⏳ Annotations flagged for review
   - ⏳ Reviewer views review queue
   - ⏳ Reviewer opens flagged annotation
   - ⏳ Reviewer compares annotations side-by-side
   - ⏳ Reviewer approves or rejects annotation
   - ⏳ Reviewer adds comments
   - ⏳ Task status updated

4. **RBAC Workflow**
   - ⏳ Labeler tries to access admin-only features (denied)
   - ⏳ Reviewer tries to delete annotations (denied)
   - ⏳ Admin can access all features (allowed)
   - ⏳ Project member can access project (allowed)
   - ⏳ Non-member cannot access project (denied)

**Test Tools**:
- Backend: pytest with multiple test users
- Frontend: Playwright/Cypress with multiple browser contexts (when implemented)

**Test Data**:
- Test project with multiple members
- Test tasks assigned to multiple users
- Multiple annotations for same image

---

### 4. Error Handling & Edge Cases

#### Test Suite: `tests/integration/test_error_handling.py`

**Test Cases**:

1. **API Error Handling**
   - ✅ Test 404 for non-existent resources
   - ✅ Test 403 for unauthorized access
   - ✅ Test 400 for invalid request body
   - ✅ Test 500 for server errors
   - ✅ Test error messages displayed in frontend

2. **Model Error Handling**
   - ✅ Test model loading failure
   - ✅ Test inference failure
   - ✅ Test timeout handling for slow inference
   - ✅ Test error recovery

3. **Database Error Handling**
   - ✅ Test database connection failure
   - ✅ Test transaction rollback on error
   - ✅ Test constraint violations handled

4. **File Upload Error Handling**
   - ✅ Test invalid file format rejection
   - ✅ Test file too large rejection
   - ✅ Test corrupted file handling

5. **Video Processing Error Handling**
   - ✅ Test invalid video format rejection
   - ✅ Test video processing failure
   - ✅ Test FFmpeg errors handled

**Test Tools**:
- pytest with mocked failures
- FastAPI TestClient for API error testing

---

### 5. Cross-Phase Integration Tests

#### Test Suite: `tests/integration/test_cross_phase.py`

**Test Cases**:

1. **Image to Video Workflow**
   - ✅ User annotates images in dataset
   - ✅ User uploads video to same project
   - ✅ User uses image annotations as reference for video tracking
   - ✅ Exports include both image and video annotations

2. **Batch to Individual Workflow**
   - ✅ User runs batch labeling job
   - ✅ User reviews batch-generated annotations
   - ✅ User refines individual annotations
   - ✅ Refined annotations preserve batch job metadata

3. **Collaboration Across Phases**
   - ✅ Multiple users annotate images (Phase 1)
   - ✅ Reviewer reviews annotations (Phase 3)
   - ✅ Approved annotations used for video tracking (Phase 2)

**Test Setup**:
- Full test environment with all phases enabled
- Test projects spanning multiple phases

---

### 6. API Integration Tests

#### Test Suite: `tests/integration/test_api_integration.py`

**Test Cases**:

1. **API Contract Testing**
   - ✅ Test all API endpoints return correct schema
   - ✅ Test request/response formats match OpenAPI spec
   - ✅ Test API versioning (if implemented)

2. **API Performance**
   - ✅ Test API response times acceptable
   - ✅ Test API handles concurrent requests
   - ✅ Test API rate limiting (if implemented)

3. **API Authentication**
   - ✅ Test authenticated endpoints require tokens
   - ✅ Test token expiration handled
   - ✅ Test token refresh works
   - ✅ Test unauthorized access denied

**Test Tools**:
- pytest with FastAPI TestClient
- OpenAPI schema validation
- Performance testing tools (Locust, k6)

---

### 7. Database Integration Tests

#### Test Suite: `tests/integration/test_database_integration.py`

**Test Cases**:

1. **CRUD Operations**
   - ✅ Test create, read, update, delete for all models
   - ✅ Test relationships preserved (foreign keys)
   - ✅ Test cascade deletes work correctly

2. **Transactions**
   - ✅ Test transaction rollback on error
   - ✅ Test transaction commits on success
   - ✅ Test concurrent transactions handled

3. **Query Performance**
   - ✅ Test queries perform acceptably
   - ✅ Test indexes used correctly
   - ✅ Test N+1 query problems avoided

**Test Setup**:
- Real database (PostgreSQL test instance)
- Test data fixtures
- Database cleanup after tests

---

## Test Execution

### Running Integration Tests

```bash
# All integration tests
pytest tests/integration/ -v

# Specific integration test suite
pytest tests/integration/test_cross_phase.py -v

# E2E tests (when implemented)
pytest tests/e2e/ -v
# or for frontend E2E:
npm run test:e2e
```

### Running with Coverage

```bash
pytest tests/integration/ --cov=app --cov-report=html
```

---

## Test Environment Setup

### Backend Test Environment

- PostgreSQL test database
- Real SAM3 model (if GPU available) or mocked
- FastAPI test server
- Test data fixtures

### Frontend Test Environment (When Implemented)

- Test browser (Playwright/Cypress)
- Mock API or real backend
- Test user accounts
- Test projects and data

---

## Success Criteria

- ✅ All critical user journeys tested end-to-end
- ✅ All API integrations tested
- ✅ All error scenarios handled correctly
- ✅ Performance meets requirements
- ✅ Database operations tested thoroughly
- ✅ Cross-phase workflows tested

---

## Known Challenges

1. **Test Data Management**: Large test datasets can be slow
   - Use minimal test data
   - Use test fixtures
   - Clean up test data after tests

2. **Model Inference**: Real model inference is slow
   - Use mocked model for most tests
   - Use real model for critical E2E tests only
   - Set appropriate timeouts

3. **Concurrency**: Testing concurrent operations is complex
   - Use async/await properly
   - Test with multiple users/clients
   - Use proper synchronization

4. **Flakiness**: E2E tests can be flaky
   - Use proper waits (not sleep)
   - Retry on known flaky operations
   - Isolate tests from each other

---

**Next**: See `test-plan-08-performance.md` for performance and load tests

