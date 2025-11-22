# Test Plan: Phase 2 Backend - Video & Tracking

## Overview

This document defines the test plan for Phase 2 backend components of the SAM 3 Labeling App. Phase 2 includes video asset management, SAM3 video inference, masklet tracking, memory bank management, and video export formats.

**Status**: Backend 100% Complete ✅  
**Target Coverage**: 85%+ code coverage

## Test Categories

### 1. Video Processor Service Tests

#### Test Suite: `tests/unit/services/test_video_processor.py`

**Test Cases**:

1. **Video Metadata Extraction**
   - ✅ Test extracts width, height from video
   - ✅ Test extracts FPS from video
   - ✅ Test extracts duration from video
   - ✅ Test extracts frame count from video
   - ✅ Test handles various video formats (MP4, AVI, MOV)
   - ✅ Test error handling for invalid video files

2. **Keyframe Extraction**
   - ✅ Test extracts keyframes based on scene change detection
   - ✅ Test keyframes saved as images
   - ✅ Test keyframe filenames follow convention
   - ✅ Test handles videos with no scene changes

3. **HLS Transcoding**
   - ✅ Test transcodes video to HLS format
   - ✅ Test generates manifest file (.m3u8)
   - ✅ Test generates segment files (.ts)
   - ✅ Test transcoding with different qualities
   - ✅ Test error handling for transcoding failures

4. **Video Processing Pipeline**
   - ✅ Test `process_video()` runs all steps in order
   - ✅ Test async processing completes successfully
   - ✅ Test database updates with video metadata
   - ✅ Test ImageAsset records created for keyframes
   - ✅ Test error handling for partial failures

**Mock Strategy**:
- Mock OpenCV (cv2) video operations
- Mock FFmpeg transcoding
- Mock file system operations

**Test Data**:
- Short test videos (< 10 seconds)
- Various video formats
- Videos with scene changes

---

### 2. Video Asset API Tests

#### Test Suite: `tests/integration/api/test_videos.py`

**Test Cases**:

1. **Video Upload**
   - ✅ Test `POST /videos/upload`
   - ✅ Test file upload accepted
   - ✅ Test video asset created in database
   - ✅ Test background processing triggered
   - ✅ Test error handling for invalid file format
   - ✅ Test error handling for file too large

2. **Video Listing**
   - ✅ Test `GET /videos` returns video list
   - ✅ Test filtering by project_id
   - ✅ Test filtering by dataset_id
   - ✅ Test pagination (if implemented)
   - ✅ Test sorting options

3. **Video Details**
   - ✅ Test `GET /videos/{video_id}` returns metadata
   - ✅ Test metadata includes all fields (duration, fps, frame_count)
   - ✅ Test error handling for non-existent video

4. **Video Content**
   - ✅ Test `GET /videos/{video_id}/content` returns video file
   - ✅ Test correct content-type header
   - ✅ Test file streaming works

5. **Frame Extraction**
   - ✅ Test `GET /videos/{video_id}/frames/{frame_idx}` returns frame
   - ✅ Test frame extracted correctly
   - ✅ Test error handling for invalid frame index
   - ✅ Test error handling for non-existent video

**Test Setup**:
- Use FastAPI TestClient
- Create test database with test videos
- Mock video processing (or use small test videos)
- Clean up test data after tests

---

### 3. SAM3 Video Inference Service Tests

#### Test Suite: `tests/unit/services/test_sam3_video_inference.py`

**Test Cases**:

1. **Model Loading**
   - ✅ Test video model loads successfully
   - ✅ Test singleton pattern for model
   - ✅ Test model loads on CUDA/CPU correctly
   - ✅ Test error handling for model loading failure

2. **Session Management**
   - ✅ Test `start_session()` creates new session
   - ✅ Test session ID generation
   - ✅ Test session state stored correctly
   - ✅ Test multiple concurrent sessions supported
   - ✅ Test error handling for invalid video path

3. **Prompt Addition**
   - ✅ Test `add_prompt()` with text prompt
   - ✅ Test `add_prompt()` with point prompts
   - ✅ Test `add_prompt()` with box prompts
   - ✅ Test `add_prompt()` with obj_id assignment
   - ✅ Test prompts stored in session state
   - ✅ Test error handling for invalid frame index

4. **Object Tracking**
   - ✅ Test `track_objects()` generates masklets
   - ✅ Test forward tracking direction
   - ✅ Test backward tracking direction
   - ✅ Test bidirectional tracking
   - ✅ Test frame-by-frame masklet generation
   - ✅ Test max_frame_num_to_track limit
   - ✅ Test error handling for tracking failures

5. **Session Cleanup**
   - ✅ Test sessions cleaned up correctly
   - ✅ Test session state persisted (if enabled)
   - ✅ Test error handling for invalid session ID

**Mock Strategy**:
- Mock `Sam3VideoPredictor` class
- Mock video model forward pass
- Mock memory bank operations

**Test Data**:
- Test video paths
- Mock video predictor outputs (masklets)

---

### 4. Memory Bank Manager Tests

#### Test Suite: `tests/unit/services/test_memory_bank_manager.py`

**Test Cases**:

1. **Memory Bank Storage**
   - ✅ Test memory bank state stored per session
   - ✅ Test memory bank updates correctly
   - ✅ Test FIFO buffer management (7 frames)
   - ✅ Test memory bank serialization

2. **Keyframe Management**
   - ✅ Test `mark_keyframe()` adds keyframe
   - ✅ Test `unmark_keyframe()` removes keyframe
   - ✅ Test keyframes stored in memory bank
   - ✅ Test keyframe list retrieval

3. **Memory Context**
   - ✅ Test `get_memory_context()` returns state
   - ✅ Test context includes keyframes
   - ✅ Test context includes memory snapshots
   - ✅ Test context includes active frames

4. **Memory Bank Updates**
   - ✅ Test `update_memory_bank()` updates state
   - ✅ Test updates propagate to tracking
   - ✅ Test memory bank resets correctly

**Mock Strategy**:
- Mock memory bank state storage
- Test with in-memory storage for unit tests

---

### 5. Track Manager Tests

#### Test Suite: `tests/unit/services/test_track_manager.py`

**Test Cases**:

1. **Track Merging**
   - ✅ Test `merge_tracks()` combines multiple tracks
   - ✅ Test merged track has combined frame range
   - ✅ Test new track ID assigned (if not provided)
   - ✅ Test original tracks removed/updated
   - ✅ Test error handling for invalid track IDs

2. **Track Splitting**
   - ✅ Test `split_track()` splits at frame index
   - ✅ Test new track created with correct frame range
   - ✅ Test original track updated with new frame range
   - ✅ Test new track ID assigned (if not provided)
   - ✅ Test error handling for invalid frame index

3. **Track Information**
   - ✅ Test `get_track_info()` returns track details
   - ✅ Test `list_tracks()` returns all tracks in session
   - ✅ Test track info includes frame range, obj_id

**Mock Strategy**:
- Mock track storage (in-memory dictionary)
- Test track state management

---

### 6. Video Tracking API Tests

#### Test Suite: `tests/integration/api/test_video_tracking.py`

**Test Cases**:

1. **Session Creation**
   - ✅ Test `POST /video-tracking/sessions` creates session
   - ✅ Test session ID returned
   - ✅ Test video path validated
   - ✅ Test error handling for non-existent video

2. **Prompt Addition**
   - ✅ Test `POST /video-tracking/sessions/{session_id}/prompt`
   - ✅ Test text prompt accepted
   - ✅ Test point prompts accepted
   - ✅ Test box prompts accepted
   - ✅ Test obj_id assignment
   - ✅ Test error handling for invalid frame index

3. **Object Tracking**
   - ✅ Test `POST /video-tracking/sessions/{session_id}/track`
   - ✅ Test streaming response format (SSE/JSON stream)
   - ✅ Test masklets returned frame-by-frame
   - ✅ Test forward/backward/both directions
   - ✅ Test max_frame_num_to_track respected
   - ✅ Test error handling for tracking failures

4. **Correction Propagation**
   - ✅ Test `POST /video-tracking/sessions/{session_id}/correct`
   - ✅ Test mask correction updates memory bank
   - ✅ Test forward propagation works
   - ✅ Test backward propagation works
   - ✅ Test bidirectional propagation works
   - ✅ Test propagation_range limit respected

5. **Track Management**
   - ✅ Test `POST /video-tracking/sessions/{session_id}/merge-tracks`
   - ✅ Test `POST /video-tracking/sessions/{session_id}/split-track`
   - ✅ Test track operations return success status
   - ✅ Test error handling for invalid operations

6. **Memory Bank API**
   - ✅ Test `GET /video-tracking/sessions/{session_id}/memory-context`
   - ✅ Test memory context returned correctly
   - ✅ Test `POST /video-tracking/sessions/{session_id}/keyframes/{frame_idx}`
   - ✅ Test `DELETE /video-tracking/sessions/{session_id}/keyframes/{frame_idx}`

7. **Session Management**
   - ✅ Test `GET /video-tracking/sessions` lists active sessions
   - ✅ Test `GET /video-tracking/sessions/{session_id}` returns status
   - ✅ Test `DELETE /video-tracking/sessions/{session_id}` closes session
   - ✅ Test `POST /video-tracking/sessions/{session_id}/reset` resets session

**Test Setup**:
- Use FastAPI TestClient
- Create test video assets
- Mock video inference service (or use test videos)
- Test streaming responses

---

### 7. Video Export Service Tests

#### Test Suite: `tests/unit/services/exporters/test_coco_video_exporter.py`

**Test Cases**:

1. **COCO-Video Export**
   - ✅ Test `build_coco_video_export()` generates valid JSON
   - ✅ Test format matches COCO-Video specification
   - ✅ Test masklet IDs mapped to track IDs
   - ✅ Test frame-by-frame masks included
   - ✅ Test video metadata included

2. **Track Mapping**
   - ✅ Test masklet obj_id mapped to COCO track ID
   - ✅ Test stable IDs across frames
   - ✅ Test multiple objects tracked correctly

#### Test Suite: `tests/unit/services/exporters/test_mot_exporter.py`

**Test Cases**:

1. **MOT Challenge Export**
   - ✅ Test `build_mot_export()` generates CSV format
   - ✅ Test format matches MOT Challenge specification
   - ✅ Test frame-by-frame bounding boxes
   - ✅ Test stable IDs across frames
   - ✅ Test CSV per video format

2. **CSV Format**
   - ✅ Test CSV columns correct (frame, id, bbox, etc.)
   - ✅ Test bounding box format (x1, y1, x2, y2 or x, y, w, h)
   - ✅ Test file naming convention

**Test Suite**: `tests/integration/api/test_export_video.py`

**Test Cases**:

1. **Export API Endpoints**
   - ✅ Test `GET /export/{project_id}/coco-video`
   - ✅ Test `GET /export/{project_id}/mot`
   - ✅ Test exports only include video annotations
   - ✅ Test error handling for projects without videos

---

### 8. Integration Tests

#### Test Suite: `tests/integration/test_video_workflow.py`

**Test Cases**:

1. **Complete Video Upload Workflow**
   - ✅ Upload video file
   - ✅ Verify video asset created
   - ✅ Verify metadata extracted
   - ✅ Verify keyframes extracted
   - ✅ Verify HLS transcoding completed

2. **Complete Video Tracking Workflow**
   - ✅ Start tracking session
   - ✅ Add prompt to frame
   - ✅ Track objects forward/backward
   - ✅ Verify masklets created
   - ✅ Verify memory bank updated
   - ✅ Export to COCO-Video format

3. **Complete Correction Workflow**
   - ✅ Track objects to generate masklets
   - ✅ Correct mask at specific frame
   - ✅ Verify correction propagated
   - ✅ Verify masklets updated

4. **Complete Track Management Workflow**
   - ✅ Track multiple objects
   - ✅ Merge tracks
   - ✅ Split track at frame
   - ✅ Verify track operations successful

**Test Setup**:
- Full test environment (database, API, services)
- Test videos (short, low resolution for fast testing)
- Real SAM3 video model (if GPU available) or mocked

---

## Test Execution

### Running Tests

```bash
# Unit tests
pytest tests/unit/services/test_video_processor.py -v
pytest tests/unit/services/test_sam3_video_inference.py -v

# Integration tests
pytest tests/integration/api/test_videos.py -v
pytest tests/integration/api/test_video_tracking.py -v

# All Phase 2 backend tests
pytest tests/unit/services/test_video* tests/integration/api/test_video* -v --cov=app/services/video_processor --cov=app/services/sam3_video_inference
```

### Coverage Report

```bash
pytest --cov=app/services/video_processor --cov=app/services/sam3_video_inference --cov=app/services/memory_bank_manager --cov=app/services/track_manager --cov=app/api/routes/videos --cov=app/api/routes/video_tracking --cov-report=html
```

---

## Test Data Requirements

### Videos
- Short test videos (< 10 seconds, low resolution)
- Various formats (MP4, AVI, MOV)
- Videos with clear objects for tracking
- Videos with scene changes for keyframe testing

### Mock Data
- Mock SAM3 video model outputs (masklets)
- Mock video processor outputs
- Test database fixtures with video assets

---

## Success Criteria

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Code coverage ≥ 85% for video services and API routes
- ✅ All critical video workflows tested end-to-end
- ✅ Error handling tested for all error cases
- ✅ Streaming API responses tested correctly
- ✅ Memory bank management tested thoroughly

---

## Known Issues & Limitations

1. **GPU Dependency**: Full video model testing requires GPU
   - Use mocked model for unit tests
   - Skip GPU-dependent tests in CI if unavailable

2. **Video Processing Time**: Video processing is slow
   - Use short, low-resolution test videos
   - Mock video processing for unit tests
   - Use async timeouts for integration tests

3. **FFmpeg Dependency**: Video transcoding requires FFmpeg
   - Skip HLS tests if FFmpeg unavailable
   - Mock FFmpeg for unit tests

4. **Large File Sizes**: Video files are large
   - Use compressed test videos
   - Store test videos separately from code repository

---

**Next**: See `test-plan-04-phase2-frontend.md` for Phase 2 frontend tests (placeholder)

