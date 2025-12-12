# API Specification: Core Identity, Access & Organization (F-001) - Part 2

## 1. Overview

This document defines the REST API specification for **F-001: Core Identity, Access & Organization** - Part 2, covering Invitations, Profile Management, and Role Management.

### 1.1 Feature Summary

The F-001 feature provides the foundational identity and tenant-isolation framework for DocValut. This API specification covers:

- **D. Invitations**: User invitation creation, validation, and account activation
- **E. Profile Management**: Current user profile viewing and password management
- **F. Role Management**: Role listing and user role assignment

### 1.2 Scope

This specification includes:
- User invitation workflow with 24-hour expiry
- Invitation token validation and account activation
- Current user profile retrieval and name updates
- Password change with strong policy enforcement
- Global role listing (predefined roles)
- User role assignment within families

### 1.3 Key Capabilities

- Secure invitation system with token-based activation
- Strong password policy enforcement (12+ chars, upper/lower/number/special, no reuse of last 5)
- Self-service profile management
- Multi-role assignment with permission merging
- Family-scoped role management

---

## 2. Global API Rules

### 2.1 Authentication

**JWT Token Structure:**

All API endpoints (except invitation validation and activation) require JWT Bearer token authentication.

**Token Format:** `Authorization: Bearer <jwt_token>`

**Required Claims in JWT Payload:**
- `sub` (subject): User ID (string, UUID format) - **REQUIRED**
- `role`: User role (string) - **REQUIRED** - Encoded in token, not database lookup
  - Values: `"superadmin"`, `"familyadmin"`, `"member"` (lowercase)
- `family_id`: Family ID (string, UUID format, nullable) - **REQUIRED**
  - `null` for SuperAdmin (indicates global access)
  - UUID for family-scoped users (indicates family membership)
- `exp`: Token expiration timestamp (integer, Unix timestamp) - **REQUIRED**
- `iat`: Token issued at timestamp (integer, Unix timestamp) - **RECOMMENDED**
- `jti`: JWT ID (string, unique token identifier) - **RECOMMENDED** for token revocation

**Token Expiration:**
- Access tokens expire after **1 hour (60 minutes)**
- Expired tokens return `401 UNAUTHENTICATED` with error code `TOKEN_EXPIRED`

### 2.2 Response Format

**Success Response (200/201):**
```json
{
  "data": { ... },
  "message": "Operation completed successfully"
}
```

**Error Response (400/401/403/404/etc.):**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "details": [{"field": "field_name", "issue": "Error description"}]
  },
  "message": "Human-friendly error message"
}
```

**Response Headers (REQUIRED):**
- `X-Request-ID`: Unique request identifier for debugging (e.g., `req_abc123xyz789`) - **MUST be present in ALL responses**
- `ETag`: Resource version identifier (for GET responses of resources that support updates, based on `updated_at`)
- `Last-Modified`: Timestamp of last modification (for GET responses, optional)

**Note:** 
- Field order shown is for readability only. JSON objects are unordered (RFC 7159). Do not require or emphasize field order.
- DO NOT include `success` field - HTTP status codes indicate success/failure.

### 2.3 Conditional Requests (ETags)

**ETag Requirements:**
- GET responses MUST include `ETag` header with resource version identifier (based on `updated_at`)
- GET responses SHOULD include `Last-Modified` header with `updated_at` timestamp
- PATCH requests SHOULD include `If-Match` header with ETag value from GET
- GET requests MAY include `If-None-Match` header with ETag value for cache validation
- Server MUST return `412 Precondition Failed` if ETag doesn't match current resource version (for If-Match)
- Server MUST return `304 Not Modified` if ETag matches current resource version (for If-None-Match)

**ETag Format:**
- Based on `updated_at` timestamp: `"20240120T103000Z"` (ISO 8601 format, UTC)

### 2.4 Field Validation

**Email Field Validation:**
- Format: RFC 5322 format
- Maximum length: 254 characters
- Uniqueness: Case-insensitive uniqueness check (system-wide)

**Password Field Validation:**
- Minimum length: 12 characters
- Must contain: uppercase letter, lowercase letter, number, special character
- Cannot reuse last 5 passwords
- Validation: Enforced both client-side and server-side

**String Length Validation:**
- User name: Min 1 character, max 255 characters

**Date/DateTime Field Validation:**
- Format: ISO 8601 format (e.g., `YYYY-MM-DDTHH:mm:ssZ`)
- Timezone: **MUST use UTC timezone** - All datetime fields MUST be in UTC
- Format with UTC: Use `Z` suffix (e.g., `2024-01-20T10:30:00Z`)

**UUID Field Validation:**
- Format: RFC 4122 UUID format (e.g., `550e8400-e29b-41d4-a716-446655440000`)
- Version: UUID v4 recommended

**Enum/Choice Field Validation:**
- Status: Enum - one of: `"Active"`, `"PendingActivation"`, `"SoftDeleted"` (case-sensitive)

**Business-Level Validation:**
- User email: Case-insensitive unique across all users (system-wide)
- Error on duplicate: `409 Conflict` with error code `DUPLICATE_EMAIL`
- Invitation token: Unique, expires 24 hours after creation
- Password reuse: Cannot match any of the last 5 passwords

---

## 3. Roles & Permissions

### 3.1 Role Definitions

| Role | Description | Family Access |
|------|-------------|---------------|
| superadmin | Global administrator with access to all families | All families (family_id: null in JWT) |
| familyadmin | Administrator within a specific family | Single family (family_id: <uuid> in JWT) |
| member | Standard user within a family | Single family (family_id: <uuid> in JWT) |

### 3.2 Permission Matrix

| Endpoint | SuperAdmin | FamilyAdmin | Member |
|----------|------------|-------------|--------|
| POST /v1/invite/families/{family_id}/users/ | ✓ | ✓ (own family) | ✗ |
| GET /v1/invitations/validate | ✓ (public) | ✓ (public) | ✓ (public) |
| POST /v1/invitations/activate | ✓ (public) | ✓ (public) | ✓ (public) |
| GET /v1/users/me | ✓ | ✓ | ✓ |
| PATCH /v1/users/me | ✓ | ✓ | ✓ |
| POST /v1/users/me/password/change | ✓ | ✓ | ✓ |
| GET /v1/roles | ✓ | ✓ | ✓ |
| PATCH /v1/roles/families/{family_id}/users/{user_id}/ | ✓ | ✓ (own family) | ✗ |

**Notes:**
- Invitation validation and activation are public endpoints (no authentication required)
- SuperAdmin can invite users to any family
- FamilyAdmin can only invite users to their own family (family_id from token must match)
- All users can manage their own profile
- SuperAdmin and FamilyAdmin can assign roles to users
- FamilyAdmin can only assign roles to users in their own family

---

## 4. Resources & Endpoints

**Note:** All router endpoints MUST use centralized documentation classes for Swagger/OpenAPI documentation (Rule 10). Create documentation classes in `src/{module}/documentations/{module}_api_doc.py` with `summary` and `description` fields for each endpoint operation.

### 4.1 Resource Overview

| Resource | Description | Scope |
|----------|-------------|-------|
| Invitation | User invitation with token and expiry | Family-scoped |
| User Profile | Current authenticated user's profile | Self-scoped |
| Role | Predefined permission profile | Global |

### 4.2 Endpoint Summary

| Method | Path | Purpose | Auth Required |
|--------|------|---------|---------------|
| POST | /v1/invite/families/{family_id}/users/ | Create user invitation | Yes (SuperAdmin/FamilyAdmin) |
| GET | /v1/invitations/validate | Validate invitation token | No (public) |
| POST | /v1/invitations/activate | Activate account with password | No (public) |
| GET | /v1/users/me | Get current user profile | Yes |
| PATCH | /v1/users/me | Update current user profile name | Yes |
| POST | /v1/users/me/password/change | Change current user password | Yes |
| GET | /v1/roles | List available roles | Yes |
| PATCH | /v1/roles/families/{family_id}/users/{user_id}/ | Update user roles | Yes (SuperAdmin/FamilyAdmin) |

---

## D. Invitations

### D.1 POST /v1/invite/families/{family_id}/users/

- **Purpose:** Create a new user invitation and send invitation email
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin (all families) or FamilyAdmin (own family only)
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `Content-Type: application/json` (REQUIRED)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier (optional for POST endpoints, included for consistency)

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| family_id | string (UUID) | Yes | Family identifier |

**Query Parameters:** None

**Request Body**

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| email | string | Yes | User email address | RFC 5322 format, max 254 chars, case-insensitive unique system-wide |

**Request Body Example:**
```json
{
  "email": "newuser@example.com"
}
```

**Success Response (201 Created)**

```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "family_id": "660e8400-e29b-41d4-a716-446655440000",
    "status": "PendingActivation",
    "invite_token": "abc123xyz789def456",
    "invite_sent_at": "2024-01-20T10:30:00Z",
    "invite_expire_at": "2024-01-21T10:30:00Z",
    "invited_by": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2024-01-20T10:30:00Z"
  },
  "message": "Invitation sent successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | User ID (created in PendingActivation status) |
| email | string | User email |
| family_id | string (UUID) | Family ID |
| status | string | User status (PendingActivation) |
| invite_token | string | Invitation token (for activation link) |
| invite_sent_at | string (datetime) | When invite was sent (UTC, ISO 8601) |
| invite_expire_at | string (datetime) | Invite expiration timestamp (24h after send, UTC, ISO 8601) |
| invited_by | string (UUID) | User ID who created the invitation |
| created_at | string (datetime) | Creation timestamp (UTC, ISO 8601) |

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User cannot invite to this family (not SuperAdmin and not member of family) |
| 404 Not Found | FAMILY_NOT_FOUND | Family not found or soft-deleted |
| 400 Bad Request | VALIDATION_ERROR | Invalid request body or field validation failed |
| 409 Conflict | DUPLICATE_EMAIL | Email already exists (case-insensitive) |
| 422 Unprocessable Entity | BUSINESS_RULE_FAILED | Family is SoftDeleted (cannot invite) |

**Error Response Example (409 - Duplicate Email):**
```json
{
  "error": {
    "code": "DUPLICATE_EMAIL",
    "details": [{"field": "email", "issue": "A user with this email already exists."}]
  },
  "message": "Email must be unique."
}
```

**Business Rules:**
- SuperAdmin can invite users to any family
- FamilyAdmin can only invite users to their own family (family_id from token must match)
- User is created with status = `PendingActivation`
- Invitation token is generated (unique, secure random string)
- `invite_expire_at` is set to 24 hours after `invite_sent_at`
- `invited_by` is set to current user ID
- Email must be unique system-wide (case-insensitive)
- Cannot invite if family is SoftDeleted
- Invitation email is sent via SMTP (handled by email service)
- If user already exists with same email, return 409 Conflict

---

### D.2 GET /v1/invitations/validate

- **Purpose:** Validate invitation token and determine if account setup can proceed
- **Authentication:** Not required (public endpoint)
- **Authorization / Roles:** Public (no authentication)
- **Headers:**
  - **Request Headers:**
    - None (public endpoint)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier (optional for POST endpoints, included for consistency)

**Path Parameters:** None

**Query Parameters**

**Note:** Query parameters MUST be defined using a query schema class with `Depends()` pattern (Rule 9), NOT individual `Query()` parameters in the router endpoint.

**Query Schema Class (REQUIRED):**
```python
class InvitationValidateQuery(BaseModel):
    """Query schema for validating invitation token."""

    token: str = Field(..., description="Invitation token", min_length=1)

    model_config = ConfigDict(from_attributes=True)
```

**Router Endpoint Pattern (REQUIRED):**
```python
@router.get("", response_model=StandardResponse[InvitationValidationResponse])
async def validate_invitation(
    query: InvitationValidateQuery = Depends(InvitationValidateQuery),
    session: AsyncSession = Depends(get_session),
):
    """Validate invitation token."""
    # Access via query.token
```

**Query Parameters Table (for documentation only):**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| token | string | Yes | Invitation token (alphanumeric string, secure random) |

**Success Response (200 OK)**

```json
{
  "data": {
    "is_token_valid": true,
    "is_token_expired": false,
    "redirect_target": "account_setup",
    "user_id": "770e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "family_id": "660e8400-e29b-41d4-a716-446655440000",
    "status": "PendingActivation",
    "invite_expire_at": "2024-01-21T10:30:00Z",
    "password_rules": {
      "min_length": 12,
      "uppercase": true,
      "lowercase": true,
      "number": true,
      "special": true,
      "disallow_last_5": false
    }
  },
  "message": "Invitation token is valid"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| is_token_valid | boolean | True if token is valid and not expired |
| is_token_expired | boolean | True if token has expired (NOW > invite_expire_at) |
| redirect_target | string | Redirect target: "account_setup" if valid, "invite_expired" if invalid/expired |
| user_id | string (UUID) \| null | User ID (null if token invalid) |
| email | string \| null | User email (null if token invalid) |
| family_id | string (UUID) \| null | Family ID (null if token invalid) |
| status | string \| null | User status (null if token invalid) |
| invite_expire_at | string (datetime) \| null | Invite expiration timestamp (null if token invalid) |
| password_rules | object \| null | Password rules for account setup (null if token invalid) |
| password_rules.min_length | integer | Minimum password length (12) |
| password_rules.uppercase | boolean | Require uppercase letter (true) |
| password_rules.lowercase | boolean | Require lowercase letter (true) |
| password_rules.number | boolean | Require number (true) |
| password_rules.special | boolean | Require special character (true) |
| password_rules.disallow_last_5 | boolean | Cannot reuse last 5 passwords (false for new users, true for password changes) |

**Success Response (200 OK) - Invalid/Expired Token:**

```json
{
  "data": {
    "is_token_valid": false,
    "is_token_expired": true,
    "redirect_target": "invite_expired",
    "user_id": null,
    "email": null,
    "family_id": null,
    "status": null,
    "invite_expire_at": null,
    "expired_reason": "expired"
  },
  "message": "Invitation token is invalid or expired"
}
```

**Response Schema for Invalid Token:**

| Field | Type | Description |
|-------|------|-------------|
| is_token_valid | boolean | Always false for invalid tokens |
| is_token_expired | boolean | True if expired, false if invalid/not found |
| redirect_target | string | Always "invite_expired" |
| expired_reason | string \| null | Reason: "expired", "invalid", "family_soft_deleted", "user_soft_deleted" (optional) |
| user_id | null | Always null |
| email | null | Always null |
| family_id | null | Always null |
| status | null | Always null |
| invite_expire_at | null | Always null |

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | INVALID_REQUEST | Missing or invalid token parameter |

**Business Rules:**
- Token validation is public (no authentication required)
- Token is valid if:
  - User exists with matching `invite_token`
  - User status is `PendingActivation`
  - `invite_expire_at` > NOW
  - User is not soft-deleted (`is_del = false`)
  - Family is not soft-deleted (`family.status = Active`)
- Token is invalid/expired if:
  - No user found with matching token
  - Token has expired (`invite_expire_at` <= NOW)
  - User is soft-deleted
  - Family is soft-deleted
  - User status is not `PendingActivation`
- Invalid tokens and expired tokens are treated the same (no distinction in error message)
- Must not expose existence of accounts via error messages (generic error for invalid tokens)
- `redirect_target` guides UI to appropriate screen:
  - `"account_setup"` if token is valid
  - `"invite_expired"` if token is invalid/expired

---

### D.3 POST /v1/invitations/activate

- **Purpose:** Activate user account by setting name and password
- **Authentication:** Not required (public endpoint, uses invitation token)
- **Authorization / Roles:** Public (no authentication)
- **Headers:**
  - **Request Headers:**
    - `Content-Type: application/json` (REQUIRED)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier (optional for POST endpoints, included for consistency)

**Path Parameters:** None

**Query Parameters:** None

**Request Body**

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| invite_token | string | Yes | Invitation token | Must match valid, non-expired token |
| name | string | Yes | User name | Min 1 char, max 255 chars |
| password | string | Yes | User password | Min 12 chars, upper/lower/number/special, not in last 5 passwords |

**Request Body Example:**
```json
{
  "invite_token": "abc123xyz789def456",
  "name": "John Doe",
  "password": "SecurePass123!"
}
```

**Success Response (200 OK)**

```json
{
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "user": {
      "id": "770e8400-e29b-41d4-a716-446655440000",
      "email": "newuser@example.com",
      "name": "John Doe",
      "role": "member",
      "family_id": "660e8400-e29b-41d4-a716-446655440000",
      "family_name": "The Smith Family Vault"
    },
    "password_rules": {
      "min_length": 12,
      "uppercase": true,
      "lowercase": true,
      "number": true,
      "special": true,
      "disallow_last_5": false
    }
  },
  "message": "Account activated successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| token | string | JWT access token (user is automatically authenticated) |
| expires_in | integer | Token expiration time in seconds (3600 = 1 hour) |
| user | object | User information |
| user.id | string (UUID) | User ID |
| user.email | string | User email |
| user.name | string | User name |
| user.role | string | User role (default: member, or first assigned role) |
| user.family_id | string (UUID) | Family ID |
| user.family_name | string | Family name |
| password_rules | object | Password rules (for reference, disallow_last_5 is false for new users) |
| password_rules.min_length | integer | Minimum password length (12) |
| password_rules.uppercase | boolean | Require uppercase letter (true) |
| password_rules.lowercase | boolean | Require lowercase letter (true) |
| password_rules.number | boolean | Require number (true) |
| password_rules.special | boolean | Require special character (true) |
| password_rules.disallow_last_5 | boolean | Cannot reuse last 5 passwords (false for new users) |

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | VALIDATION_ERROR | Invalid request body or field validation failed |
| 401 Unauthorized | INVALID_TOKEN | Invitation token is invalid, expired, or already used |
| 401 Unauthorized | TOKEN_EXPIRED | Invitation token has expired |
| 401 Unauthorized | USER_ALREADY_ACTIVATED | User status is already Active (token already used) |
| 401 Unauthorized | USER_SOFT_DELETED | User is soft-deleted |
| 401 Unauthorized | FAMILY_SOFT_DELETED | User's family is soft-deleted |
| 422 Unprocessable Entity | PASSWORD_VALIDATION_FAILED | Password does not meet strong password requirements |

**Error Response Example (422 - Password Validation Failed):**
```json
{
  "error": {
    "code": "PASSWORD_VALIDATION_FAILED",
    "details": [
      {"field": "password", "issue": "Password must be at least 12 characters long."},
      {"field": "password", "issue": "Password must contain at least one uppercase letter."},
      {"field": "password", "issue": "Password must contain at least one special character."}
    ]
  },
  "message": "Password does not meet security requirements."
}
```

**Business Rules:**
- Token must be valid and not expired (same validation as GET /v1/invitations/validate)
- User must have status = `PendingActivation` (if already Active, return error)
- User must not be soft-deleted
- Family must not be soft-deleted
- Password must meet strong password policy:
  - Minimum 12 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character
  - **Password reuse check does NOT apply to initial activation** (new users have no password history)
  - Password reuse check only applies to password changes (POST /v1/users/me/password/change)
- On success:
  - Set `user.name` to provided name
  - Set `user.hash_password` to hashed password
  - Set `user.status` = `Active`
  - Set `user.activated_at` = NOW
  - Clear `invite_token` and `invite_expire_at`
  - Generate and return JWT token (user is automatically authenticated)
- Token is single-use (cannot be used again after activation)
- If token expires between validation and activation, return 401 with `TOKEN_EXPIRED`
- Password validation errors must be detailed (per rule failure)

---

## E. Profile Management

### E.1 GET /v1/users/me

- **Purpose:** Get current authenticated user's profile information
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** All authenticated users
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `If-None-Match`: ETag value from previous GET (optional, for cache validation)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier based on `updated_at` (e.g., `"20240120T103000Z"`)
    - `Last-Modified`: Timestamp of last modification (e.g., `Wed, 20 Jan 2024 10:30:00 GMT`)

**Path Parameters:** None

**Query Parameters:** None

**Success Response (200 OK)**

```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe",
    "status": "Active",
    "family_id": "660e8400-e29b-41d4-a716-446655440000",
    "family_name": "The Smith Family Vault",
    "can_edit_profile": true,
    "password_rules": {
      "min_length": 12,
      "uppercase": true,
      "lowercase": true,
      "number": true,
      "special": true,
      "disallow_last_5": true
    },
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "updated_at": "2024-01-20T10:30:00Z",
    "updated_by": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "Profile retrieved successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | User ID |
| email | string | User email (immutable, read-only) |
| name | string | User name |
| status | string | User status (Active, PendingActivation, SoftDeleted) |
| family_id | string (UUID) \| null | Family ID (null for SuperAdmin) |
| family_name | string \| null | Family name (null for SuperAdmin) |
| can_edit_profile | boolean | True if user can edit profile (status = Active) |
| password_rules | object | Password rules for change password operation |
| password_rules.min_length | integer | Minimum password length (12) |
| password_rules.uppercase | boolean | Require uppercase letter (true) |
| password_rules.lowercase | boolean | Require lowercase letter (true) |
| password_rules.number | boolean | Require number (true) |
| password_rules.special | boolean | Require special character (true) |
| password_rules.disallow_last_5 | boolean | Cannot reuse last 5 passwords (true) |
| created_at | string (datetime) | Creation timestamp (UTC, ISO 8601) |
| created_by | string (UUID) | User ID who created the user |
| updated_at | string (datetime) | Last update timestamp (UTC, ISO 8601) |
| updated_by | string (UUID) | User ID who last updated the user |
| deleted_at | string (datetime) \| null | Soft-delete timestamp (null if Active, UTC, ISO 8601) |
| deleted_by | string (UUID) \| null | User ID who soft-deleted the user (null if Active) |

**Success Response (304 Not Modified)**

If `If-None-Match` header matches current ETag:
- Status: `304 Not Modified`
- No response body
- Headers: `X-Request-ID`, `ETag`, `Last-Modified`

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 401 Unauthorized | USER_SOFT_DELETED | User is soft-deleted (force logout) |
| 401 Unauthorized | FAMILY_SOFT_DELETED | User's family is soft-deleted (force logout) |

**Business Rules:**
- Returns current authenticated user's profile (from JWT `sub` claim)
- Email is immutable and read-only (never returned as mutable)
- If user is SoftDeleted mid-session, return 401 and force logout
- If family is SoftDeleted mid-session, return 401 and force logout
- `can_edit_profile` = true only if user.status = `Active`
- Password rules are returned for UI display (for change password modal)
- ETag based on `updated_at` timestamp

---

### E.2 PATCH /v1/users/me

- **Purpose:** Update current authenticated user's profile name
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** All authenticated users (own profile only)
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `Content-Type: application/json` (REQUIRED)
    - `If-Match`: ETag value from GET response (REQUIRED for concurrency control)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier (optional for POST endpoints, included for consistency)
    - `ETag`: New resource version identifier after update (based on new `updated_at`)

**Path Parameters:** None

**Query Parameters:** None

**Request Body**

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| name | string | Yes | User name | Min 1 char, max 255 chars |

**Request Body Example:**
```json
{
  "name": "John Doe Updated"
}
```

**Success Response (200 OK)**

```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "John Doe Updated",
    "status": "Active",
    "family_id": "660e8400-e29b-41d4-a716-446655440000",
    "family_name": "The Smith Family Vault",
    "can_edit_profile": true,
    "password_rules": {
      "min_length": 12,
      "uppercase": true,
      "lowercase": true,
      "number": true,
      "special": true,
      "disallow_last_5": true
    },
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "updated_at": "2024-01-20T10:35:00Z",
    "updated_by": "770e8400-e29b-41d4-a716-446655440000",
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "Profile updated successfully"
}
```

**Response Schema:** Same as GET /v1/users/me

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 401 Unauthorized | USER_SOFT_DELETED | User is soft-deleted (force logout) |
| 401 Unauthorized | FAMILY_SOFT_DELETED | User's family is soft-deleted (force logout) |
| 400 Bad Request | VALIDATION_ERROR | Invalid request body or field validation failed |
| 412 Precondition Failed | PRECONDITION_FAILED | ETag mismatch (If-Match header doesn't match current resource version) |
| 422 Unprocessable Entity | BUSINESS_RULE_FAILED | User status is not Active (cannot edit) |

**Error Response Example (412 - ETag Mismatch):**
```json
{
  "error": {
    "code": "PRECONDITION_FAILED",
    "details": [{"field": "etag", "issue": "Resource has been modified since retrieval. Please fetch the latest version and retry."}]
  },
  "message": "Resource version mismatch. The resource was modified by another user."
}
```

**Business Rules:**
- Only updates current authenticated user's profile (from JWT `sub` claim)
- Email cannot be updated (immutable field)
- Only `name` field can be updated
- User must have status = `Active` (cannot update if PendingActivation or SoftDeleted)
- If user is SoftDeleted mid-session, return 401 and force logout
- If family is SoftDeleted mid-session, return 401 and force logout
- `updated_at` updated automatically
- ETag validation required (If-Match header)

---

### E.3 POST /v1/users/me/password/change

- **Purpose:** Change current authenticated user's password
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** All authenticated users (own password only)
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `Content-Type: application/json` (REQUIRED)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier (optional for POST endpoints, included for consistency)

**Path Parameters:** None

**Query Parameters:** None

**Request Body**

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| current_password | string | Yes | Current password | Must match stored password hash |
| new_password | string | Yes | New password | Min 12 chars, upper/lower/number/special, not in last 5 passwords |

**Request Body Example:**
```json
{
  "current_password": "OldSecurePass123!",
  "new_password": "NewSecurePass456!"
}
```

**Success Response (200 OK)**

```json
{
  "data": null,
  "message": "Password changed successfully"
}
```

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 401 Unauthorized | INCORRECT_PASSWORD | Current password is incorrect |
| 401 Unauthorized | USER_SOFT_DELETED | User is soft-deleted (force logout) |
| 401 Unauthorized | FAMILY_SOFT_DELETED | User's family is soft-deleted (force logout) |
| 400 Bad Request | VALIDATION_ERROR | Invalid request body |
| 422 Unprocessable Entity | PASSWORD_VALIDATION_FAILED | New password does not meet strong password requirements |
| 422 Unprocessable Entity | PASSWORD_REUSE_VIOLATION | New password matches one of the last 5 passwords |

**Error Response Example (401 - Incorrect Password):**
```json
{
  "error": {
    "code": "INCORRECT_PASSWORD",
    "details": [{"field": "current_password", "issue": "Current password is incorrect."}]
  },
  "message": "Password change failed. Please verify your current password."
}
```

**Error Response Example (422 - Password Validation Failed):**
```json
{
  "error": {
    "code": "PASSWORD_VALIDATION_FAILED",
    "details": [
      {"field": "new_password", "issue": "Password must be at least 12 characters long."},
      {"field": "new_password", "issue": "Password must contain at least one uppercase letter."}
    ]
  },
  "message": "Password does not meet security requirements."
}
```

**Error Response Example (422 - Password Reuse):**
```json
{
  "error": {
    "code": "PASSWORD_REUSE_VIOLATION",
    "details": [{"field": "new_password", "issue": "Password cannot be one of your last 5 passwords."}]
  },
  "message": "Password reuse is not allowed for security reasons."
}
```

**Note:** Password reuse validation only applies to password changes. Initial account activation (POST /v1/invitations/activate) does not check password history since new users have no previous passwords.

**Business Rules:**
- Only changes current authenticated user's password (from JWT `sub` claim)
- Current password must be verified (match stored hash)
- New password must meet strong password policy:
  - Minimum 12 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character
  - Cannot match any of the last 5 passwords
- User must have status = `Active` (cannot change password if PendingActivation or SoftDeleted)
- If user is SoftDeleted mid-session, return 401 and force logout
- If family is SoftDeleted mid-session, return 401 and force logout
- Password validation errors must be detailed (per rule failure)
- Password history must be checked (last 5 passwords) - **only for password changes, not initial activation**
- On success:
  - Update `hash_password` with new hashed password
  - Update password history (store old password hash in history)
  - Update `updated_at` timestamp
- Passwords must never be logged or returned in responses
- Must not reveal whether previous passwords matched other accounts (generic error)

---

## F. Role Management

### F.1 GET /v1/roles

- **Purpose:** List all available predefined roles (global)
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** All authenticated users
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `If-None-Match`: ETag value from previous GET (optional, for cache validation)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier (optional for POST endpoints, included for consistency)

**Path Parameters:** None

**Query Parameters:** None

**Success Response (200 OK)**

```json
{
  "data": {
    "items": [
      {
        "id": "880e8400-e29b-41d4-a716-446655440000",
        "name": "superadmin",
        "permissions": {
          "family:manage_all": true,
          "user:manage_all": true,
          "role:manage_all": true
        }
      },
      {
        "id": "990e8400-e29b-41d4-a716-446655440000",
        "name": "familyadmin",
        "permissions": {
          "family:manage_users": true,
          "user:invite": true,
          "user:manage_roles": true
        }
      },
      {
        "id": "aa0e8400-e29b-41d4-a716-446655440000",
        "name": "member",
        "permissions": {
          "document:manage_own": true,
          "document:view_shared": true
        }
      }
    ]
  },
  "message": "Roles retrieved successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| items | array | Array of role objects |
| items[].id | string (UUID) | Role ID |
| items[].name | string | Role name (superadmin, familyadmin, member) |
| items[].permissions | object | JSON permission blob (from permission system) |

**Success Response (304 Not Modified)**

If `If-None-Match` header matches current ETag:
- Status: `304 Not Modified`
- No response body
- Headers: `X-Request-ID`, `ETag`, `Last-Modified`

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |

**Business Rules:**
- Returns all predefined roles (global, not family-scoped)
- Roles are: `superadmin`, `familyadmin`, `member`
- Roles are predefined and not editable via API
- Permissions are JSON objects imported from permission system
- All authenticated users can view available roles
- Roles are used for user role assignment within families
- **Note:** ETag header is optional for list endpoints (included for consistency, but conditional requests are typically used for single resource GETs)

---

### F.2 PATCH /v1/roles/families/{family_id}/users/{user_id}/

- **Purpose:** Update user roles within a family (replace existing roles)
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin (all families) or FamilyAdmin (own family only)
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `Content-Type: application/json` (REQUIRED)
    - `If-Match`: ETag value from GET user response (REQUIRED for concurrency control)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier (optional for POST endpoints, included for consistency)

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| family_id | string (UUID) | Yes | Family identifier |
| user_id | string (UUID) | Yes | User identifier |

**Query Parameters:** None

**Request Body**

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| role_ids | array (string) | Yes | Array of role IDs to assign | Array of valid UUID role IDs, must contain exactly one role ID (single role per user), can be empty array (remove all roles) |

**Request Body Example:**
```json
{
  "role_ids": [
    "990e8400-e29b-41d4-a716-446655440000"
  ]
}
```

**Note:** Users have exactly one role at a time. The `role_ids` array must contain exactly one role ID (not multiple roles). Empty array removes all roles.

**Success Response (200 OK)**

```json
{
  "data": {
    "user_id": "770e8400-e29b-41d4-a716-446655440000",
    "family_id": "660e8400-e29b-41d4-a716-446655440000",
    "roles": [
      {
        "id": "990e8400-e29b-41d4-a716-446655440000",
        "name": "familyadmin"
      }
    ]
  },
  "message": "User roles updated successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| user_id | string (UUID) | User ID |
| family_id | string (UUID) | Family ID |
| roles | array (object) | List of assigned roles (single role per user) |
| roles[].id | string (UUID) | Role ID |
| roles[].name | string | Role name |

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User cannot manage roles in this family (not SuperAdmin and not member of family) |
| 404 Not Found | USER_NOT_FOUND | User not found, soft-deleted, or not in specified family |
| 404 Not Found | FAMILY_NOT_FOUND | Family not found or soft-deleted |
| 400 Bad Request | VALIDATION_ERROR | Invalid request body or invalid role IDs |
| 412 Precondition Failed | PRECONDITION_FAILED | ETag mismatch (If-Match header doesn't match current resource version) |
| 422 Unprocessable Entity | BUSINESS_RULE_FAILED | User is SoftDeleted (cannot update roles) OR Family is SoftDeleted |

**Error Response Example (400 - Invalid Role ID):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [{"field": "role_ids", "issue": "Invalid role ID: role_id_does_not_exist"}]
  },
  "message": "One or more role IDs are invalid."
}
```

**Business Rules:**
- SuperAdmin can update roles for users in any family
- FamilyAdmin can update roles for users in their own family (family_id from token must match)
- Member role cannot update user roles
- Replaces all existing User_Role mappings for the user in the specified family
- Empty `role_ids` array removes all roles (allowed)
- **Single role per user**: Users have exactly one role at a time (not multiple roles)
- User must have status = `Active` or `PendingActivation` (cannot update roles if SoftDeleted)
- Cannot update roles if family is SoftDeleted
- Cannot update roles if user is SoftDeleted
- All role IDs must be valid (exist in roles table)
- Role assignments are family-scoped (User_Role includes family_id)
- ETag validation required (If-Match header from GET user response)

---

## 5. Open Questions

1. Should password history be stored in a separate table or embedded in user record?
2. Should there be rate limiting on invitation creation?
3. Should there be audit logging for role assignment changes?
4. Should invitation emails include a resend option if expired?

---

## 6. Assumptions

1. Invitation tokens are single-use (cannot be reused after activation)
2. Password history stores last 5 password hashes (implementation detail)
3. Role permissions are JSON objects imported from permission system
4. Multi-role permission merging is handled by permission system (not API layer)
5. Invitation emails are sent via SMTP (handled by email service)
6. All datetime fields are stored and returned in UTC timezone
7. Role assignments are family-scoped (same user can have different roles in different families, if multi-family support is added later)
8. Empty role assignment (remove all roles) is allowed

