# API Specification: Core Identity, Access & Organization (F-001) - Part 1

## 1. Overview

This document defines the REST API specification for **F-001: Core Identity, Access & Organization** - Part 1, covering Authentication & Session, Families, and Users management.

### 1.1 Feature Summary

The F-001 feature provides the foundational identity and tenant-isolation framework for DocValut. This API specification covers:

- **A. Authentication & Session**: User login and logout operations
- **B. Families**: Tenant-level organizational unit management (SuperAdmin only)
- **C. Users**: User management within families (family-scoped operations)

### 1.2 Scope

This specification includes:
- User authentication (login/logout)
- Family CRUD operations (create, read, update, soft-delete)
- User listing and detail retrieval within families
- User soft-delete operations
- Tenant isolation enforcement at the family level

### 1.3 Key Capabilities

- JWT-based authentication with family-scoped access
- Multi-tenant isolation through family boundaries
- Soft-delete operations with cascade rules
- Role-based access control (RBAC) enforcement
- Comprehensive audit tracking

---

## 2. Global API Rules

### 2.1 Authentication

**JWT Token Structure:**

All API endpoints (except login) require JWT Bearer token authentication.

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

**CORRECT JWT Payload Structure:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "role": "familyadmin",
  "family_id": "660e8400-e29b-41d4-a716-446655440000",
  "exp": 1735689600,
  "iat": 1735686000,
  "jti": "jwt_abc123xyz789"
}
```

**SuperAdmin JWT Payload:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "role": "superadmin",
  "family_id": null,
  "exp": 1735689600,
  "iat": 1735686000,
  "jti": "jwt_abc123xyz789"
}
```

**Token Expiration:**
- Access tokens expire after **1 hour (60 minutes)**
- Expired tokens return `401 UNAUTHENTICATED` with error code `TOKEN_EXPIRED`

**Token Validation:**
- Server MUST validate token signature, expiration, and required claims
- Missing or invalid token: Return `401 UNAUTHENTICATED`
- Missing required claims: Return `401 UNAUTHENTICATED` with error code `INVALID_TOKEN`

**Multi-Tenancy from Token:**
- **SuperAdmin**: `family_id: null` - Has access to all families
- **Family-scoped users**: `family_id: "<uuid>"` - Access limited to specified family
- Server MUST extract `family_id` from token for authorization checks

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
- PATCH/PUT/DELETE requests SHOULD include `If-Match` header with ETag value from GET
- GET requests MAY include `If-None-Match` header with ETag value for cache validation
- Server MUST return `412 Precondition Failed` if ETag doesn't match current resource version (for If-Match)
- Server MUST return `304 Not Modified` if ETag matches current resource version (for If-None-Match)

**ETag Format:**
- Based on `updated_at` timestamp: `"20240120T103000Z"` (ISO 8601 format, UTC)

**HTTP Status Codes:**
- `200 OK`: Request successful, resource returned (GET) or updated (PATCH)
- `304 Not Modified`: GET request with If-None-Match - resource unchanged, ETag matches (no response body)
- `412 Precondition Failed`: ETag mismatch (If-Match), resource was modified since retrieval

### 2.4 Field Validation

**Email Field Validation:**
- Format: RFC 5322 format
- Maximum length: 254 characters
- Uniqueness: Case-insensitive uniqueness check (system-wide)

**String Length Validation:**
- Family name: Min 1 character, max 255 characters
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
- Family name: Case-insensitive unique across all families
- User email: Case-insensitive unique across all users (system-wide)
- Error on duplicate: `409 Conflict` with error code `DUPLICATE_FAMILY_NAME` or `DUPLICATE_EMAIL`

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
| POST /v1/auth/login | ✓ | ✓ | ✓ |
| POST /v1/auth/logout | ✓ | ✓ | ✓ |
| GET /v1/families | ✓ (all) | ✗ | ✗ |
| POST /v1/families | ✓ | ✗ | ✗ |
| GET /v1/families/{family_id} | ✓ | ✓ (own family) | ✓ (own family) |
| PATCH /v1/families/{family_id} | ✓ | ✗ | ✗ |
| PATCH /v1/families/{family_id}/soft-delete | ✓ | ✗ | ✗ |
| GET /v1/families/{family_id}/users | ✓ | ✓ (own family) | ✗ |
| GET /v1/families/{family_id}/users/{user_id} | ✓ | ✓ (own family) | ✗ |
| PATCH /v1/families/{family_id}/users/{user_id}/soft-delete | ✓ | ✓ (own family, cannot delete self) | ✗ |

**Notes:**
- SuperAdmin can access all families regardless of `family_id` in token
- FamilyAdmin and Member can only access their own family (family_id from token must match)
- FamilyAdmin cannot soft-delete themselves
- All operations require family to be Active (not SoftDeleted)

---

## 4. Resources & Endpoints

**Note:** All router endpoints MUST use centralized documentation classes for Swagger/OpenAPI documentation (Rule 10). Create documentation classes in `src/{module}/documentations/{module}_api_doc.py` with `summary` and `description` fields for each endpoint operation.

### 4.1 Resource Overview

| Resource | Description | Scope |
|----------|-------------|-------|
| Family | Tenant-level organizational unit | Global (SuperAdmin) or Family-scoped |
| User | Individual identity within a family | Family-scoped |

### 4.2 Endpoint Summary

| Method | Path | Purpose | Auth Required |
|--------|------|---------|---------------|
| POST | /v1/auth/login | Authenticate user and return JWT | No |
| POST | /v1/auth/logout | Logout user | Yes |
| GET | /v1/families | List all families | Yes (SuperAdmin) |
| POST | /v1/families | Create new family | Yes (SuperAdmin) |
| GET | /v1/families/{family_id} | Get family details | Yes |
| PATCH | /v1/families/{family_id} | Update family name | Yes (SuperAdmin) |
| PATCH | /v1/families/{family_id}/soft-delete | Soft delete family | Yes (SuperAdmin) |
| GET | /v1/families/{family_id}/users | List users in family | Yes (SuperAdmin/FamilyAdmin) |
| GET | /v1/families/{family_id}/users/{user_id} | Get user details | Yes (SuperAdmin/FamilyAdmin) |
| PATCH | /v1/families/{family_id}/users/{user_id}/soft-delete | Soft delete user | Yes (SuperAdmin/FamilyAdmin) |

---

## A. Authentication & Session

### A.1 POST /v1/auth/login

- **Purpose:** Authenticate user with email and password, return JWT token
- **Authentication:** Not required (public endpoint)
- **Authorization / Roles:** All users (Active status only)
- **Headers:**
  - **Request Headers:**
    - `Content-Type: application/json` (REQUIRED)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)

**Request Body**

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| email | string | Yes | User email address | RFC 5322 format, max 254 chars |
| password | string | Yes | User password | Plain text password (will be hashed server-side) |

**Request Body Example:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200 OK)**

| Field | Type | Description |
|-------|------|-------------|
| token | string | JWT access token |
| expires_in | integer | Token expiration time in seconds (3600 = 1 hour) |
| user | object | User information |
| user.id | string (UUID) | User ID |
| user.email | string | User email |
| user.name | string | User name |
| user.role | string | User role (superadmin, familyadmin, member) |
| user.family_id | string (UUID) \| null | Family ID (null for SuperAdmin) |
| user.family_name | string \| null | Family name (null for SuperAdmin) |

**Success Response Example:**
```json
{
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 3600,
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "familyadmin",
      "family_id": "660e8400-e29b-41d4-a716-446655440000",
      "family_name": "The Smith Family Vault"
    }
  },
  "message": "Login successful"
}
```

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 400 Bad Request | INVALID_REQUEST | Missing or invalid request body |
| 401 Unauthorized | UNAUTHENTICATED | Invalid credentials (email/password mismatch) |
| 401 Unauthorized | USER_NOT_ACTIVATED | User status is PendingActivation |
| 401 Unauthorized | USER_SOFT_DELETED | User is soft-deleted |
| 401 Unauthorized | FAMILY_SOFT_DELETED | User's family is soft-deleted |
| 422 Unprocessable Entity | VALIDATION_ERROR | Email format invalid |

**Error Response Example (401 - Invalid Credentials):**
```json
{
  "error": {
    "code": "UNAUTHENTICATED",
    "details": [{"field": "credentials", "issue": "Invalid email or password"}]
  },
  "message": "Authentication failed. Please check your credentials."
}
```

**Business Rules:**
- User must have status = `Active` (not `PendingActivation` or `SoftDeleted`)
- User's family must have status = `Active` (not `SoftDeleted`)
- Password must match stored hash
- Login must not leak whether email exists (generic error for invalid credentials)
- All user states (except PendingActivation) map to generic error messages
- PendingActivation users get specific message: "Account not activated. Please check your invitation email."
- **No rate limiting**: Login attempts are not rate-limited (no lockout after failed attempts)
- **No session timeout**: Sessions do not timeout (only JWT token expiration applies)

---

### A.2 POST /v1/auth/logout

- **Purpose:** Logout user and invalidate session
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** All authenticated users
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)

**Request Body:** None

**Success Response (200 OK)**

```json
{
  "data": null,
  "message": "Logout successful"
}
```

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |

**Business Rules:**
- Logout must always succeed, even if session was already invalid
- Token invalidation handled server-side (if token blacklist is implemented)

**Note:** Password reset functionality is out of scope for F-001. Users must contact administrators for password recovery. This aligns with the feature brief constraint: "Account recovery outside password reset" (out of scope).

---

## B. Families

### B.1 GET /v1/families

- **Purpose:** List all families with pagination, filtering, and sorting (SuperAdmin only)
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin only
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `If-None-Match`: ETag value from previous GET (optional, for cache validation)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier (optional for list endpoints, included for consistency)

**Path Parameters:** None

**Query Parameters**

**Note:** Query parameters MUST be defined using a query schema class with `Depends()` pattern (Rule 9), NOT individual `Query()` parameters in the router endpoint.

**Query Schema Class (REQUIRED):**
```python
class FamilyListQuery(BaseModel):
    """Query schema for listing families with pagination and filtering."""

    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    status: Optional[str] = Field(None, description="Filter by status: Active, SoftDeleted")
    sort_by: str = Field("created_at", description="Sort field: name, created_at, status")
    sort_order: str = Field("desc", description="Sort order: asc or desc")

    model_config = ConfigDict(from_attributes=True)
```

**Router Endpoint Pattern (REQUIRED):**
```python
@router.get("", response_model=StandardResponse[FamilyPaginatedResponse])
async def list_families(
    query: FamilyListQuery = Depends(FamilyListQuery),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_superadmin),
):
    """List families with pagination and filtering."""
    # Access via query.page, query.page_size, query.status, etc.
```

**Query Parameters Table (for documentation only):**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number (≥ 1) |
| page_size | integer | No | 20 | Page size (1-100) |
| status | string | No | null | Filter by status: Active, SoftDeleted |
| sort_by | string | No | created_at | Sort field: name, created_at, status |
| sort_order | string | No | desc | Sort order: asc or desc |

**Success Response (200 OK)**

**Pagination Structure:**
```json
{
  "data": {
    "items": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "name": "The Smith Family Vault",
        "status": "Active",
        "is_del": false,
        "created_at": "2024-01-20T10:30:00Z",
        "created_by": "550e8400-e29b-41d4-a716-446655440000",
        "updated_at": "2024-01-20T10:30:00Z",
        "updated_by": "550e8400-e29b-41d4-a716-446655440000",
        "deleted_at": null,
        "deleted_by": null
      }
    ],
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8,
    "next_page": "/v1/families?page=2&page_size=20&sort_by=created_at&status=Active",
    "prev_page": null
  },
  "message": "Families retrieved successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| items | array | Array of family objects |
| items[].id | string (UUID) | Family ID |
| items[].name | string | Family name |
| items[].status | string | Family status (Active, SoftDeleted) |
| items[].is_del | boolean | Soft-delete indicator |
| items[].created_at | string (datetime) | Creation timestamp (UTC, ISO 8601) |
| items[].created_by | string (UUID) | User ID who created the family |
| items[].updated_at | string (datetime) | Last update timestamp (UTC, ISO 8601) |
| items[].updated_by | string (UUID) | User ID who last updated the family |
| items[].deleted_at | string (datetime) \| null | Soft-delete timestamp (null if Active, UTC, ISO 8601) |
| items[].deleted_by | string (UUID) \| null | User ID who soft-deleted the family (null if Active) |
| total | integer | Total number of families |
| page | integer | Current page number |
| page_size | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| next_page | string \| null | URL for next page (or null) |
| prev_page | string \| null | URL for previous page (or null) |

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User is not SuperAdmin |
| 400 Bad Request | INVALID_REQUEST | Invalid query parameters |

**Business Rules:**
- Only SuperAdmin can list all families
- Soft-deleted families included based on `status` filter
- Pagination must be server-side
- Sorting must be stable and deterministic
- `next_page` and `prev_page` URLs must preserve all query parameters
- **Note:** ETag header is optional for list endpoints (included for consistency, but conditional requests are typically used for single resource GETs)

---

### B.2 POST /v1/families

- **Purpose:** Create a new family (SuperAdmin only)
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin only
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `Content-Type: application/json` (REQUIRED)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)

**Path Parameters:** None

**Query Parameters:** None

**Request Body**

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| name | string | Yes | Family name | Min 1 char, max 255 chars, case-insensitive unique across all families |

**Request Body Example:**
```json
{
  "name": "The Smith Family Vault"
}
```

**Success Response (201 Created)**

```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "The Smith Family Vault",
    "status": "Active",
    "is_del": false,
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "updated_at": "2024-01-20T10:30:00Z",
    "updated_by": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "Family created successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Family ID |
| name | string | Family name |
| status | string | Family status (Active) |
| is_del | boolean | Soft-delete indicator (false) |
| created_at | string (datetime) | Creation timestamp (UTC, ISO 8601) |
| created_by | string (UUID) | User ID who created the family |
| updated_at | string (datetime) | Last update timestamp (UTC, ISO 8601) |
| updated_by | string (UUID) | User ID who last updated the family |
| deleted_at | string (datetime) \| null | Soft-delete timestamp (null if Active, UTC, ISO 8601) |
| deleted_by | string (UUID) \| null | User ID who soft-deleted the family (null if Active) |

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User is not SuperAdmin |
| 400 Bad Request | VALIDATION_ERROR | Invalid request body or field validation failed |
| 409 Conflict | DUPLICATE_FAMILY_NAME | Family name already exists (case-insensitive) |

**Error Response Example (409 - Duplicate Name):**
```json
{
  "error": {
    "code": "DUPLICATE_FAMILY_NAME",
    "details": [{"field": "name", "issue": "A family with this name already exists."}]
  },
  "message": "Family name must be unique."
}
```

**Business Rules:**
- Only SuperAdmin can create families
- Family name must be unique system-wide (case-insensitive)
- Family is created with status = `Active`
- `created_by` and `updated_by` set to current user ID
- `created_at` and `updated_at` set to current timestamp (UTC)

---

### B.3 GET /v1/families/{family_id}

- **Purpose:** Get family details
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin (all families) or FamilyAdmin/Member (own family only)
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `If-None-Match`: ETag value from previous GET (optional, for cache validation)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier based on `updated_at` (e.g., `"20240120T103000Z"`)
    - `Last-Modified`: Timestamp of last modification (e.g., `Wed, 20 Jan 2024 10:30:00 GMT`)

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| family_id | string (UUID) | Yes | Family identifier |

**Query Parameters:** None

**Success Response (200 OK)**

```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "The Smith Family Vault",
    "status": "Active",
    "is_del": false,
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "updated_at": "2024-01-20T10:30:00Z",
    "updated_by": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "Family retrieved successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | Family ID |
| name | string | Family name |
| status | string | Family status (Active, SoftDeleted) |
| is_del | boolean | Soft-delete indicator |
| created_at | string (datetime) | Creation timestamp (UTC, ISO 8601) |
| created_by | string (UUID) | User ID who created the family |
| updated_at | string (datetime) | Last update timestamp (UTC, ISO 8601) |
| updated_by | string (UUID) | User ID who last updated the family |
| deleted_at | string (datetime) \| null | Soft-delete timestamp (null if Active, UTC, ISO 8601) |
| deleted_by | string (UUID) \| null | User ID who soft-deleted the family (null if Active) |

**Success Response (304 Not Modified)**

If `If-None-Match` header matches current ETag:
- Status: `304 Not Modified`
- No response body
- Headers: `X-Request-ID`, `ETag`, `Last-Modified`

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User cannot access this family (not SuperAdmin and not member of family) |
| 404 Not Found | FAMILY_NOT_FOUND | Family not found or soft-deleted |
| 400 Bad Request | INVALID_REQUEST | Invalid family_id format |

**Business Rules:**
- SuperAdmin can access any family
- FamilyAdmin and Member can only access their own family (family_id from token must match)
- If family is SoftDeleted, return 404 (not accessible)
- ETag based on `updated_at` timestamp

---

### B.4 PATCH /v1/families/{family_id}

- **Purpose:** Update family name (SuperAdmin only)
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin only
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `Content-Type: application/json` (REQUIRED)
    - `If-Match`: ETag value from GET response (REQUIRED for concurrency control)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: New resource version identifier after update (based on new `updated_at`)

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| family_id | string (UUID) | Yes | Family identifier |

**Query Parameters:** None

**Request Body**

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| name | string | Yes | Family name | Min 1 char, max 255 chars, case-insensitive unique across all families |

**Request Body Example:**
```json
{
  "name": "The Smith Family Vault - Updated"
}
```

**Success Response (200 OK)**

```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "The Smith Family Vault - Updated",
    "status": "Active",
    "is_del": false,
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "updated_at": "2024-01-20T10:35:00Z",
    "updated_by": "550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "Family updated successfully"
}
```

**Response Schema:** Same as GET /v1/families/{family_id}

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User is not SuperAdmin |
| 404 Not Found | FAMILY_NOT_FOUND | Family not found or soft-deleted |
| 400 Bad Request | VALIDATION_ERROR | Invalid request body or field validation failed |
| 409 Conflict | DUPLICATE_FAMILY_NAME | Family name already exists (case-insensitive) |
| 412 Precondition Failed | PRECONDITION_FAILED | ETag mismatch (If-Match header doesn't match current resource version) |
| 422 Unprocessable Entity | BUSINESS_RULE_FAILED | Family is SoftDeleted (cannot update) |

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
- Only SuperAdmin can update families
- Family name must be unique system-wide (case-insensitive)
- Cannot update if family is SoftDeleted
- `updated_at` and `updated_by` updated automatically
- ETag validation required (If-Match header)

---

### B.5 PATCH /v1/families/{family_id}/soft-delete

- **Purpose:** Soft delete family with cascade to users and documents (SuperAdmin only)
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin only
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `If-Match`: ETag value from GET response (REQUIRED for concurrency control)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| family_id | string (UUID) | Yes | Family identifier |

**Query Parameters:** None

**Request Body:** None

**Success Response (200 OK)**

```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "name": "The Smith Family Vault",
    "status": "SoftDeleted",
    "is_del": true,
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "updated_at": "2024-01-20T10:40:00Z",
    "updated_by": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_at": "2024-01-20T10:40:00Z",
    "deleted_by": "550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "Family soft-deleted successfully"
}
```

**Response Schema:** Same as GET /v1/families/{family_id}

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User is not SuperAdmin |
| 404 Not Found | FAMILY_NOT_FOUND | Family not found |
| 412 Precondition Failed | PRECONDITION_FAILED | ETag mismatch (If-Match header doesn't match current resource version) |
| 422 Unprocessable Entity | BUSINESS_RULE_FAILED | Family is already SoftDeleted |

**Business Rules:**
- Only SuperAdmin can soft-delete families
- Soft-delete cascades to:
  - All users in the family (set status = SoftDeleted, is_del = true)
  - All User_Role mappings (removed)
  - All documents in the family (soft-deleted, handled by document feature)
  - All pending invitations (invalidated)
- Cannot soft-delete if already SoftDeleted
- Operation is irreversible (no restore)
- `updated_at`, `updated_by`, `deleted_at`, and `deleted_by` updated automatically
- ETag validation required (If-Match header)

---

## C. Users

### C.1 GET /v1/families/{family_id}/users

- **Purpose:** List users within a family with pagination, filtering, and sorting
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin (all families) or FamilyAdmin (own family only)
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `If-None-Match`: ETag value from previous GET (optional, for cache validation)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| family_id | string (UUID) | Yes | Family identifier |

**Query Parameters**

**Note:** Query parameters MUST be defined using a query schema class with `Depends()` pattern (Rule 9), NOT individual `Query()` parameters in the router endpoint.

**Query Schema Class (REQUIRED):**
```python
class UserListQuery(BaseModel):
    """Query schema for listing users with pagination and filtering."""

    page: int = Field(1, ge=1, description="Page number (≥ 1)")
    page_size: int = Field(20, ge=1, le=100, description="Page size (1-100)")
    status: Optional[str] = Field(None, description="Filter by status: Active, PendingActivation, SoftDeleted")
    sort_by: str = Field("created_at", description="Sort field: name, email, status, created_at")
    sort_order: str = Field("desc", description="Sort order: asc or desc")

    model_config = ConfigDict(from_attributes=True)
```

**Router Endpoint Pattern (REQUIRED):**
```python
@router.get("", response_model=StandardResponse[UserPaginatedResponse])
async def list_users(
    family_id: UUID,
    query: UserListQuery = Depends(UserListQuery),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
):
    """List users with pagination and filtering."""
    # Access via query.page, query.page_size, query.status, etc.
```

**Query Parameters Table (for documentation only):**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| page | integer | No | 1 | Page number (≥ 1) |
| page_size | integer | No | 20 | Page size (1-100) |
| status | string | No | null | Filter by status: Active, PendingActivation, SoftDeleted |
| sort_by | string | No | created_at | Sort field: name, email, status, created_at |
| sort_order | string | No | desc | Sort order: asc or desc |

**Success Response (200 OK)**

**Pagination Structure:**
```json
{
  "data": {
    "items": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440000",
        "name": "John Doe",
        "email": "john@example.com",
        "status": "Active",
        "invite_sent_at": null,
        "invite_expire_at": null,
        "activated_at": "2024-01-20T10:30:00Z",
        "is_del": false,
        "roles_summary": ["familyadmin"],
        "activation_state_label": "Active",
        "is_activation_expired": false,
        "family_status": "Active",
        "created_at": "2024-01-20T10:30:00Z",
        "created_by": "550e8400-e29b-41d4-a716-446655440000",
        "updated_at": "2024-01-20T10:30:00Z",
        "updated_by": "550e8400-e29b-41d4-a716-446655440000",
        "deleted_at": null,
        "deleted_by": null
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3,
    "next_page": "/v1/families/660e8400-e29b-41d4-a716-446655440000/users?page=2&page_size=20&sort_by=created_at&status=Active",
    "prev_page": null
  },
  "message": "Users retrieved successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| items | array | Array of user objects |
| items[].id | string (UUID) | User ID |
| items[].name | string | User name |
| items[].email | string | User email |
| items[].status | string | User status (Active, PendingActivation, SoftDeleted) |
| items[].invite_sent_at | string (datetime) \| null | When invite was last sent (null if Active) |
| items[].invite_expire_at | string (datetime) \| null | Invite expiration timestamp (null if Active) |
| items[].activated_at | string (datetime) \| null | Activation timestamp (null if PendingActivation) |
| items[].is_del | boolean | Soft-delete indicator |
| items[].roles_summary | array (string) | List of role names assigned to user (single role per user) |
| items[].activation_state_label | string | Derived label from status + invite_expire_at |
| items[].is_activation_expired | boolean | True if invite expired (for PendingActivation only) |
| items[].family_status | string | Family status (Active, SoftDeleted) - used to disable operations if family is SoftDeleted |
| items[].created_at | string (datetime) | Creation timestamp (UTC, ISO 8601) |
| items[].created_by | string (UUID) | User ID who created the user |
| items[].updated_at | string (datetime) | Last update timestamp (UTC, ISO 8601) |
| items[].updated_by | string (UUID) | User ID who last updated the user |
| items[].deleted_at | string (datetime) \| null | Soft-delete timestamp (null if Active, UTC, ISO 8601) |
| items[].deleted_by | string (UUID) \| null | User ID who soft-deleted the user (null if Active) |
| total | integer | Total number of users |
| page | integer | Current page number |
| page_size | integer | Number of items per page |
| total_pages | integer | Total number of pages |
| next_page | string \| null | URL for next page (or null) |
| prev_page | string \| null | URL for previous page (or null) |

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User cannot access this family (not SuperAdmin and not member of family) |
| 404 Not Found | FAMILY_NOT_FOUND | Family not found or soft-deleted |
| 400 Bad Request | INVALID_REQUEST | Invalid query parameters |

**Business Rules:**
- SuperAdmin can list users in any family
- FamilyAdmin can only list users in their own family (family_id from token must match)
- Member role cannot list users
- Soft-deleted users included based on `status` filter
- Role assignments aggregated per user (roles_summary array - single role per user)
- Pagination must be server-side
- Sorting must be stable and deterministic
- If family is SoftDeleted, return 404 (not accessible)
- `next_page` and `prev_page` URLs must preserve all query parameters
- `family_status` field indicates family state (used to disable operations if SoftDeleted)
- **Note:** ETag header is optional for list endpoints (included for consistency, but conditional requests are typically used for single resource GETs)

---

### C.2 GET /v1/families/{family_id}/users/{user_id}

- **Purpose:** Get user details within a family
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin (all families) or FamilyAdmin (own family only)
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `If-None-Match`: ETag value from previous GET (optional, for cache validation)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)
    - `ETag`: Resource version identifier based on `updated_at` (e.g., `"20240120T103000Z"`)
    - `Last-Modified`: Timestamp of last modification (e.g., `Wed, 20 Jan 2024 10:30:00 GMT`)

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| family_id | string (UUID) | Yes | Family identifier |
| user_id | string (UUID) | Yes | User identifier |

**Query Parameters:** None

**Success Response (200 OK)**

```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "email": "john@example.com",
    "family_id": "660e8400-e29b-41d4-a716-446655440000",
    "status": "Active",
    "activated_at": "2024-01-20T10:30:00Z",
    "invite_sent_at": null,
    "invite_expire_at": null,
    "invited_by": "550e8400-e29b-41d4-a716-446655440000",
    "is_del": false,
    "roles_list": [
      {"id": "880e8400-e29b-41d4-a716-446655440000", "name": "familyadmin"}
    ],
    "allowed_role_management": true,
    "created_at": "2024-01-20T10:30:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "updated_at": "2024-01-20T10:30:00Z",
    "updated_by": "550e8400-e29b-41d4-a716-446655440000",
    "deleted_at": null,
    "deleted_by": null
  },
  "message": "User retrieved successfully"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| id | string (UUID) | User ID |
| name | string | User name |
| email | string | User email |
| family_id | string (UUID) | Family ID |
| status | string | User status (Active, PendingActivation, SoftDeleted) |
| activated_at | string (datetime) \| null | Activation timestamp (null if PendingActivation) |
| invite_sent_at | string (datetime) \| null | When invite was last sent (null if Active) |
| invite_expire_at | string (datetime) \| null | Invite expiration timestamp (null if Active) |
| invited_by | string (UUID) \| null | User ID who created the invitation (null if Active) |
| is_del | boolean | Soft-delete indicator |
| roles_list | array (object) | List of roles assigned to user (single role per user) |
| roles_list[].id | string (UUID) | Role ID |
| roles_list[].name | string | Role name |
| allowed_role_management | boolean | True if current user can manage roles (SuperAdmin or FamilyAdmin AND target user not SoftDeleted) |
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
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User cannot access this family (not SuperAdmin and not member of family) |
| 404 Not Found | USER_NOT_FOUND | User not found, soft-deleted, or not in specified family |
| 404 Not Found | FAMILY_NOT_FOUND | Family not found or soft-deleted |
| 400 Bad Request | INVALID_REQUEST | Invalid user_id or family_id format |

**Business Rules:**
- SuperAdmin can access users in any family
- FamilyAdmin can only access users in their own family (family_id from token must match)
- Member role cannot access user details
- If user is SoftDeleted, return 404 (not accessible)
- If family is SoftDeleted, return 404 (not accessible)
- `allowed_role_management` = true if (current user is SuperAdmin OR FamilyAdmin) AND target user is not SoftDeleted
- ETag based on `updated_at` timestamp

---

### C.3 PATCH /v1/families/{family_id}/users/{user_id}/soft-delete

- **Purpose:** Soft delete user with cascade to documents (SuperAdmin or FamilyAdmin)
- **Authentication:** Required (JWT Bearer token)
- **Authorization / Roles:** SuperAdmin (all families) or FamilyAdmin (own family only, cannot delete self)
- **Headers:**
  - **Request Headers:**
    - `Authorization: Bearer <token>` (REQUIRED)
    - `If-Match`: ETag value from GET response (REQUIRED for concurrency control)
  - **Response Headers (REQUIRED):**
    - `X-Request-ID`: Unique request identifier (e.g., `req_abc123xyz789`)

**Path Parameters**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| family_id | string (UUID) | Yes | Family identifier |
| user_id | string (UUID) | Yes | User identifier |

**Query Parameters:** None

**Request Body:** None

**Success Response (200 OK)**

```json
{
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "email": "john@example.com",
    "family_id": "660e8400-e29b-41d4-a716-446655440000",
    "status": "SoftDeleted",
    "is_del": true,
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T10:40:00Z",
    "deleted_at": "2024-01-20T10:40:00Z",
    "deleted_by": "550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "User soft-deleted successfully"
}
```

**Response Schema:** Same as GET /v1/families/{family_id}/users/{user_id} (with status = SoftDeleted, is_del = true)

**Error Responses**

| HTTP Status | Error Code | When |
|-------------|------------|------|
| 401 Unauthorized | UNAUTHENTICATED | Missing or invalid token |
| 403 Forbidden | INSUFFICIENT_PERMISSIONS | User cannot access this family (not SuperAdmin and not member of family) OR FamilyAdmin trying to delete self |
| 404 Not Found | USER_NOT_FOUND | User not found, already soft-deleted, or not in specified family |
| 404 Not Found | FAMILY_NOT_FOUND | Family not found or soft-deleted |
| 412 Precondition Failed | PRECONDITION_FAILED | ETag mismatch (If-Match header doesn't match current resource version) |
| 422 Unprocessable Entity | BUSINESS_RULE_FAILED | User is already SoftDeleted OR Family is SoftDeleted |

**Error Response Example (403 - Cannot Delete Self):**
```json
{
  "error": {
    "code": "INSUFFICIENT_PERMISSIONS",
    "details": [{"field": "user", "issue": "You cannot soft-delete yourself."}]
  },
  "message": "Operation not allowed."
}
```

**Business Rules:**
- SuperAdmin can soft-delete users in any family
- FamilyAdmin can soft-delete users in their own family (family_id from token must match)
- FamilyAdmin cannot soft-delete themselves
- Soft-delete cascades to:
  - All user-owned documents (soft-deleted, handled by document feature)
  - All User_Role mappings (removed)
  - Invite tokens invalidated (if PendingActivation)
- Cannot soft-delete if user is already SoftDeleted
- Cannot soft-delete if family is SoftDeleted
- Operation is irreversible (no restore)
- `updated_at`, `deleted_at`, and `deleted_by` updated automatically
- ETag validation required (If-Match header)

---

## 5. Open Questions

1. Should password history be stored in a separate table or embedded in user record?
2. Should there be rate limiting on login attempts?
3. Should there be audit logging for family and user operations?

---

## 6. Assumptions

1. JWT tokens are stateless and do not require server-side session storage
2. Token blacklist (if implemented) is handled separately from this API spec
3. Password hashing is handled server-side (bcrypt/argon2)
4. Email service (SMTP) is available for invitation emails
5. Soft-delete cascade to documents is handled by document feature (F-003)
6. All datetime fields are stored and returned in UTC timezone
7. Family name uniqueness check is case-insensitive
8. User email uniqueness check is case-insensitive and system-wide

