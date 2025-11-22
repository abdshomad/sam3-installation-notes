# Test Plan: Phase 3 Backend - Collaboration

## Overview

This document defines the test plan for Phase 3 backend components of the SAM 3 Labeling App. Phase 3 includes role-based access control (RBAC), user management, consensus voting, and enhanced export formats.

**Status**: Backend 60% Complete ⚠️  
**Target Coverage**: 80%+ code coverage

## Test Categories

### 1. User Model & Authentication Tests

#### Test Suite: `tests/unit/models/test_user.py`

**Test Cases**:

1. **User Model**
   - ✅ Test user creation with email, name, role
   - ✅ Test password hashing (bcrypt/argon2)
   - ✅ Test email uniqueness constraint
   - ✅ Test role validation (admin, reviewer, labeler)
   - ✅ Test password verification

2. **User Schema Validation**
   - ✅ Test `UserCreate` schema validation
   - ✅ Test `UserRead` schema excludes password
   - ✅ Test email format validation
   - ✅ Test password strength validation (if implemented)

---

### 2. Project Member Model Tests

#### Test Suite: `tests/unit/models/test_project_member.py`

**Test Cases**:

1. **ProjectMember Model**
   - ✅ Test project member creation with user_id, project_id, role
   - ✅ Test unique constraint on (user_id, project_id)
   - ✅ Test role validation (admin, reviewer, labeler)
   - ✅ Test cascade delete (user/project deletion)

2. **Project Member Schema**
   - ✅ Test `ProjectMemberCreate` schema validation
   - ✅ Test `ProjectMemberRead` schema includes user info

---

### 3. Authentication & Authorization Tests

#### Test Suite: `tests/integration/api/test_auth.py`

**Test Cases**:

1. **User Registration**
   - ⏳ Test `POST /users/register` (if implemented)
   - ⏳ Test password hashing on registration
   - ⏳ Test email uniqueness check
   - ⏳ Test validation errors for invalid input

2. **User Login**
   - ⏳ Test `POST /users/login` (if implemented)
   - ⏳ Test JWT token generation
   - ⏳ Test token refresh mechanism
   - ⏳ Test error handling for invalid credentials

3. **JWT Token Validation**
   - ⏳ Test token validation in `get_current_user()`
   - ⏳ Test token expiration handling
   - ⏳ Test token refresh handling
   - ⏳ Test error handling for invalid tokens

**Note**: JWT authentication implementation is pending (foundation ready in `app/api/deps.py`)

---

### 4. RBAC Permission Tests

#### Test Suite: `tests/integration/api/test_rbac.py`

**Test Cases**:

1. **Role-Based Route Protection**
   - ✅ Test `require_role()` decorator
   - ✅ Test admin can access all routes
   - ✅ Test reviewer can access reviewer routes
   - ✅ Test labeler can access labeler routes
   - ✅ Test unauthorized access returns 403

2. **Project Member Checks**
   - ✅ Test `require_project_member()` decorator
   - ✅ Test project member can access project resources
   - ✅ Test non-member access denied (403)
   - ✅ Test role hierarchy (admin > reviewer > labeler)

3. **Permission Scenarios**
   - ✅ Test admin can access all projects
   - ✅ Test reviewer can review but not delete
   - ✅ Test labeler can annotate but not review
   - ✅ Test project member role overrides

**Mock Strategy**:
- Mock `get_current_user()` to return test users
- Test with different user roles
- Test with different project memberships

---

### 5. User Management API Tests

#### Test Suite: `tests/integration/api/test_users.py`

**Test Cases**:

1. **User CRUD Operations**
   - ✅ Test `POST /users` creates user
   - ✅ Test `GET /users` lists users (with pagination if implemented)
   - ✅ Test `GET /users/{id}` returns user details
   - ✅ Test `PATCH /users/{id}` updates user
   - ✅ Test `DELETE /users/{id}` deletes user

2. **User Search & Filtering**
   - ✅ Test filtering by role
   - ✅ Test searching by email/name
   - ✅ Test pagination works correctly

3. **Authorization Checks**
   - ✅ Test only admin can create users
   - ✅ Test users can update own profile
   - ✅ Test only admin can delete users
   - ✅ Test error handling for unauthorized access

**Test Setup**:
- Use FastAPI TestClient
- Create test users with different roles
- Mock authentication for tests

---

### 6. Project Member Management API Tests

#### Test Suite: `tests/integration/api/test_project_members.py`

**Test Cases**:

1. **Project Member CRUD**
   - ✅ Test `POST /projects/{id}/members` adds member
   - ✅ Test `GET /projects/{id}/members` lists members
   - ✅ Test `PATCH /projects/{id}/members/{user_id}` updates role
   - ✅ Test `DELETE /projects/{id}/members/{user_id}` removes member

2. **Member Role Assignment**
   - ✅ Test assigning admin role
   - ✅ Test assigning reviewer role
   - ✅ Test assigning labeler role
   - ✅ Test role update changes permissions

3. **Authorization Checks**
   - ✅ Test only project admin can add members
   - ✅ Test only project admin can change roles
   - ✅ Test only project admin can remove members
   - ✅ Test error handling for unauthorized access

4. **Edge Cases**
   - ✅ Test adding duplicate member returns error
   - ✅ Test removing non-existent member returns error
   - ✅ Test removing last admin returns error (if validation exists)

**Test Setup**:
- Create test projects and users
- Test with different project roles
- Mock authentication

---

### 7. Consensus Service Tests

#### Test Suite: `tests/unit/services/test_consensus_service.py`

**Test Cases**:

1. **IoU Calculation**
   - ✅ Test IoU calculated correctly between two masks
   - ✅ Test IoU = 1.0 for identical masks
   - Test IoU = 0.0 for non-overlapping masks
   - Test IoU handles different mask sizes

2. **Consensus Calculation**
   - ✅ Test consensus score calculated for multiple annotations
   - ✅ Test auto-merge threshold (>0.85)
   - ✅ Test flag for super reviewer (<0.85)
   - ✅ Test consensus handles 2 annotators
   - ✅ Test consensus handles 3+ annotators

3. **Auto-Merge Logic**
   - ✅ Test annotations auto-merged when IoU > threshold
   - ✅ Test merged annotation combines masks
   - ✅ Test merged annotation metadata preserved
   - ✅ Test flag set correctly for review

4. **Edge Cases**
   - ✅ Test consensus with no annotations
   - ✅ Test consensus with single annotation
   - ✅ Test consensus with all identical annotations
   - ✅ Test consensus with all different annotations

**Mock Strategy**:
- Mock mask IoU calculation
- Test with synthetic masks
- Test with various IoU values

---

### 8. Consensus API Tests

#### Test Suite: `tests/integration/api/test_consensus.py`

**Test Cases**:

1. **Task Assignment**
   - ✅ Test `POST /consensus/tasks/{task_id}/assign` assigns to multiple annotators
   - ✅ Test multiple users receive same task
   - ✅ Test error handling for non-existent task

2. **Consensus Status**
   - ✅ Test `GET /consensus/images/{image_id}/status` returns status
   - ✅ Test status includes annotator count
   - ✅ Test status includes consensus score
   - ✅ Test status includes merge status

3. **Auto-Merge**
   - ✅ Test `POST /consensus/images/{image_id}/merge` auto-merges annotations
   - ✅ Test merged annotation created
   - ✅ Test original annotations marked as merged
   - ✅ Test error handling for no consensus

4. **Authorization Checks**
   - ✅ Test only reviewer/admin can view consensus status
   - ✅ Test only reviewer/admin can merge annotations
   - ✅ Test annotators cannot merge own annotations

**Test Setup**:
- Create test tasks with multiple annotations
- Create test users with different roles
- Mock consensus service

---

### 9. YOLO Export Service Tests

#### Test Suite: `tests/unit/services/exporters/test_yolo_exporter.py`

**Test Cases**:

1. **YOLO Format Export**
   - ✅ Test `build_yolo_export()` generates correct format
   - ✅ Test text-to-integer class ID mapping
   - ✅ Test normalized bounding box format (x_center, y_center, width, height)
   - ✅ Test text file per image format
   - ✅ Test ZIP file generation

2. **Ontology Mapping**
   - ✅ Test concept text mapped to class ID
   - ✅ Test multiple concepts mapped correctly
   - ✅ Test mapping parameter handling
   - ✅ Test error handling for unmapped concepts

3. **File Structure**
   - ✅ Test images directory structure
   - ✅ Test labels directory structure
   - ✅ Test class names file generated
   - ✅ Test ZIP contains all files

**Test Suite**: `tests/integration/api/test_export_yolo.py`

**Test Cases**:

1. **YOLO Export API**
   - ✅ Test `GET /export/{project_id}/yolo` returns ZIP file
   - ✅ Test ZIP file format correct
   - ✅ Test ontology mapping parameter works
   - ✅ Test error handling for projects without annotations

---

### 10. Integration Tests

#### Test Suite: `tests/integration/test_collaboration_workflow.py`

**Test Cases**:

1. **Multi-User Annotation Workflow**
   - ✅ Create project with multiple members
   - ✅ Assign task to multiple annotators
   - ✅ Each annotator creates annotations
   - ✅ Consensus status checked
   - ✅ Annotations auto-merged (if IoU > threshold)
   - ✅ Super reviewer flags reviewed (if IoU < threshold)

2. **RBAC Workflow**
   - ✅ Admin creates project and adds members
   - ✅ Reviewer reviews annotations
   - ✅ Labeler annotates images
   - ✅ Unauthorized access denied correctly

3. **User Management Workflow**
   - ✅ Admin creates user
   - ✅ User logs in (when implemented)
   - ✅ User assigned to project
   - ✅ User accesses project resources
   - ✅ User removed from project
   - ✅ User access denied after removal

**Test Setup**:
- Full test environment (database, API, services)
- Multiple test users with different roles
- Test projects with members
- Mock authentication (or implement JWT for tests)

---

## Test Execution

### Running Tests

```bash
# Unit tests
pytest tests/unit/models/test_user.py -v
pytest tests/unit/services/test_consensus_service.py -v

# Integration tests
pytest tests/integration/api/test_users.py -v
pytest tests/integration/api/test_project_members.py -v
pytest tests/integration/api/test_rbac.py -v

# All Phase 3 backend tests
pytest tests/unit/models/test_user* tests/integration/api/test_users* tests/integration/api/test_project_members* tests/integration/api/test_consensus* tests/integration/api/test_rbac* -v --cov=app/services/consensus_service --cov=app/api/routes/users --cov=app/api/routes/project_members
```

### Coverage Report

```bash
pytest --cov=app/services/consensus_service --cov=app/api/routes/users --cov=app/api/routes/project_members --cov=app/api/routes/consensus --cov=app/api/deps --cov-report=html
```

---

## Test Data Requirements

### Test Users
- Admin user (full access)
- Reviewer user (review access)
- Labeler user (annotation access)
- Multiple users for consensus testing

### Test Projects
- Projects with different member configurations
- Projects with tasks assigned to multiple annotators
- Projects with consensus annotations

### Mock Data
- Mock authentication tokens (JWT)
- Test consensus scenarios (various IoU values)

---

## Success Criteria

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Code coverage ≥ 80% for collaboration services and API routes
- ✅ All RBAC permission checks tested
- ✅ Consensus voting logic tested thoroughly
- ✅ Error handling tested for all error cases
- ⏳ JWT authentication implemented and tested (pending)

---

## Known Issues & Limitations

1. **JWT Authentication**: JWT implementation is pending
   - Foundation ready in `app/api/deps.py`
   - `get_current_user()` currently returns None
   - Need to implement token generation, validation, refresh

2. **Password Hashing**: Password hashing library needs to be selected
   - Recommend bcrypt or argon2
   - Need to implement password verification

3. **Token Refresh**: Token refresh mechanism not yet implemented
   - Need refresh token endpoint
   - Need token refresh logic

4. **Consensus Edge Cases**: Some edge cases may need additional handling
   - Annotations from different frames (should be separate)
   - Annotations from different objects (should not be merged)
   - Partial consensus (some annotators agree, others don't)

---

**Next**: See `test-plan-06-phase3-frontend.md` for Phase 3 frontend tests (placeholder)

