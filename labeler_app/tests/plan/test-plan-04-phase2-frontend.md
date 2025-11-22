# Test Plan: Phase 2 Frontend - Video & Tracking

## Overview

This document defines the test plan for Phase 2 frontend components of the SAM 3 Labeling App. Phase 2 includes video player integration, masklet timeline component, and video annotation UI.

**Status**: Frontend 0% Complete (Not Yet Implemented) ⏳  
**Target Coverage**: 80%+ code coverage (when implemented)

## Implementation Status

**Note**: These frontend components have not yet been implemented. This test plan is prepared for when implementation begins.

**Backend Status**: ✅ 100% Complete (see `test-plan-03-phase2-backend.md`)

**Frontend Components to Implement**:
- ❌ Masklet Timeline Component (2.3.1)
- ❌ Video Player Integration (2.3.2)
- ❌ Masklet Interaction Logic (2.3.3)
- ❌ Correction UI & Feedback (2.4.3)
- ❌ Track Management UI (2.5.3)
- ❌ Memory Bank Indicators (2.6.2)

---

## Test Categories (Planned)

### 1. Video Player Component Tests

#### Test Suite: `tests/components/VideoPlayer.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Video Player Rendering**
   - ⏳ Test video player loads and displays video
   - ⏳ Test HLS video streaming works
   - ⏳ Test video player controls visible
   - ⏳ Test play/pause functionality
   - ⏳ Test volume control
   - ⏳ Test fullscreen mode

2. **Frame Navigation**
   - ⏳ Test frame scrubbing (seeking to specific frame)
   - ⏳ Test frame counter displays correctly
   - ⏳ Test previous/next frame buttons
   - ⏳ Test keyboard shortcuts for frame navigation

3. **Video Loading**
   - ⏳ Test loading state during video load
   - ⏳ Test error handling for failed video load
   - ⏳ Test error handling for unsupported format

**Mock Strategy** (Planned):
- Mock video player library (e.g., Video.js, Plyr)
- Mock HLS.js for HLS streaming
- Mock video loading events

---

### 2. Masklet Timeline Component Tests

#### Test Suite: `tests/components/MaskletTimeline.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Timeline Rendering**
   - ⏳ Test timeline renders with correct duration
   - ⏳ Test masklet tracks displayed
   - ⏳ Test frame markers displayed
   - ⏳ Test current frame indicator visible
   - ⏳ Test zoom in/out functionality

2. **Masklet Visualization**
   - ⏳ Test masklets rendered as colored bars
   - ⏳ Test different objects have different colors
   - ⏳ Test masklet gaps (missing frames) displayed
   - ⏳ Test masklet duration displayed

3. **Timeline Interaction**
   - ⏳ Test clicking timeline seeks to frame
   - ⏳ Test dragging timeline scrubs video
   - ⏳ Test selecting masklet highlights it
   - ⏳ Test keyboard shortcuts for timeline navigation

4. **Object Selection**
   - ⏳ Test clicking masklet selects object
   - ⏳ Test multiple masklet selection
   - ⏳ Test selected masklets highlighted

**Mock Strategy** (Planned):
- Mock timeline data (masklets, frames)
- Mock canvas rendering (for timeline visualization)

---

### 3. Masklet Interaction Logic Tests

#### Test Suite: `tests/hooks/useMaskletInteraction.test.ts` (Planned)

**Test Cases** (To be implemented):

1. **Masklet Selection**
   - ⏳ Test selectMasklet updates selected state
   - ⏳ Test deselectMasklet clears selection
   - ⏳ Test multiple masklet selection/deselection

2. **Frame Navigation**
   - ⏳ Test goToFrame updates current frame
   - ⏳ Test goToNextFrame increments frame
   - ⏳ Test goToPreviousFrame decrements frame
   - ⏳ Test frame bounds checking

3. **Masklet Operations**
   - ⏳ Test deleteMasklet removes masklet
   - ⏳ Test splitMasklet splits at frame
   - ⏳ Test mergeMasklets combines masklets

**Mock Strategy** (Planned):
- Mock API calls (video tracking API)
- Mock state management (Zustand store)

---

### 4. Video Annotation Page Tests

#### Test Suite: `tests/pages/VideoAnnotationPage.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Page Layout**
   - ⏳ Test video player visible
   - ⏳ Test masklet timeline visible
   - ⏳ Test annotation sidebar visible
   - ⏳ Test toolbar visible

2. **Video Session Management**
   - ⏳ Test tracking session started on mount
   - ⏳ Test session closed on unmount
   - ⏳ Test session status displayed

3. **Prompting Integration**
   - ⏳ Test text prompt adds prompt to current frame
   - ⏳ Test point prompt adds prompt
   - ⏳ Test box prompt adds prompt
   - ⏳ Test obj_id assignment

4. **Tracking Integration**
   - ⏳ Test track forward button triggers tracking
   - ⏳ Test track backward button triggers tracking
   - ⏳ Test tracking progress displayed
   - ⏳ Test masklets updated after tracking

5. **Masklet Display**
   - ⏳ Test masklets rendered on video frames
   - ⏳ Test masklet colors match objects
   - ⏳ Test masklet opacity/configurable
   - ⏳ Test bounding boxes displayed

---

### 5. Correction UI Component Tests

#### Test Suite: `tests/components/CorrectionTool.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Mask Correction**
   - ⏳ Test correction tool activates on masklet click
   - ⏳ Test user can edit mask on canvas
   - ⏳ Test correction applied to frame
   - ⏳ Test propagation direction selected
   - ⏳ Test propagation range configured

2. **Correction Feedback**
   - ⏳ Test loading state during propagation
   - ⏳ Test success message after correction
   - ⏳ Test error handling for correction failure
   - ⏳ Test masklets updated after correction

**Mock Strategy** (Planned):
- Mock mask editing canvas
- Mock API calls for correction propagation

---

### 6. Track Management UI Tests

#### Test Suite: `tests/components/TrackManager.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Track List Display**
   - ⏳ Test track list displays all tracks
   - ⏳ Test track information shown (ID, frame range, object count)
   - ⏳ Test selected track highlighted

2. **Track Merging**
   - ⏳ Test merge tracks button visible when multiple selected
   - ⏳ Test merge confirmation dialog
   - ⏳ Test tracks merged successfully
   - ⏳ Test merged track displayed

3. **Track Splitting**
   - ⏳ Test split track button visible when track selected
   - ⏳ Test split frame selection
   - ⏳ Test track split successfully
   - ⏳ Test split tracks displayed

**Mock Strategy** (Planned):
- Mock API calls for track operations
- Mock state updates

---

### 7. Memory Bank Indicators Tests

#### Test Suite: `tests/components/MemoryBankIndicator.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Memory Bank Display**
   - ⏳ Test memory bank context displayed
   - ⏳ Test keyframes highlighted in timeline
   - ⏳ Test memory snapshots shown
   - ⏳ Test active frames indicated

2. **Keyframe Management**
   - ⏳ Test mark keyframe button
   - ⏳ Test unmark keyframe button
   - ⏳ Test keyframes persist in timeline

**Mock Strategy** (Planned):
- Mock memory bank API responses
- Mock timeline component

---

### 8. API Client Tests

#### Test Suite: `tests/api/videoTracking.test.ts` (Planned)

**Test Cases** (To be implemented):

1. **Session Management API**
   - ⏳ Test startSession API call
   - ⏳ Test getSessionStatus API call
   - ⏳ Test closeSession API call

2. **Tracking API**
   - ⏳ Test addPrompt API call
   - ⏳ Test trackObjects API call (streaming)
   - ⏳ Test correctMask API call

3. **Track Management API**
   - ⏳ Test mergeTracks API call
   - ⏳ Test splitTrack API call

**Mock Strategy** (Planned):
- Mock fetch API
- Use MSW (Mock Service Worker) for API mocking
- Mock streaming responses

---

## Test Execution (When Implemented)

### Running Tests

```bash
# Component tests (when implemented)
npm test -- VideoPlayer.test.tsx
npm test -- MaskletTimeline.test.tsx

# All video frontend tests (when implemented)
npm test -- components/Video* tests/pages/VideoAnnotationPage*

# All tests with coverage (when implemented)
npm test -- --coverage
```

---

## Implementation Checklist

Before starting implementation, ensure:

- [ ] Backend API endpoints fully tested (see `test-plan-03-phase2-backend.md`)
- [ ] Video player library selected (Video.js, Plyr, or custom)
- [ ] HLS.js integrated for HLS streaming
- [ ] Canvas/mask rendering library selected for masklet display
- [ ] State management strategy defined (Zustand store for video state)

---

## Success Criteria (When Implemented)

- ✅ All component tests pass
- ✅ All integration tests pass
- ✅ Code coverage ≥ 80% for video components
- ✅ All user interactions tested
- ✅ Video streaming works reliably
- ✅ Masklet rendering performs well (< 60fps)
- ✅ Error handling tested for all error cases
- ✅ Accessibility tested (keyboard navigation, screen readers)

---

## Known Challenges (Future)

1. **Video Streaming**: HLS streaming can be complex to test
   - Use mock HLS.js for unit tests
   - Test with real videos for integration tests

2. **Canvas Performance**: Rendering many masklets may be slow
   - Performance testing required
   - Consider WebGL for complex rendering

3. **Real-time Updates**: Streaming API responses require special handling
   - Test streaming response parsing
   - Test reconnection on connection loss

4. **Large Videos**: Long videos may have performance issues
   - Test with videos of various lengths
   - Optimize rendering for large frame counts

---

**Note**: This test plan will be updated as implementation progresses.  
**Next**: See `test-plan-05-phase3-backend.md` for Phase 3 backend tests

