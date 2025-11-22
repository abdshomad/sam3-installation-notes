# Test Plan Overview - SAM 3 Labeling App

## Document Purpose

This document provides an overview of the comprehensive test plan for the SAM 3 Image Labeling App. The test plan is organized into multiple files covering different phases and test types.

## Test Plan Structure

### Core Test Documents

- **`test-plan-00-overview.md`** (this file) - Test strategy, coverage overview, and test execution guidelines
- **`test-plan-01-phase1-backend.md`** - Phase 1 (Core PCS Engine) backend tests
- **`test-plan-02-phase1-frontend.md`** - Phase 1 (Core PCS Engine) frontend tests
- **`test-plan-03-phase2-backend.md`** - Phase 2 (Video & Tracking) backend tests
- **`test-plan-04-phase2-frontend.md`** - Phase 2 (Video & Tracking) frontend tests (placeholder)
- **`test-plan-05-phase3-backend.md`** - Phase 3 (Collaboration) backend tests
- **`test-plan-06-phase3-frontend.md`** - Phase 3 (Collaboration) frontend tests (placeholder)
- **`test-plan-07-integration.md`** - Cross-phase integration and end-to-end tests
- **`test-plan-08-performance.md`** - Performance, load, and stress tests

## Implementation Status Reference

Based on `plan-based-on-prd-implemented.md`:

- **Phase 1 (Core PCS Engine)**: ✅ 90% Complete (Backend: 100%, Frontend: 85%)
- **Phase 2 (Video & Tracking)**: ✅ 70% Complete (Backend: 100%, Frontend: 0%)
- **Phase 3 (Collaboration)**: ✅ 50% Complete (Backend: 60%, Frontend: 0%)

## Test Coverage Goals

### Phase 1: Core PCS Engine
- **Backend**: 90%+ code coverage for inference services, API endpoints, batch processing
- **Frontend**: 80%+ coverage for components, user interactions, state management
- **Integration**: Full workflow testing (text prompt → mask → annotation)

### Phase 2: Video & Tracking
- **Backend**: 85%+ code coverage for video processing, tracking, memory bank
- **Frontend**: N/A (not yet implemented)
- **Integration**: Video upload → tracking → correction propagation

### Phase 3: Collaboration
- **Backend**: 80%+ code coverage for RBAC, consensus, user management
- **Frontend**: N/A (not yet implemented)
- **Integration**: Multi-user annotation → consensus voting

## Test Types

### 1. Unit Tests
- **Purpose**: Test individual functions, methods, and classes in isolation
- **Scope**: Services, utilities, data models, helper functions
- **Tools**: pytest (backend), Jest/Vitest (frontend)
- **Target Coverage**: 80%+

### 2. Integration Tests
- **Purpose**: Test interaction between components (services, API endpoints, database)
- **Scope**: API endpoints, service integrations, database operations
- **Tools**: pytest with FastAPI TestClient, test database
- **Target Coverage**: Critical workflows 100%

### 3. End-to-End Tests
- **Purpose**: Test complete user workflows from frontend to backend
- **Scope**: Full annotation workflows, batch processing, video tracking
- **Tools**: Playwright, Cypress, or similar E2E framework
- **Target Coverage**: All critical user journeys

### 4. Component Tests (Frontend)
- **Purpose**: Test React components in isolation with mocked dependencies
- **Scope**: UI components, hooks, state management
- **Tools**: React Testing Library, Vitest
- **Target Coverage**: 75%+

### 5. API Tests
- **Purpose**: Test API contracts, request/response formats, error handling
- **Scope**: All API endpoints, authentication, authorization
- **Tools**: pytest with FastAPI TestClient
- **Target Coverage**: 100% endpoint coverage

### 6. Performance Tests
- **Purpose**: Validate performance characteristics and resource usage
- **Scope**: Model inference latency, batch processing throughput, concurrent requests
- **Tools**: Locust, pytest-benchmark, custom load testing scripts
- **Target Metrics**: See `test-plan-08-performance.md`

## Test Environment Setup

### Backend Test Environment

```bash
# Python test environment
uv venv .venv-test
source .venv-test/bin/activate
uv pip install pytest pytest-cov pytest-asyncio httpx sqlmodel
```

### Frontend Test Environment

```bash
# Frontend test environment (if using Vitest/Jest)
cd frontend
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
```

### Test Database

- Use SQLite in-memory database for unit tests
- Use PostgreSQL test instance for integration tests
- Use test fixtures and factories for consistent test data

### Mock SAM3 Model

- Create lightweight mock SAM3 model for unit tests
- Use real model for integration tests (if GPU available)
- Consider model stub/patches for fast unit test execution

## Test Execution Strategy

### Continuous Integration (CI)

1. **Pre-commit hooks**: Lint, format, quick unit tests
2. **Pull Request checks**: Full unit + integration test suite
3. **Merge to main**: Full test suite + E2E tests
4. **Nightly builds**: Full suite + performance benchmarks

### Test Execution Order

1. Unit tests (fast, isolated)
2. Integration tests (moderate speed, dependencies)
3. E2E tests (slow, full stack)
4. Performance tests (scheduled, separate runs)

### Test Data Management

- Use test fixtures for consistent data
- Isolate test data per test suite
- Clean up test data after each test run
- Use factories for generating test data

## Critical Test Scenarios

### Must-Have Tests (P0 - Critical)

1. ✅ SAM3 inference service handles all prompt types correctly
2. ✅ Model manager loads and manages model singleton properly
3. ✅ Text-to-mask API creates annotations with correct presence scores
4. ✅ Batch processing completes successfully for datasets
5. ✅ Mask rendering displays correctly in frontend
6. ✅ Confidence indicators show correct color coding
7. ✅ Export formats generate valid output files

### Should-Have Tests (P1 - Important)

1. ✅ Video upload and processing pipeline
2. ✅ Video tracking session management
3. ✅ Correction propagation updates masklets correctly
4. ✅ RBAC permission checks work correctly
5. ✅ Consensus voting calculates IoU correctly
6. ✅ User authentication and authorization

### Nice-to-Have Tests (P2 - Enhancement)

1. Performance benchmarks for model inference
2. Load testing for concurrent users
3. Memory leak detection
4. Edge case handling (empty images, invalid prompts, etc.)

## Test Metrics & Reporting

### Coverage Metrics

- **Code Coverage**: Target 80%+ overall
- **Branch Coverage**: Target 75%+ overall
- **Function Coverage**: Target 85%+ overall

### Quality Metrics

- **Test Pass Rate**: 100% (all tests must pass before merge)
- **Test Execution Time**: Unit tests < 5 min, Integration < 15 min, E2E < 30 min
- **Flaky Test Rate**: < 1% (tests should be deterministic)

### Reporting Tools

- pytest-html for test reports
- Coverage.py for coverage reports
- Allure or similar for detailed test reports

## Test Data & Fixtures

### Image Test Data

- Small test images (< 1MB) for unit tests
- Diverse images (various sizes, formats) for integration tests
- Real-world images for E2E tests
- Edge cases: very large images, corrupted images, unsupported formats

### Video Test Data

- Short test videos (< 10 seconds) for unit tests
- Various formats (MP4, AVI, MOV) for integration tests
- Real-world videos for E2E tests

### Mock Data

- Mock SAM3 model responses
- Mock database responses
- Mock API responses for external services

## Known Limitations & Risks

### Testing Challenges

1. **GPU Dependency**: SAM3 model requires GPU for full functionality
   - **Solution**: Mock model for unit tests, skip GPU tests in CI if unavailable

2. **Large File Sizes**: Video files and model checkpoints are large
   - **Solution**: Use compressed test files, model stubs for unit tests

3. **Model Inference Time**: SAM3 inference is slow
   - **Solution**: Timeout settings, async tests, benchmarking separate from unit tests

4. **External Dependencies**: FFmpeg for video processing
   - **Solution**: Docker container with all dependencies, skip video tests if FFmpeg unavailable

### Test Environment Requirements

- Python 3.10+
- Node.js 18+
- PostgreSQL (for integration tests)
- GPU (optional, for full model testing)
- FFmpeg (for video tests)

## Test Maintenance

### Regular Tasks

- Update tests when features change
- Remove obsolete tests
- Refactor flaky tests
- Add tests for bug fixes
- Review and improve test coverage

### Test Documentation

- Document test fixtures and test data
- Document test environment setup
- Document known test limitations
- Update test plan as features evolve

## References

- **Implementation Status**: `plan-based-on-prd-implemented.md`
- **Original PRD**: `PRD for SAM 3 Image Labeling App.md`
- **Original Plan**: `plan-based-on-prd.md`

## Test Plan Status

- **Created**: [Current Date]
- **Last Updated**: [Current Date]
- **Version**: 1.0
- **Status**: Initial draft, ready for implementation

---

**Next Steps**: 
1. Review and approve test plan structure
2. Begin implementing tests starting with Phase 1 backend (see `test-plan-01-phase1-backend.md`)
3. Set up CI/CD pipeline with test execution
4. Establish test data repository

