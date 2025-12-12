# API Improvements: Core Identity, Access & Organization (F-001)

This document outlines proposed improvements to the F-001 API specification for better RESTful design, consistency, and usability.

---

## 1. Soft Delete Endpoints - Use DELETE Method

### 1.1 Family Soft Delete

**Existing:**
- `PATCH /v1/families/{family_id}/soft-delete`

**Improvement:**
- `DELETE /v1/families/{family_id}`

**Rationale:** DELETE method is more semantically correct for deletion operations, even if it's a soft delete. The `/soft-delete` suffix is redundant since the behavior is defined by business logic.

**Changes:**
- Method changes from PATCH to DELETE
- Path simplified from `/v1/families/{family_id}/soft-delete` to `/v1/families/{family_id}`
- Request body: None (same as before)
- Response: Same structure
- Authorization: SuperAdmin only (unchanged)
- ETag validation: Still required via `If-Match` header

---

### 1.2 User Soft Delete

**Existing:**
- `PATCH /v1/families/{family_id}/users/{user_id}/soft-delete`

**Improvement:**
- `DELETE /v1/families/{family_id}/users/{user_id}`

**Rationale:** Consistent with family soft delete improvement. DELETE method is more RESTful for deletion operations.

**Changes:**
- Method changes from PATCH to DELETE
- Path simplified from `/v1/families/{family_id}/users/{user_id}/soft-delete` to `/v1/families/{family_id}/users/{user_id}`
- Request body: None (same as before)
- Response: Same structure
- Authorization: SuperAdmin or FamilyAdmin (unchanged, cannot delete self)
- ETag validation: Still required via `If-Match` header

---

## 2. Unified Invitation Endpoint

**Existing:**
- `POST /v1/invite/families/{family_id}/users/`

**Improvement:**
- `POST /v1/invite`

**Rationale:** Single unified endpoint allows both SuperAdmin and FamilyAdmin to invite users. SuperAdmin can specify any family_id (or null for creating SuperAdmin users), while FamilyAdmin can only use their own family_id.

**Changes:**
- Path changed from `/v1/invite/families/{family_id}/users/` to `/v1/invite`
- Removed `family_id` from path parameters
- Request body now includes `family_id` (nullable):
  ```json
  {
    "email": "user@example.com",
    "family_id": "660e8400-e29b-41d4-a716-446655440000",  // null for SuperAdmin creation
    "role_id": "990e8400-e29b-41d4-a716-446655440000"
  }
  ```
- Authorization logic:
  - SuperAdmin: Can set any `family_id` or `null` (for SuperAdmin user creation)
  - FamilyAdmin: Can only set their own `family_id` (from JWT token), cannot set `null`
  - Server validates `family_id` matches token's `family_id` for FamilyAdmin
- Response: Same structure (includes family_id, role_id)

---

## 3. Invitation Validation - Path Parameter

**Existing:**
- `GET /v1/invitations/validate?token=abc123`

**Improvement:**
- `GET /v1/invitations/{token}`

**Rationale:** Token as path parameter is more RESTful and cleaner than query parameter. Follows standard REST resource pattern.

**Changes:**
- Path changed from `/v1/invitations/validate` to `/v1/invitations/{token}`
- Token moved from query parameter to path parameter
- Query schema class no longer needed (token is path parameter)
- Response: Same structure
- Authentication: Still public (no authentication required)

---

## 4. Invitation Activation - Path Parameter

**Existing:**
- `POST /v1/invitations/activate` (with token in body)

**Improvement:**
- `POST /v1/invitations/activate/{token}`

**Rationale:** Token in path parameter is more consistent with validation endpoint and cleaner API design.

**Changes:**
- Path changed from `/v1/invitations/activate` to `/v1/invitations/activate/{token}`
- Token moved from request body to path parameter
- Request body now only contains:
  ```json
  {
    "name": "John Doe",
    "password": "SecurePass123!"
  }
  ```
- Response: Same structure
- Authentication: Still public (no authentication required)

---

## 5. User Profile Management - Use User ID

### 5.1 Get User Profile

**Existing:**
- `GET /v1/users/me`

**Improvement:**
- `GET /v1/users/{user_id}`

**Rationale:** More flexible API design. Users can view their own profile by passing their user_id, and SuperAdmin/FamilyAdmin can view other users' profiles using the same endpoint.

**Changes:**
- Path changed from `/v1/users/me` to `/v1/users/{user_id}`
- Authorization logic:
  - Users can access their own profile (`user_id` matches JWT `sub`)
  - SuperAdmin can access any user's profile
  - FamilyAdmin can access users in their own family only
  - Member can only access their own profile
- Response: Same structure
- ETag validation: Still supported via `If-None-Match` header

---

### 5.2 Update User Profile

**Existing:**
- `PATCH /v1/users/me`

**Improvement:**
- `PATCH /v1/users/{user_id}`

**Rationale:** Consistent with GET endpoint. Allows users to update their own profile and SuperAdmin/FamilyAdmin to update other users' profiles.

**Changes:**
- Path changed from `/v1/users/me` to `/v1/users/{user_id}`
- Authorization logic:
  - Users can update their own profile (`user_id` matches JWT `sub`)
  - SuperAdmin can update any user's profile
  - FamilyAdmin can update users in their own family only
  - Member can only update their own profile
- Request body: Same (only `name` field)
- Response: Same structure
- ETag validation: Still required via `If-Match` header

---

## 6. Password Change - Use PATCH Method

**Existing:**
- `POST /v1/users/me/password/change`

**Improvement:**
- `PATCH /v1/users/{user_id}` (with password in body)

**Rationale:** Password change is an update operation, so PATCH is more appropriate than POST. Consolidates profile updates into a single endpoint.

**Changes:**
- Endpoint consolidated into `PATCH /v1/users/{user_id}`
- Request body now supports both name and password updates:
  ```json
  {
    "name": "John Doe Updated",  // optional
    "password": "NewSecurePass456!"  // optional, requires current_password
  }
  ```
- When updating password, include `current_password`:
  ```json
  {
    "password": "NewSecurePass456!",
    "current_password": "OldSecurePass123!"
  }
  ```
- Authorization: Same as profile update (users can change own password, SuperAdmin/FamilyAdmin can change others)
- Response: Same structure as profile update
- Password validation: Same strong password policy applies

**Alternative Approach (if keeping separate endpoint):**
- `PATCH /v1/users/{user_id}/password` (if password change should remain separate from profile update)

---

## 7. New Endpoints

### 7.1 Resend Invitation

**Add:**
- `POST /v1/invite/resend`

**Purpose:** Resend invitation email to a user with PendingActivation status.

**Request Body:**
```json
{
  "user_id": "770e8400-e29b-41d4-a716-446655440000"
}
```

**Authorization:**
- SuperAdmin: Can resend invitation for any user
- FamilyAdmin: Can resend invitation for users in their own family only

**Response:**
```json
{
  "data": {
    "user_id": "770e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "invite_token": "new_abc123xyz789def456",
    "invite_sent_at": "2024-01-20T10:30:00Z",
    "invite_expire_at": "2024-01-21T10:30:00Z"
  },
  "message": "Invitation resent successfully"
}
```

**Business Rules:**
- User must have status = `PendingActivation`
- Generates new invitation token
- Sets new `invite_expire_at` (24 hours from resend)
- Updates `invite_sent_at` timestamp
- Sends new invitation email via SMTP

---

### 7.2 Get User by ID

**Add:**
- `GET /v1/users/{user_id}`

**Purpose:** Get user details by user ID (alternative to family-scoped endpoint).

**Authorization:**
- SuperAdmin: Can access any user
- FamilyAdmin: Can access users in their own family only
- Member: Can only access their own profile

**Response:** Same structure as `GET /v1/families/{family_id}/users/{user_id}`

**Rationale:** Provides direct user lookup without requiring family_id, useful for SuperAdmin operations and user profile access.

---

## 8. Summary of Changes

| Endpoint | Old | New | Change Type |
|----------|-----|-----|-------------|
| Family Soft Delete | `PATCH /v1/families/{family_id}/soft-delete` | `DELETE /v1/families/{family_id}` | Method + Path |
| User Soft Delete | `PATCH /v1/families/{family_id}/users/{user_id}/soft-delete` | `DELETE /v1/families/{family_id}/users/{user_id}` | Method + Path |
| Create Invitation | `POST /v1/invite/families/{family_id}/users/` | `POST /v1/invite` | Path + Body |
| Validate Invitation | `GET /v1/invitations/validate?token=...` | `GET /v1/invitations/{token}` | Path Parameter |
| Activate Invitation | `POST /v1/invitations/activate` | `POST /v1/invitations/activate/{token}` | Path Parameter |
| Get User Profile | `GET /v1/users/me` | `GET /v1/users/{user_id}` | Path |
| Update User Profile | `PATCH /v1/users/me` | `PATCH /v1/users/{user_id}` | Path |
| Change Password | `POST /v1/users/me/password/change` | `PATCH /v1/users/{user_id}` | Method + Path + Consolidation |
| Resend Invitation | N/A | `POST /v1/invite/resend` | New Endpoint |
| Get User by ID | N/A | `GET /v1/users/{user_id}` | New Endpoint |

---

## 9. Migration Notes

1. **Backward Compatibility:** These changes are breaking changes. Consider versioning (e.g., `/v2/`) or maintaining old endpoints during transition period.

2. **Client Updates Required:**
   - Update all soft-delete calls to use DELETE method
   - Update invitation endpoints to use new paths and body structure
   - Update profile endpoints to use `{user_id}` instead of `/me`
   - Update password change to use PATCH with consolidated endpoint

3. **Authorization Logic:**
   - Ensure proper validation for `family_id` in unified invitation endpoint
   - Ensure users can only access/modify their own resources unless they have admin privileges
   - Validate `user_id` matches JWT `sub` for self-operations

4. **Testing Considerations:**
   - Test all authorization scenarios (self-access vs admin-access)
   - Test family_id validation in unified invitation endpoint
   - Test password change consolidation with profile update
   - Test new resend invitation endpoint

---

## 10. Benefits

1. **RESTful Design:** DELETE method for deletions, proper resource paths
2. **Consistency:** Unified patterns across similar operations
3. **Flexibility:** Single endpoints that support both self and admin operations
4. **Cleaner API:** Reduced path complexity, better resource naming
5. **Extensibility:** Easier to add new features (e.g., resend invitation)

