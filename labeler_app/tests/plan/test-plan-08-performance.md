# Test Plan: Performance & Load Tests

## Overview

This document defines the test plan for performance, load, and stress testing of the SAM 3 Labeling App. These tests validate system performance characteristics, resource usage, and scalability.

**Target Metrics**: Defined below  
**Test Tools**: pytest-benchmark, Locust, custom scripts

## Test Categories

### 1. Model Inference Performance Tests

#### Test Suite: `tests/performance/test_model_inference.py`

**Test Cases**:

1. **Image Inference Latency**
   - ✅ Test text prompt inference latency (< 2 seconds per image)
   - ✅ Test geometric prompt inference latency
   - ✅ Test exemplar prompt inference latency
   - ✅ Test batch inference latency (10 images, < 20 seconds)

2. **Video Inference Latency**
   - ✅ Test video tracking latency per frame (< 100ms per frame)
   - ✅ Test full video tracking latency (30s video, < 5 minutes)
   - ✅ Test correction propagation latency (< 500ms per frame)

3. **Model Loading Performance**
   - ✅ Test model loading time (< 30 seconds)
   - ✅ Test model warmup time (< 10 seconds)
   - ✅ Test model memory usage (< 8GB VRAM)

**Test Tools**:
- pytest-benchmark for latency measurements
- Custom scripts for GPU memory monitoring

**Target Metrics**:
- Image inference: < 2s per image
- Video tracking: < 100ms per frame
- Model loading: < 30s
- GPU memory: < 8GB VRAM

---

### 2. API Performance Tests

#### Test Suite: `tests/performance/test_api_performance.py`

**Test Cases**:

1. **Endpoint Response Times**
   - ✅ Test text prompt endpoint latency (< 3s including inference)
   - ✅ Test batch job creation latency (< 1s)
   - ✅ Test video upload endpoint latency (< 5s for small video)
   - ✅ Test export endpoint latency (< 10s for 1000 images)
   - ✅ Test user authentication latency (< 500ms)

2. **Concurrent Request Handling**
   - ✅ Test API handles 10 concurrent requests
   - ✅ Test API handles 50 concurrent requests
   - ✅ Test API handles 100 concurrent requests
   - ✅ Test response times degrade gracefully

3. **Database Query Performance**
   - ✅ Test annotation list query latency (< 100ms for 1000 annotations)
   - ✅ Test image list query latency (< 200ms for 1000 images)
   - ✅ Test project member query latency (< 50ms)
   - ✅ Test query performance with indexes

**Test Tools**:
- pytest-benchmark
- Locust for load testing
- Custom scripts for concurrent requests

**Target Metrics**:
- Text prompt endpoint: < 3s
- Batch job creation: < 1s
- Export (1000 images): < 10s
- Concurrent requests: 50+ supported

---

### 3. Batch Processing Performance Tests

#### Test Suite: `tests/performance/test_batch_processing.py`

**Test Cases**:

1. **Batch Job Throughput**
   - ✅ Test batch processing of 100 images (< 5 minutes)
   - ✅ Test batch processing of 500 images (< 25 minutes)
   - ✅ Test batch processing of 1000 images (< 50 minutes)
   - ✅ Test progress updates frequency

2. **Memory Usage During Batch Processing**
   - ✅ Test memory usage stays within limits (< 16GB RAM)
   - ✅ Test memory leaks (memory stable over long runs)
   - ✅ Test GPU memory stable during batch processing

3. **Presence Token Filtering Performance**
   - ✅ Test presence token check latency (< 100ms per image)
   - ✅ Test skip_empty_images reduces processing time
   - ✅ Test filtering accuracy (no false positives/negatives)

**Test Tools**:
- Custom scripts for batch processing
- Memory profiling tools (memory_profiler, py-spy)

**Target Metrics**:
- 100 images: < 5 minutes
- 500 images: < 25 minutes
- 1000 images: < 50 minutes
- Memory stable over long runs

---

### 4. Video Processing Performance Tests

#### Test Suite: `tests/performance/test_video_processing.py`

**Test Cases**:

1. **Video Upload & Processing**
   - ✅ Test video metadata extraction latency (< 5s for 1-minute video)
   - ✅ Test keyframe extraction latency (< 10s for 1-minute video)
   - ✅ Test HLS transcoding latency (< 2 minutes for 1-minute video)
   - ✅ Test full video processing pipeline latency

2. **Video Tracking Performance**
   - ✅ Test tracking session initialization latency (< 5s)
   - ✅ Test frame-by-frame tracking throughput
   - ✅ Test memory bank updates latency
   - ✅ Test correction propagation latency

3. **Video Storage**
   - ✅ Test video file storage performance
   - ✅ Test HLS segment serving performance
   - ✅ Test frame extraction performance

**Test Tools**:
- Custom scripts for video processing
- FFmpeg benchmarking
- Storage I/O monitoring

**Target Metrics**:
- Metadata extraction: < 5s for 1-minute video
- Keyframe extraction: < 10s for 1-minute video
- HLS transcoding: < 2 minutes for 1-minute video

---

### 5. Frontend Performance Tests

#### Test Suite: `tests/performance/test_frontend_performance.ts` (When Implemented)

**Test Cases** (Planned):

1. **Component Render Performance**
   - ⏳ Test Concept Command Bar render time (< 50ms)
   - ⏳ Test Annotation Canvas render time (< 100ms)
   - ⏳ Test Mask Overlay render time (< 50ms per mask)
   - ⏳ Test page load time (< 2 seconds)

2. **Mask Rendering Performance**
   - ⏳ Test RLE decoding performance (< 10ms per mask)
   - ⏳ Test canvas drawing performance (< 16ms for 60fps)
   - ⏳ Test multiple mask rendering (< 100ms for 10 masks)

3. **API Call Performance**
   - ⏳ Test API request latency from frontend
   - ⏳ Test response parsing time
   - ⏳ Test error handling doesn't block UI

**Test Tools** (Planned):
- Lighthouse for page performance
- React DevTools Profiler
- Custom performance monitoring

**Target Metrics** (When Implemented):
- Page load: < 2s
- Component render: < 100ms
- Mask rendering: 60fps for single mask

---

### 6. Database Performance Tests

#### Test Suite: `tests/performance/test_database_performance.py`

**Test Cases**:

1. **Query Performance**
   - ✅ Test annotation queries with indexes
   - ✅ Test image queries with filters
   - ✅ Test project member queries
   - ✅ Test complex joins performance

2. **Write Performance**
   - ✅ Test annotation creation throughput
   - ✅ Test batch annotation creation
   - ✅ Test video asset creation performance

3. **Database Scaling**
   - ✅ Test performance with 10,000 annotations
   - ✅ Test performance with 100,000 annotations
   - ✅ Test performance with 1,000,000 annotations
   - ✅ Test query performance degradation

**Test Tools**:
- pytest-benchmark
- Database query profiling
- PostgreSQL EXPLAIN ANALYZE

**Target Metrics**:
- Annotation query (10k): < 100ms
- Annotation query (100k): < 500ms
- Write throughput: 100+ annotations/second

---

### 7. Load Testing

#### Test Suite: `tests/load/test_load.py` (Locust)

**Test Scenarios**:

1. **Normal Load**
   - ✅ Simulate 10 concurrent users
   - ✅ Test text prompting, batch jobs, exports
   - ✅ Test API response times acceptable
   - ✅ Test no errors under normal load

2. **High Load**
   - ✅ Simulate 50 concurrent users
   - ✅ Test system stability
   - ✅ Test response times (may degrade)
   - ✅ Test error rate (< 1%)

3. **Stress Testing**
   - ✅ Simulate 100+ concurrent users
   - ✅ Test system breaking point
   - ✅ Test recovery after load reduction
   - ✅ Test resource limits (memory, CPU, GPU)

**Test Tools**:
- Locust for load testing
- Custom scripts for GPU monitoring

**Target Metrics**:
- Normal load (10 users): All requests < 3s
- High load (50 users): 95% requests < 5s
- Error rate: < 1%

---

### 8. Resource Usage Tests

#### Test Suite: `tests/performance/test_resource_usage.py`

**Test Cases**:

1. **Memory Usage**
   - ✅ Test baseline memory usage
   - ✅ Test memory usage during inference
   - ✅ Test memory usage during batch processing
   - ✅ Test memory leaks (memory stable over 1 hour)

2. **GPU Usage**
   - ✅ Test GPU memory usage
   - ✅ Test GPU utilization during inference
   - ✅ Test GPU memory fragmentation

3. **CPU Usage**
   - ✅ Test CPU usage during API requests
   - ✅ Test CPU usage during batch processing
   - ✅ Test CPU usage during video processing

4. **Disk I/O**
   - ✅ Test disk read/write performance
   - ✅ Test storage space usage
   - ✅ Test file system performance

**Test Tools**:
- Memory profiling (memory_profiler, py-spy)
- GPU monitoring (nvidia-smi)
- System monitoring (psutil)

**Target Metrics**:
- Memory: < 16GB RAM usage
- GPU memory: < 8GB VRAM
- CPU: < 80% average usage
- Disk I/O: Acceptable for storage backend

---

## Test Execution

### Running Performance Tests

```bash
# Model inference performance
pytest tests/performance/test_model_inference.py --benchmark-only

# API performance
pytest tests/performance/test_api_performance.py --benchmark-only

# Batch processing performance
pytest tests/performance/test_batch_processing.py --benchmark-only

# All performance tests
pytest tests/performance/ --benchmark-only
```

### Running Load Tests

```bash
# Start Locust
locust -f tests/load/test_load.py --host=http://localhost:8000

# Or run headless
locust -f tests/load/test_load.py --headless --users 10 --spawn-rate 2 --run-time 60s
```

### Generating Performance Reports

```bash
# Benchmark report
pytest tests/performance/ --benchmark-only --benchmark-json=benchmark.json

# Generate HTML report
pytest-benchmark compare benchmark.json --html=benchmark_report.html
```

---

## Benchmarking Baselines

### Hardware Requirements

**Minimum Requirements**:
- CPU: 4 cores
- RAM: 16GB
- GPU: 8GB VRAM (for SAM3 model)
- Storage: SSD recommended

**Recommended Requirements**:
- CPU: 8+ cores
- RAM: 32GB
- GPU: 16GB+ VRAM (H200 for production)
- Storage: NVMe SSD

### Baseline Metrics

**Image Inference**:
- Target: < 2s per image
- Baseline: ~1.5s per image (on H200 GPU)

**Video Tracking**:
- Target: < 100ms per frame
- Baseline: ~80ms per frame (on H200 GPU)

**API Response**:
- Target: < 3s for text prompt endpoint
- Baseline: ~2.5s (including inference)

---

## Success Criteria

- ✅ All performance targets met
- ✅ System handles expected load
- ✅ Resource usage within limits
- ✅ No memory leaks detected
- ✅ Performance degradation acceptable under high load
- ✅ System recovers after stress testing

---

## Known Limitations

1. **Hardware Dependent**: Performance varies significantly with hardware
   - Benchmark on target hardware
   - Document hardware specifications in reports

2. **Model Dependent**: SAM3 model performance may vary
   - Test with actual SAM3 model
   - Consider model optimization for production

3. **Network Dependent**: API performance depends on network
   - Test in local environment for consistency
   - Document network conditions in reports

4. **Test Data Dependent**: Performance depends on test data
   - Use representative test data
   - Document test data characteristics

---

**Next**: Return to `test-plan-00-overview.md` for test plan overview

