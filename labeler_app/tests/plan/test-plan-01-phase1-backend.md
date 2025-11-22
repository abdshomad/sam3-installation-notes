# Test Plan: Phase 1 Backend - Core PCS Engine

## Overview

This document defines the test plan for Phase 1 backend components of the SAM 3 Labeling App. Phase 1 includes SAM3 integration, concept-based prompting, batch processing, and export functionality.

**Status**: Backend 100% Complete ✅  
**Target Coverage**: 90%+ code coverage

## Test Categories

### 1. SAM3 Model Manager Tests

#### Test Suite: `tests/unit/services/test_sam3_model_manager.py`

**Test Cases**:

1. **Model Singleton Pattern**
   - ✅ Test that only one instance is created (singleton)
   - ✅ Test thread safety with concurrent access
   - ✅ Test model caching (model not reloaded on multiple calls)

2. **Model Loading**
   - ✅ Test model loads successfully on first access
   - ✅ Test model loads on CPU when CUDA unavailable
   - ✅ Test model loads on CUDA when available
   - ✅ Test error handling when model fails to load

3. **Model Warmup**
   - ✅ Test model warmup runs after loading
   - ✅ Test warmup completes successfully
   - ✅ Test warmup handles errors gracefully

4. **Processor Creation**
   - ✅ Test processor created with default confidence threshold
   - ✅ Test processor created with custom confidence threshold
   - ✅ Test processor updates when threshold changes
   - ✅ Test processor reuses model instance

5. **Health Check**
   - ✅ Test `is_ready()` returns True after model loaded
   - ✅ Test `is_ready()` returns False before model loaded
   - ✅ Test `get_device()` returns correct device string

**Mock Strategy**: 
- Mock `build_sam3_image_model` function
- Mock `torch.cuda.is_available()`
- Mock model forward pass

**Test Data**: 
- Mock model weights
- Mock processor outputs

---

### 2. SAM3 Inference Service Tests

#### Test Suite: `tests/unit/services/test_sam3_inference.py`

**Test Cases**:

1. **Text Prompt Inference**
   - ✅ Test `prompt_image_with_text()` with valid prompt
   - ✅ Test returns structured response (masks, boxes, scores)
   - ✅ Test presence score extraction
   - ✅ Test filtering by confidence threshold
   - ✅ Test handling empty results
   - ✅ Test error handling for invalid image path
   - ✅ Test error handling for invalid prompt

2. **Geometric Prompt Inference**
   - ✅ Test `prompt_image_with_bbox()` with valid bbox
   - ✅ Test point prompts (positive/negative)
   - ✅ Test box prompts
   - ✅ Test coordinate normalization
   - ✅ Test error handling for invalid coordinates

3. **Exemplar Prompt Inference**
   - ✅ Test `prompt_image_with_exemplar()` with crop bbox
   - ✅ Test positive exemplar detection
   - ✅ Test negative exemplar detection
   - ✅ Test crop region extraction
   - ✅ Test error handling for invalid crop region

4. **Batch Inference**
   - ✅ Test `batch_infer_text_prompts()` processes multiple images
   - ✅ Test presence token check skips empty images
   - ✅ Test batch processing returns correct counts
   - ✅ Test error handling for partial failures
   - ✅ Test progress tracking

**Mock Strategy**:
- Mock `Sam3Processor` class
- Mock model forward pass outputs
- Mock image loading

**Test Data**:
- Sample images (various sizes)
- Mock SAM3 outputs (masks, boxes, presence tokens)

---

### 3. Concept API Endpoint Tests

#### Test Suite: `tests/integration/api/test_concepts.py`

**Test Cases**:

1. **Text-to-Mask Endpoint**
   - ✅ Test `POST /concepts/projects/{project_id}/images/{image_id}/prompt`
   - ✅ Test creates annotations in database
   - ✅ Test auto-creates label class from concept text
   - ✅ Test returns annotations with presence scores
   - ✅ Test filters by confidence threshold
   - ✅ Test error handling for non-existent project
   - ✅ Test error handling for non-existent image
   - ✅ Test error handling for invalid request body
   - ✅ Test authorization (project member required)

2. **Exemplar Endpoint**
   - ✅ Test `POST /concepts/projects/{project_id}/images/{image_id}/exemplar`
   - ✅ Test creates annotations from crop region
   - ✅ Test positive exemplar detection
   - ✅ Test negative exemplar detection
   - ✅ Test crop bbox validation
   - ✅ Test error handling for invalid crop coordinates
   - ✅ Test error handling for non-existent image

3. **Response Format**
   - ✅ Test response matches `AnnotationCreate` schema
   - ✅ Test presence_score in response
   - ✅ Test concept_text in response
   - ✅ Test exemplar_crop in response (for exemplar endpoint)
   - ✅ Test is_ai_generated flag set correctly

**Test Setup**:
- Use FastAPI TestClient
- Create test database with test projects/images
- Mock SAM3 inference service
- Clean up test data after tests

**Test Data**:
- Test project, dataset, image assets
- Valid/invalid request payloads

---

### 4. Batch Processing API Tests

#### Test Suite: `tests/integration/api/test_batch.py`

**Test Cases**:

1. **Batch Job Creation**
   - ✅ Test `POST /batch/projects/{project_id}/datasets/{dataset_id}/label`
   - ✅ Test job ID generation
   - ✅ Test job status initialization
   - ✅ Test validation of request parameters
   - ✅ Test error handling for non-existent project/dataset

2. **Batch Job Status**
   - ✅ Test `GET /batch/jobs/{job_id}`
   - ✅ Test returns job status (pending, processing, completed, failed)
   - ✅ Test progress tracking (processed, succeeded, failed, skipped)
   - ✅ Test error handling for non-existent job ID

3. **Batch Processing Logic**
   - ✅ Test `_process_batch_job()` processes all images
   - ✅ Test presence token check skips empty images (if enabled)
   - ✅ Test annotations created in database
   - ✅ Test progress updates during processing
   - ✅ Test error handling for individual image failures
   - ✅ Test partial completion (some images fail)
   - ✅ Test skip_empty_images flag behavior

4. **Background Task Execution**
   - ✅ Test job runs asynchronously
   - ✅ Test job status updates during execution
   - ✅ Test job completion updates status correctly
   - ✅ Test job failure handling

**Test Setup**:
- Use FastAPI BackgroundTasks (or mock)
- Test database with multiple images
- Mock SAM3 inference service
- Test both sync and async execution

**Test Data**:
- Test dataset with 10+ images
- Various image types (some empty, some with objects)

---

### 5. Export Service Tests

#### Test Suite: `tests/unit/services/exporters/test_saco_exporter.py`

**Test Cases**:

1. **SA-Co Export Format**
   - ✅ Test `build_saco_export()` generates valid JSON structure
   - ✅ Test includes all required fields (images, concepts, masks)
   - ✅ Test preserves open-vocabulary text prompts
   - ✅ Test includes presence scores
   - ✅ Test includes exemplar crops
   - ✅ Test handles empty projects gracefully
   - ✅ Test handles projects with no annotations

2. **Export Statistics**
   - ✅ Test concept count calculation
   - ✅ Test image count calculation
   - ✅ Test mask count calculation

**Test Suite**: `tests/integration/api/test_export.py`

**Test Cases**:

1. **Export API Endpoints**
   - ✅ Test `GET /export/{project_id}/saco`
   - ✅ Test `GET /export/{project_id}/coco`
   - ✅ Test `GET /export/{project_id}/coco-video` (if video assets exist)
   - ✅ Test `GET /export/{project_id}/mot` (if video assets exist)
   - ✅ Test `GET /export/{project_id}/yolo`
   - ✅ Test response format (JSON or file download)
   - ✅ Test error handling for non-existent project
   - ✅ Test authorization checks

2. **Export Format Validation**
   - ✅ Test COCO format matches COCO specification
   - ✅ Test SA-Co format matches expected structure
   - ✅ Test YOLO format has correct text files
   - ✅ Test file downloads have correct content-type

**Test Data**:
- Test project with annotations
- Test project with video assets
- Various annotation types (masks, boxes)

---

### 6. Data Model Tests

#### Test Suite: `tests/unit/models/test_entities.py`

**Test Cases**:

1. **Annotation Model**
   - ✅ Test `presence_score` field validation (0.0-1.0)
   - ✅ Test `concept_text` field max length
   - ✅ Test `exemplar_crop` JSON field serialization
   - ✅ Test `is_ai_generated` boolean field
   - ✅ Test annotation creation with SAM3 fields
   - ✅ Test annotation reading includes all fields

2. **Project Model**
   - ✅ Test `confidence_threshold` field validation (0.0-1.0)
   - ✅ Test default confidence threshold (0.7)
   - ✅ Test project creation with threshold

3. **Schema Validation**
   - ✅ Test `AnnotationCreate` schema validation
   - ✅ Test `AnnotationRead` schema includes all fields
   - ✅ Test `ProjectRead` schema includes confidence_threshold

**Test Setup**:
- Use SQLModel test database
- Test model instantiation
- Test database operations (CRUD)

---

### 7. Integration Tests

#### Test Suite: `tests/integration/test_full_workflow.py`

**Test Cases**:

1. **Complete Text Prompt Workflow**
   - ✅ Create project with confidence threshold
   - ✅ Upload image asset
   - ✅ Send text prompt via API
   - ✅ Verify annotation created in database
   - ✅ Verify label class auto-created
   - ✅ Verify presence score stored correctly
   - ✅ Export annotations in SA-Co format

2. **Complete Exemplar Workflow**
   - ✅ Create project and upload image
   - ✅ Send exemplar prompt with crop region
   - ✅ Verify annotation created with exemplar_crop
   - ✅ Verify detection matches crop region

3. **Complete Batch Processing Workflow**
   - ✅ Create dataset with multiple images
   - ✅ Submit batch labeling job
   - ✅ Monitor job status
   - ✅ Verify annotations created for all images
   - ✅ Verify skip_empty_images behavior

**Test Setup**:
- Full test environment (database, API, services)
- Real SAM3 model (if GPU available) or mocked
- Clean test data before/after

---

## Test Execution

### Running Tests

```bash
# Unit tests
pytest tests/unit/services/test_sam3_model_manager.py -v
pytest tests/unit/services/test_sam3_inference.py -v

# Integration tests
pytest tests/integration/api/test_concepts.py -v
pytest tests/integration/api/test_batch.py -v

# All Phase 1 backend tests
pytest tests/unit/services/ tests/integration/api/ -v --cov=app/services --cov=app/api/routes/concepts --cov=app/api/routes/batch
```

### Coverage Report

```bash
pytest --cov=app/services/sam3_model_manager --cov=app/services/sam3_inference --cov=app/api/routes/concepts --cov=app/api/routes/batch --cov-report=html
```

---

## Test Data Requirements

### Images
- Small test images (< 1MB) for unit tests
- Various formats (JPEG, PNG)
- Various sizes (512x512, 1024x1024, etc.)
- Edge cases: very large images, corrupted images

### Mock Data
- Mock SAM3 model outputs
- Mock processor responses
- Test database fixtures

---

## Success Criteria

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Code coverage ≥ 90% for services and API routes
- ✅ All critical workflows tested end-to-end
- ✅ Error handling tested for all error cases
- ✅ Performance tests meet latency requirements (see `test-plan-08-performance.md`)

---

## Known Issues & Limitations

1. **GPU Dependency**: Full model testing requires GPU
   - Use mocked model for unit tests
   - Skip GPU-dependent tests in CI if unavailable

2. **Model Inference Time**: SAM3 inference is slow
   - Use timeouts in tests
   - Separate performance tests from unit tests

---

**Next**: See `test-plan-02-phase1-frontend.md` for frontend tests

