# Test Plan: Phase 3 Frontend - Collaboration

## Overview

This document defines the test plan for Phase 3 frontend components of the SAM 3 Labeling App. Phase 3 includes RBAC UI components, consensus UI, user management UI, and review queue UI.

**Status**: Frontend 0% Complete (Not Yet Implemented) ⏳  
**Target Coverage**: 80%+ code coverage (when implemented)

## Implementation Status

**Note**: These frontend components have not yet been implemented. This test plan is prepared for when implementation begins.

**Backend Status**: ⚠️ 60% Complete (see `test-plan-05-phase3-backend.md`)

**Frontend Components to Implement**:
- ❌ RBAC UI Components (3.2.4)
- ❌ Consensus UI (3.1.4)
- ❌ Review Queue UI (3.6.3)
- ❌ User Management UI
- ❌ Project Member Invitation System

---

## Test Categories (Planned)

### 1. Authentication & Login Component Tests

#### Test Suite: `tests/components/LoginForm.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Login Form Rendering**
   - ⏳ Test login form renders correctly
   - ⏳ Test email input field visible
   - ⏳ Test password input field visible
   - ⏳ Test submit button visible
   - ⏳ Test "Forgot Password" link (if implemented)

2. **User Input**
   - ⏳ Test user can enter email
   - ⏳ Test user can enter password
   - ⏳ Test password field masks input
   - ⏳ Test form validation (required fields, email format)

3. **Login Submission**
   - ⏳ Test submit button triggers login API call
   - ⏳ Test loading state during login
   - ⏳ Test success redirects to dashboard
   - ⏳ Test error message displayed on failure
   - ⏳ Test JWT token stored in localStorage/cookies

4. **Token Refresh**
   - ⏳ Test token refresh on expiry
   - ⏳ Test refresh token stored correctly
   - ⏳ Test automatic logout on refresh failure

**Mock Strategy** (Planned):
- Mock login API call
- Mock React Router (navigation)
- Mock token storage

---

### 2. Role Guard Component Tests

#### Test Suite: `tests/components/RoleGuard.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Role-Based Rendering**
   - ⏳ Test admin users see admin content
   - ⏳ Test reviewer users see reviewer content
   - ⏳ Test labeler users see labeler content
   - ⏳ Test unauthorized users see fallback/redirect

2. **Multiple Roles**
   - ⏳ Test component accepts array of allowed roles
   - ⏳ Test user with any allowed role can access
   - ⏳ Test user without allowed role cannot access

3. **Project Member Checks**
   - ⏳ Test project member can access project resources
   - ⏳ Test non-member sees access denied
   - ⏳ Test project role hierarchy (admin > reviewer > labeler)

**Mock Strategy** (Planned):
- Mock user context/state
- Mock project member check

---

### 3. User Management UI Tests

#### Test Suite: `tests/pages/UserManagementPage.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **User List Display**
   - ⏳ Test user list displays all users
   - ⏳ Test user information shown (name, email, role)
   - ⏳ Test user filtering by role
   - ⏳ Test user search by email/name
   - ⏳ Test pagination works

2. **User Creation**
   - ⏳ Test "Create User" button opens modal
   - ⏳ Test user creation form renders
   - ⏳ Test form validation (email, password, role)
   - ⏳ Test user created successfully
   - ⏳ Test error handling for duplicate email

3. **User Editing**
   - ⏳ Test edit button opens edit modal
   - ⏳ Test user information pre-filled
   - ⏳ Test user updated successfully
   - ⏳ Test role change updates permissions

4. **User Deletion**
   - ⏳ Test delete button shows confirmation
   - ⏳ Test user deleted successfully
   - ⏳ Test error handling for deletion failure

5. **Authorization**
   - ⏳ Test only admin can access user management
   - ⏳ Test non-admin users redirected/denied

**Mock Strategy** (Planned):
- Mock user management API
- Mock React Query hooks
- Mock user context

---

### 4. Project Member Management UI Tests

#### Test Suite: `tests/components/ProjectMemberList.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Member List Display**
   - ⏳ Test member list displays all project members
   - ⏳ Test member information shown (name, email, role)
   - ⏳ Test member role badges displayed

2. **Adding Members**
   - ⏳ Test "Add Member" button opens modal
   - ⏳ Test user search/select functionality
   - ⏳ Test role selection
   - ⏳ Test member added successfully
   - ⏳ Test error handling for duplicate member

3. **Updating Member Role**
   - ⏳ Test role dropdown/selector visible
   - ⏳ Test role updated successfully
   - ⏳ Test role change reflects immediately

4. **Removing Members**
   - ⏳ Test remove button shows confirmation
   - ⏳ Test member removed successfully
   - ⏳ Test error handling for removal failure

5. **Authorization**
   - ⏳ Test only project admin can manage members
   - ⏳ Test non-admin users cannot see manage buttons

**Mock Strategy** (Planned):
- Mock project member API
- Mock user search API
- Mock React Query hooks

---

### 5. Consensus UI Component Tests

#### Test Suite: `tests/components/ConsensusView.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Annotation Comparison**
   - ⏳ Test side-by-side annotation display
   - ⏳ Test multiple annotator annotations shown
   - ⏳ Test annotations overlaid/compared visually
   - ⏳ Test IoU score displayed

2. **Consensus Status**
   - ⏳ Test consensus score displayed
   - ⏳ Test auto-merge status shown
   - ⏳ Test flag status shown (if IoU < threshold)
   - ⏳ Test annotator count displayed

3. **Auto-Merge Action**
   - ⏳ Test "Merge" button visible when IoU > threshold
   - ⏳ Test merge confirmation dialog
   - ⏳ Test annotations merged successfully
   - ⏳ Test merged annotation displayed

4. **Super Reviewer Interface**
   - ⏳ Test flag highlighted when IoU < threshold
   - ⏳ Test reviewer can select best annotation
   - ⏳ Test reviewer can create new annotation
   - ⏳ Test reviewer decision saved

5. **Navigation**
   - ⏳ Test navigate to next flagged annotation
   - ⏳ Test navigate to previous flagged annotation
   - ⏳ Test progress indicator (X of Y flagged)

**Mock Strategy** (Planned):
- Mock consensus API
- Mock annotation data
- Mock mask rendering component

---

### 6. Review Queue UI Tests

#### Test Suite: `tests/pages/ReviewQueuePage.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Queue Display**
   - ⏳ Test queue displays pending reviews
   - ⏳ Test tasks filtered by status
   - ⏳ Test tasks sorted by priority/date
   - ⏳ Test pagination works

2. **Task Filtering**
   - ⏳ Test filter by project
   - ⏳ Test filter by reviewer
   - ⏳ Test filter by status (pending, approved, rejected)
   - ⏳ Test filter by date range

3. **Task Assignment**
   - ⏳ Test assign task to reviewer
   - ⏳ Test assign multiple tasks
   - ⏳ Test task assignment updates queue

4. **Review Actions**
   - ⏳ Test approve button approves task
   - ⏳ Test reject button rejects task
   - ⏳ Test comment field for feedback
   - ⏳ Test review decision saved

5. **Task Details**
   - ⏳ Test click task opens details view
   - ⏳ Test annotations displayed in details
   - ⏳ Test task metadata shown (annotator, date, etc.)

**Mock Strategy** (Planned):
- Mock review queue API
- Mock task assignment API
- Mock React Query hooks

---

### 7. Project Settings UI Tests

#### Test Suite: `tests/pages/ProjectSettingsPage.test.tsx` (Planned)

**Test Cases** (To be implemented):

1. **Project Information**
   - ⏳ Test project name displayed
   - ⏳ Test project description displayed
   - ⏳ Test confidence threshold displayed
   - ⏳ Test project settings editable

2. **Confidence Threshold**
   - ⏳ Test threshold slider/input visible
   - ⏳ Test threshold updated successfully
   - ⏳ Test threshold validation (0.0-1.0)

3. **Member Management Integration**
   - ⏳ Test member management section visible
   - ⏳ Test "Manage Members" button links to member page

4. **Authorization**
   - ⏳ Test only project admin can edit settings
   - ⏳ Test non-admin users see read-only view

**Mock Strategy** (Planned):
- Mock project settings API
- Mock React Query hooks

---

### 8. API Client Tests

#### Test Suite: `tests/api/users.test.ts` (Planned)

**Test Cases** (To be implemented):

1. **User API**
   - ⏳ Test login API call
   - ⏳ Test register API call (if implemented)
   - ⏳ Test getCurrentUser API call
   - ⏳ Test refreshToken API call

#### Test Suite: `tests/api/projectMembers.test.ts` (Planned)

**Test Cases** (To be implemented):

1. **Project Member API**
   - ⏳ Test getProjectMembers API call
   - ⏳ Test addProjectMember API call
   - ⏳ Test updateProjectMemberRole API call
   - ⏳ Test removeProjectMember API call

#### Test Suite: `tests/api/consensus.test.ts` (Planned)

**Test Cases** (To be implemented):

1. **Consensus API**
   - ⏳ Test getConsensusStatus API call
   - ⏳ Test mergeConsensusAnnotations API call
   - ⏳ Test getFlaggedAnnotations API call

**Mock Strategy** (Planned):
- Mock fetch API
- Use MSW (Mock Service Worker) for API mocking

---

## Test Execution (When Implemented)

### Running Tests

```bash
# Component tests (when implemented)
npm test -- LoginForm.test.tsx
npm test -- RoleGuard.test.tsx

# All collaboration frontend tests (when implemented)
npm test -- components/RoleGuard* tests/pages/UserManagementPage* tests/pages/ReviewQueuePage*

# All tests with coverage (when implemented)
npm test -- --coverage
```

---

## Implementation Checklist

Before starting implementation, ensure:

- [ ] Backend API endpoints fully tested (see `test-plan-05-phase3-backend.md`)
- [ ] JWT authentication implemented and working
- [ ] Authentication context/provider implemented (React Context or Zustand)
- [ ] Role-based routing strategy defined
- [ ] Permission checking utilities created

---

## Success Criteria (When Implemented)

- ✅ All component tests pass
- ✅ All integration tests pass
- ✅ Code coverage ≥ 80% for collaboration components
- ✅ All user interactions tested
- ✅ RBAC enforced correctly in UI
- ✅ Error handling tested for all error cases
- ✅ Accessibility tested (keyboard navigation, screen readers)
- ✅ Token refresh works correctly
- ✅ Logout functionality works correctly

---

## Known Challenges (Future)

1. **Authentication State**: Managing auth state across app can be complex
   - Use React Context or Zustand for global auth state
   - Test auth state persistence (localStorage/cookies)

2. **Role-Based UI**: Conditionally rendering based on roles requires careful testing
   - Test all role combinations
   - Test role changes update UI correctly

3. **Consensus Visualization**: Comparing multiple annotations visually is complex
   - Test mask overlay rendering
   - Test IoU visualization
   - Performance testing for multiple annotations

4. **Real-time Updates**: Review queue may need real-time updates
   - Test WebSocket/polling for queue updates
   - Test optimistic UI updates

---

**Note**: This test plan will be updated as implementation progresses.  
**Next**: See `test-plan-07-integration.md` for cross-phase integration tests

