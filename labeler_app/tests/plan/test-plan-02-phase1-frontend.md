# Test Plan: Phase 1 Frontend - Core PCS Engine

## Overview

This document defines the test plan for Phase 1 frontend components of the SAM 3 Labeling App. Phase 1 includes the Concept Command Bar, confidence indicators, crop tool, batch labeling dialog, and mask rendering.

**Status**: Frontend 85% Complete ✅  
**Target Coverage**: 80%+ code coverage

## Test Categories

### 1. Concept Command Bar Component Tests

#### Test Suite: `tests/components/ConceptCommandBar.test.tsx`

**Test Cases**:

1. **Component Rendering**
   - ✅ Test component renders correctly
   - ✅ Test input field is visible and enabled
   - ✅ Test submit button renders
   - ✅ Test disabled state when image not selected
   - ✅ Test placeholder text displays

2. **User Input**
   - ✅ Test user can type in input field
   - ✅ Test Enter key submits prompt
   - ✅ Test submit button triggers submission
   - ✅ Test input clears after successful submission
   - ✅ Test input validation (empty prompt)

3. **API Integration**
   - ✅ Test API call made with correct parameters
   - ✅ Test loading state during API call
   - ✅ Test success callback triggers annotation refresh
   - ✅ Test error handling and error message display
   - ✅ Test confidence threshold passed correctly

4. **State Management**
   - ✅ Test loading state updates correctly
   - ✅ Test disabled state when project/image missing
   - ✅ Test instance count display after detection
   - ✅ Test presence token display after detection

**Mock Strategy**:
- Mock API client (`api/concepts.ts`)
- Mock React Query hooks
- Mock callbacks (`onConceptPrompt`)

**Test Utilities**:
- React Testing Library
- Mock service worker (MSW) for API mocking
- Custom render with providers (QueryClient, etc.)

---

### 2. Confidence Indicator Component Tests

#### Test Suite: `tests/components/ConfidenceIndicator.test.tsx`

**Test Cases**:

1. **ConfidenceIndicator Component**
   - ✅ Test renders progress bar
   - ✅ Test color coding (green ≥ 0.7, yellow 0.5-0.7, red < 0.5)
   - ✅ Test progress bar width matches score
   - ✅ Test handles edge cases (0.0, 1.0, null, undefined)
   - ✅ Test different sizes (sm, md, lg)

2. **ConfidenceBadge Component**
   - ✅ Test renders badge with score
   - ✅ Test color coding matches threshold
   - ✅ Test low confidence warning indicator
   - ✅ Test badge size variations

3. **Threshold Comparison**
   - ✅ Test highlights low confidence (score < threshold)
   - ✅ Test shows warning for borderline scores
   - ✅ Test threshold customization

**Test Data**:
- Various confidence scores (0.0, 0.4, 0.6, 0.75, 0.9, 1.0)
- Various thresholds (0.5, 0.7, 0.9)

---

### 3. Crop Tool Component Tests

#### Test Suite: `tests/components/CropTool.test.tsx`

**Test Cases**:

1. **Component Rendering**
   - ✅ Test overlay renders over canvas
   - ✅ Test dimmed region outside crop area
   - ✅ Test crop handles visible
   - ✅ Test initial crop area (if provided)

2. **User Interaction**
   - ✅ Test user can click and drag to select crop region
   - ✅ Test crop handles can be resized
   - ✅ Test ESC key cancels crop mode
   - ✅ Test click outside cancels crop (if enabled)

3. **Coordinate Handling**
   - ✅ Test coordinates normalized to [0, 1] range
   - ✅ Test coordinates converted based on image metrics
   - ✅ Test coordinates clipped to image bounds
   - ✅ Test crop completion callback receives correct bbox

4. **Visual Feedback**
   - ✅ Test overlay updates during drag
   - ✅ Test handles show resize cursor
   - ✅ Test crop region highlights correctly

**Mock Strategy**:
- Mock image metrics
- Mock mouse events
- Mock keyboard events (ESC)

---

### 4. Batch Labeling Dialog Component Tests

#### Test Suite: `tests/components/BatchLabelingDialog.test.tsx`

**Test Cases**:

1. **Dialog Rendering**
   - ✅ Test dialog opens when `open` prop is true
   - ✅ Test dialog closes when `open` prop is false
   - ✅ Test dialog renders all form fields
   - ✅ Test concept text input visible
   - ✅ Test confidence threshold slider visible
   - ✅ Test options checkboxes visible

2. **Form Interaction**
   - ✅ Test user can enter concept text
   - ✅ Test threshold slider updates value
   - ✅ Test checkboxes toggle options
   - ✅ Test form validation (required fields)

3. **Job Submission**
   - ✅ Test submit button triggers API call
   - ✅ Test job ID returned and stored
   - ✅ Test dialog shows job status
   - ✅ Test error handling for submission failure

4. **Job Status Tracking**
   - ✅ Test polling for job status
   - ✅ Test progress indicator updates
   - ✅ Test status message displays correctly
   - ✅ Test completion triggers annotation refresh
   - ✅ Test polling stops on completion/error

5. **Dialog Actions**
   - ✅ Test cancel button closes dialog
   - ✅ Test close button closes dialog
   - ✅ Test onClose callback called

**Mock Strategy**:
- Mock API client (`api/batch.ts`)
- Mock React Query hooks
- Mock polling mechanism

---

### 5. Mask Overlay Component Tests

#### Test Suite: `tests/components/MaskOverlay.test.tsx`

**Test Cases**:

1. **Component Rendering**
   - ✅ Test canvas renders correctly
   - ✅ Test canvas dimensions match image display size
   - ✅ Test mask renders on canvas

2. **Mask Decoding**
   - ✅ Test RLE string decoding
   - ✅ Test RLE array decoding
   - ✅ Test error handling for invalid RLE format
   - ✅ Test mask matches expected shape

3. **Mask Rendering**
   - ✅ Test mask drawn with correct color
   - ✅ Test mask opacity/transparency
   - ✅ Test mask coordinates scaled correctly
   - ✅ Test bounding box outline drawn (if provided)

4. **Image Metrics**
   - ✅ Test mask scales with image display size
   - ✅ Test coordinates converted from natural to display size
   - ✅ Test handles different aspect ratios

**Test Data**:
- Sample RLE encoded masks
- Various image metrics (natural size vs display size)
- Test masks with bounding boxes

---

### 6. Mask Decoder Utility Tests

#### Test Suite: `tests/utils/maskDecoder.test.ts`

**Test Cases**:

1. **RLE Decoding**
   - ✅ Test decodeRLE with space-separated string
   - ✅ Test decodeRLE with number array
   - ✅ Test decodeCounts generates correct boolean array
   - ✅ Test mask dimensions match height/width
   - ✅ Test error handling for invalid format

2. **Edge Cases**
   - ✅ Test empty RLE string/array
   - ✅ Test single pixel mask
   - ✅ Test full image mask
   - ✅ Test masks with gaps (alternating runs)

**Test Data**:
- Various RLE formats (string, array)
- Simple masks (small dimensions)
- Complex masks (large dimensions)

---

### 7. Annotation Canvas Integration Tests

#### Test Suite: `tests/components/AnnotationCanvas.test.tsx`

**Test Cases**:

1. **Image Rendering**
   - ✅ Test image loads and displays
   - ✅ Test image scaling (object-contain)
   - ✅ Test image metrics calculated correctly

2. **Annotation Rendering**
   - ✅ Test annotations rendered with MaskOverlay
   - ✅ Test multiple annotations rendered
   - ✅ Test annotation colors match label classes
   - ✅ Test annotations positioned correctly

3. **Crop Mode Integration**
   - ✅ Test crop mode disables regular drawing
   - ✅ Test crop mode shows CropTool component
   - ✅ Test onCropComplete callback triggered
   - ✅ Test onCropCancel callback triggered

4. **Interaction States**
   - ✅ Test "Select a label class" message shown
   - ✅ Test message hidden when class selected
   - ✅ Test message hidden in crop mode

**Mock Strategy**:
- Mock image loading
- Mock MaskOverlay component (or test with real component)
- Mock image URL builder

---

### 8. Labeler Page Integration Tests

#### Test Suite: `tests/pages/LabelerPage.test.tsx`

**Test Cases**:

1. **Page Layout**
   - ✅ Test three-column layout renders
   - ✅ Test label classes sidebar visible
   - ✅ Test image canvas visible
   - ✅ Test annotations sidebar visible

2. **Data Loading**
   - ✅ Test project data loads
   - ✅ Test dataset data loads
   - ✅ Test images load for dataset
   - ✅ Test annotations load for selected image
   - ✅ Test label classes load

3. **Image Navigation**
   - ✅ Test previous/next buttons navigate images
   - ✅ Test URL updates with imageId
   - ✅ Test buttons disabled at boundaries

4. **Concept Prompting Integration**
   - ✅ Test ConceptCommandBar integrated
   - ✅ Test annotations refresh after prompt
   - ✅ Test confidence threshold from project used

5. **Crop Exemplar Integration**
   - ✅ Test "Crop Exemplar" button activates crop mode
   - ✅ Test crop completion triggers API call
   - ✅ Test annotations refresh after exemplar prompt

6. **Batch Labeling Integration**
   - ✅ Test "Batch Label" button opens dialog
   - ✅ Test dialog configured with correct dataset
   - ✅ Test annotations refresh after batch completion

7. **Annotation Display**
   - ✅ Test annotations displayed with labels
   - ✅ Test confidence badges shown
   - ✅ Test concept text shown
   - ✅ Test AI-generated indicator shown
   - ✅ Test low-confidence highlighting

**Mock Strategy**:
- Mock all API calls
- Mock React Router (useParams, useSearchParams)
- Mock React Query hooks
- Mock all child components (or render with real components)

---

### 9. API Client Tests

#### Test Suite: `tests/api/concepts.test.ts`

**Test Cases**:

1. **promptImageWithText**
   - ✅ Test API call with correct URL
   - ✅ Test request body format
   - ✅ Test response parsing
   - ✅ Test error handling

2. **promptImageWithExemplar**
   - ✅ Test API call with crop bbox
   - ✅ Test request body format
   - ✅ Test response parsing

#### Test Suite: `tests/api/batch.test.ts`

**Test Cases**:

1. **createBatchJob**
   - ✅ Test API call with correct URL
   - ✅ Test request body format
   - ✅ Test job ID returned

2. **getBatchJobStatus**
   - ✅ Test API call with job ID
   - ✅ Test response parsing
   - ✅ Test status object structure

**Mock Strategy**:
- Mock fetch API
- Use MSW (Mock Service Worker) for API mocking

---

### 10. Type Tests

#### Test Suite: `tests/types.test.ts`

**Test Cases**:

1. **Type Definitions**
   - ✅ Test Annotation type includes SAM3 fields
   - ✅ Test Project type includes confidence_threshold
   - ✅ Test ConceptPromptResponse type structure
   - ✅ Test BatchJobStatus type structure

---

## Test Execution

### Running Tests

```bash
# Unit tests for components
npm test -- ConceptCommandBar.test.tsx
npm test -- ConfidenceIndicator.test.tsx

# All component tests
npm test -- components/

# All tests with coverage
npm test -- --coverage
```

### Coverage Report

```bash
npm test -- --coverage --coverageReporters=html
```

---

## Test Utilities & Setup

### Required Testing Libraries

```json
{
  "devDependencies": {
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "msw": "^2.0.0"
  }
}
```

### Test Setup File

Create `tests/setup.ts`:

```typescript
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
```

---

## Success Criteria

- ✅ All component tests pass
- ✅ All integration tests pass
- ✅ Code coverage ≥ 80% for components and utilities
- ✅ All user interactions tested
- ✅ Error handling tested for all error cases
- ✅ Accessibility tested (keyboard navigation, screen readers)

---

## Known Issues & Limitations

1. **Canvas Testing**: HTML5 Canvas is difficult to test
   - Use jsdom canvas mock
   - Test logic separately from rendering

2. **Image Loading**: Image loading in tests can be flaky
   - Mock image loading
   - Use test images with controlled loading

3. **API Mocking**: Real API calls in tests are slow
   - Use MSW for all API mocking
   - Mock all external dependencies

---

**Next**: See `test-plan-03-phase2-backend.md` for Phase 2 backend tests

