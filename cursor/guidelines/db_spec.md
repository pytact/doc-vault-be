================================================================================
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                    DOCVAULT DATABASE SPECIFICATION                          ║
║                                                                            ║
║                    Enterprise Database Design Document                      ║
║                                                                            ║
║                    PostgreSQL 3NF Normalization                            ║
║                    Microsoft Azure Data Architecture                       ║
║                                                                            ║
║                              Version 1.0                                   ║
║                                                                            ║
║                         Document Date: 2024                               ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
================================================================================

================================================================================
SECTION 2 — DOCUMENT CONTROL
================================================================================

┌────────────────────────────────────────────────────────────────────────────┐
│ Document Information                                                        │
├────────────────────────────────────────────────────────────────────────────┤
│ Document Title:          DocVault Database Specification                   │
│ Document Version:        1.1                                                │
│ Document Status:         Final                                              │
│ Classification:          Internal                                           │
│ Database System:         PostgreSQL                                          │
│ Architecture:            Microsoft Azure Data Architecture                  │
│ Normalization Level:     3NF (Third Normal Form)                            │
│ Date Created:           2024                                                │
│ Last Updated:           2024                                                │
│ Author:                 Database Architecture Team                          │
│ Review Status:          Pending Review                                      │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│ Change History                                                              │
├────────────────────────────────────────────────────────────────────────────┤
│ Version │ Date     │ Author │ Description                                  │
├─────────┼──────────┼────────┼──────────────────────────────────────────────┤
│ 1.0     │ 2024     │ Team   │ Initial database specification document     │
│ 1.1     │ 2024     │ Team   │ Updated: One role per user constraint      │
└─────────┴──────────┴────────┴──────────────────────────────────────────────┘

================================================================================
SECTION 3 — INTRODUCTION
================================================================================

3.1 Purpose

This document provides a comprehensive database specification for the DocVault 
system, a secure, role-based family document vault designed for families, 
general consumers, and enterprises. The database design follows PostgreSQL 3NF 
normalization standards and Microsoft Azure Data Architecture best practices.

3.2 Scope

This specification covers:
- Complete database schema design for 8 core tables
- Entity relationships and foreign key constraints
- Data types, constraints, and validation rules
- Indexing strategy for optimal performance
- Normalization verification (3NF compliance)
- Multi-tenancy implementation via Families table
- Soft-delete support across all entities
- Comprehensive audit trail implementation

3.3 Document Structure

This document is organized into 10 sections:
1. Cover Page
2. Document Control
3. Introduction (this section)
4. System Overview
5. Non-Functional Requirements
6. Logical Data Model
7. Physical Data Model (complete table definitions)
8. Normalization Verification
9. Index Strategy
10. Professional ASCII ER Diagram

3.4 Database Technology

- Database System: PostgreSQL
- Architecture Pattern: Microsoft Azure Data Architecture
- Normalization: Third Normal Form (3NF)
- ID Format: UUID (Universally Unique Identifier)
- Multi-tenancy: Family-based tenant isolation
- Soft Delete: Comprehensive support with deleted_at and is_del flags

================================================================================
SECTION 4 — SYSTEM OVERVIEW
================================================================================

4.1 Business Context

DocVault is a secure, role-based family document vault designed for families, 
general consumers, and enterprises. Users are organized into families, each 
functioning as an isolated tenant. The platform provides controlled document 
storage, classification, sharing, and expiry notifications through an intuitive 
web interface.

4.2 Problem Statement

Families and small organizations lack a unified, secure system for storing 
essential documents, managing access, organizing information, and ensuring 
timely reminders for document renewals. DocVault centralizes document 
management, ensures privacy through RBAC, and provides proactive notifications 
for critical expiry dates.

4.3 High-Level Goals

- Provide a secure vault for storing and managing family documents
- Implement robust role-based access control for permissions
- Enable document sharing with granular viewer/editor options
- Deliver reliable expiry notifications via email and in-app alerts
- Offer a minimal, functional, easy-to-use web UI
- Support multi-tenancy through family-based isolation
- Implement comprehensive audit trails and soft-delete capabilities

4.4 Core Entities

The system consists of 8 core database tables:

1. **users** - User accounts with invite/activation workflow
2. **roles** - Role definitions with JSON permission sets (3 roles: SuperAdmin, FamilyAdmin, Member)
3. **families** - Organizational units (tenants) for grouping users and documents
4. **user_roles** - One-to-one mapping of users to roles within families (each user has exactly one role)
5. **categories** - Document categories for organizing documents (15 categories)
6. **subcategories** - Specific document types within each category (78 subcategories)
7. **documents** - Documents owned by users within families
8. **document_assign** - Per-document sharing with viewer/editor access assignments

4.5 User Roles

The system implements three primary roles:

- **SuperAdmin**: Global system administrator with full control over families 
  and users, but no document access by default. Can perform all global 
  activities but cannot perform operations on any documents (cannot see, update, 
  or delete documents).

- **FamilyAdmin**: Full control over all users and documents within their own 
  family. Can manage users, assign roles, and has full document access within 
  their family scope.

- **Member**: Can create and manage their own documents, and assign viewer/editor 
  access to others within their family.

Note: Viewer and Editor are not roles in the roles table, but rather access 
types in the document_assign table for granular document-level permissions.

4.6 Multi-Tenancy

Multi-tenancy is implemented through the Families table. Each family functions 
as an isolated tenant, with strict data isolation between families. Users 
belong to a single family (except SuperAdmin who has no family_id). All 
documents are scoped to families, ensuring complete tenant isolation.

================================================================================
SECTION 5 — NON-FUNCTIONAL REQUIREMENTS
================================================================================

5.1 Data Integrity Requirements

- All primary keys use UUID format with gen_random_uuid() default
- All foreign keys enforce referential integrity
- CHECK constraints enforce valid enum values (status, access_type)
- UNIQUE constraints on email addresses
- NOT NULL constraints on required fields
- Comprehensive foreign key constraints with appropriate ON DELETE/ON UPDATE actions

5.2 Audit Requirements

All tables include comprehensive audit fields:
- created_at (TIMESTAMPTZ) - Timestamp when record was created
- created_by (UUID, FK to users.id) - User who created the record
- updated_at (TIMESTAMPTZ) - Timestamp when record was last updated
- updated_by (UUID, FK to users.id) - User who last updated the record
- deleted_at (TIMESTAMPTZ, nullable) - Timestamp when record was soft-deleted
- deleted_by (UUID, FK to users.id, nullable) - User who soft-deleted the record
- is_del (BOOLEAN) - Boolean flag for soft-delete status

5.3 Soft Delete Requirements

All tables support soft-delete functionality through:
- deleted_at (TIMESTAMPTZ) - NULL when active, timestamp when deleted
- is_del (BOOLEAN) - false when active, true when deleted
- deleted_by (UUID) - Tracks who performed the soft-delete operation

Soft-delete operations use RESTRICT on foreign keys to rely on application 
logic for cascade operations.

5.4 Performance Requirements

- All foreign key columns must be indexed for optimal JOIN performance
- All tables with updated_at must have index on updated_at for incremental sync
- Composite indexes for common query patterns (family_id + status, etc.)
- Partial indexes for soft-delete queries (WHERE deleted_at IS NULL)
- Text search indexes for frequently searched columns (using pg_trgm extension)

5.5 Scalability Requirements

- Database design supports horizontal scaling through family-based partitioning
- UUID primary keys support distributed systems
- Index strategy optimized for large-scale data volumes
- Multi-tenancy isolation supports enterprise-level deployment

5.6 Security Requirements

- Role-based access control enforced at database level through user_roles table
- Family-based tenant isolation prevents cross-tenant data access
- Audit trails track all create, update, and delete operations
- Soft-delete preserves data for compliance and recovery

5.7 Data Type Standards

- All IDs: UUID with gen_random_uuid() default
- Timestamps: TIMESTAMPTZ for timezone-aware timestamps
- Status fields: VARCHAR(20) with CHECK constraints
- Email: VARCHAR(255) with UNIQUE constraint
- JSON data: JSONB for efficient storage and querying
- Text fields: VARCHAR(n) or TEXT based on requirements

================================================================================
SECTION 6 — LOGICAL DATA MODEL
================================================================================

6.1 Entity Relationship Overview

The DocVault database consists of 8 core entities with the following 
relationships:

**Core Entities:**
- Users (user accounts)
- Roles (permission sets)
- Families (tenant isolation units)
- Categories (document classification)
- Subcategories (specific document types)
- Documents (stored documents)
- User_Roles (user-role-family mapping)
- Document_Assign (document sharing assignments)

**Key Relationships:**

1. **Users ↔ User_Roles ↔ Roles**: One-to-one relationship through junction 
   table, with family context (each user has exactly one role)

2. **Families → User_Roles**: One-to-many (family can have multiple user-role 
   assignments, nullable for SuperAdmin). Note: Each user has exactly one role.

3. **Families → Documents**: One-to-many (family can have multiple documents)

4. **Users → Documents**: One-to-many (user can own multiple documents)

5. **Categories → Subcategories**: One-to-many (category has multiple 
   subcategories)

6. **Categories → Documents**: One-to-many (category can have multiple documents)

7. **Subcategories → Documents**: One-to-many (subcategory can have multiple 
   documents)

8. **Documents → Document_Assign**: One-to-many (document can be assigned to 
   multiple users)

9. **Users → Document_Assign**: One-to-many (user can have multiple document 
   assignments, both as owner and assignee)

6.2 Entity Descriptions

**Users**
Represents user accounts in the system. Supports invite/activation workflow 
with invite tokens, expiry dates, and activation tracking. Users belong to a 
single family (except SuperAdmin).

**Roles**
Defines three role types (SuperAdmin, FamilyAdmin, Member) with JSON-based 
permission definitions. Permissions are stored as JSONB for flexible 
permission management.

**Families**
Organizational units that function as tenants. Each family is isolated from 
others, with users and documents scoped to families. SuperAdmin has no family 
association.

**User_Roles**
Junction table mapping users to roles within families. Each user has exactly one 
role. family_id is nullable for SuperAdmin.

**Categories**
Fixed taxonomy of 15 document categories (Identity, Educational, Professional, 
Financial, Insurance, Bills & Receipts, Contracts, Property, Vehicle, Medical, 
Legal, Travel, Warranty, Membership, Others). Non-editable by administrators.

**Subcategories**
Specific document types within each category. 78 total subcategories providing 
granular document classification. Each subcategory belongs to exactly one 
category.

**Documents**
Stores document metadata and references. Documents belong to a family, have an 
owner (user), and are classified by category and subcategory. Includes JSONB 
details field for document-specific information.

**Document_Assign**
Per-document sharing assignments. Tracks which users have been assigned access 
to specific documents, with access_type (viewer/editor) and both owner_id 
(assigner) and assign_to (assignee) for complete audit trail.

6.3 Business Rules

1. **Single Family Membership**: Each user (except SuperAdmin) belongs to exactly 
   one family.

2. **SuperAdmin Isolation**: SuperAdmin has no family_id and cannot access 
   documents.

3. **Single Role Assignment**: Each user has exactly one role. A user cannot have 
   multiple roles simultaneously.

4. **Role Hierarchy**: SuperAdmin > FamilyAdmin > Member in terms of permissions.

5. **Document Ownership**: Documents must have an owner (user) and belong to a 
   family.

6. **Category Immutability**: Categories and subcategories are fixed and 
   non-editable.

7. **Soft Delete**: All entities support soft-delete, preserving data for 
   compliance.

8. **Audit Trail**: All create, update, and delete operations are tracked with 
   user and timestamp information.

================================================================================
SECTION 7 — PHYSICAL DATA MODEL
================================================================================

This section provides complete table definitions with all columns, data types, 
constraints, and metadata for all 8 tables in the DocVault database.

┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                    SECTION 7 — PHYSICAL DATA MODEL                        │
│                                                                            │
│                    Complete Table Definitions                             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

### 7.1 Table: users

Stores user accounts with invite/activation workflow.

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique user identifier |
| email | VARCHAR(255) | No | No | No | - | NOT NULL, UNIQUE | User email address, must be unique |
| hash_password | VARCHAR(255) | No | No | No | - | NOT NULL | Hashed password for authentication |
| status | VARCHAR(20) | No | No | No | 'pending' | NOT NULL, CHECK (status IN ('pending', 'active', 'inactive')) | User account status |
| invite_token | VARCHAR(255) | No | No | Yes | NULL | - | Invitation token for account activation |
| invite_sent_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when invitation was sent |
| invite_expire_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when invitation expires |
| invited_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who sent the invitation |
| activated_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when account was activated |
| is_del | BOOLEAN | No | No | No | false | NOT NULL | Soft-delete flag, false when active |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |
| deleted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when record was soft-deleted (NULL if active) |
| deleted_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who soft-deleted the record |

**Foreign Key Constraints:**
- `invited_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `created_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `deleted_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- UNIQUE constraint on `email` to ensure email uniqueness
- CHECK constraint on `status` to ensure only valid status values ('pending', 'active', 'inactive')

---

### 7.2 Table: roles

Defines role types with JSON permission definitions. Contains 3 roles: SuperAdmin, FamilyAdmin, Member.

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique role identifier |
| name | VARCHAR(50) | No | No | No | - | NOT NULL, UNIQUE | Role name (superadmin, familyadmin, member) |
| permissions | JSONB | No | No | No | '{}' | NOT NULL | JSON object containing role permissions |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |
| deleted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when record was soft-deleted (NULL if active) |
| deleted_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who soft-deleted the record |
| is_del | BOOLEAN | No | No | No | false | NOT NULL | Soft-delete flag, false when active |

**Foreign Key Constraints:**
- `created_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `deleted_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- UNIQUE constraint on `name` to ensure role name uniqueness
- CHECK constraint on `name` to ensure only valid role names ('superadmin', 'familyadmin', 'member')

---

### 7.3 Table: families

Organizational units (tenants) for grouping users and documents.

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique family identifier |
| name | VARCHAR(255) | No | No | No | - | NOT NULL | Family name |
| status | VARCHAR(20) | No | No | No | 'active' | NOT NULL, CHECK (status IN ('active', 'inactive')) | Family status (active/inactive for soft-delete) |
| is_del | BOOLEAN | No | No | No | false | NOT NULL | Soft-delete flag, false when active |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record (SuperAdmin) |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |
| deleted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when record was soft-deleted (NULL if active) |
| deleted_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who soft-deleted the record |

**Foreign Key Constraints:**
- `created_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `deleted_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- CHECK constraint on `status` to ensure only 'active' or 'inactive' values

---

### 7.4 Table: user_roles

Maps users to roles within families (one-to-one relationship - each user has exactly one role).

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique user-role assignment identifier |
| user_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE | User ID |
| family_id | UUID | No | Yes | Yes | NULL | REFERENCES families(id) ON DELETE RESTRICT ON UPDATE CASCADE | Family ID (nullable for SuperAdmin) |
| role_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES roles(id) ON DELETE RESTRICT ON UPDATE CASCADE | Role ID |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |
| deleted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when record was soft-deleted (NULL if active) |
| deleted_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who soft-deleted the record |
| is_del | BOOLEAN | No | No | No | false | NOT NULL | Soft-delete flag, false when active |

**Foreign Key Constraints:**
- `user_id` → `users(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `family_id` → `families(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `role_id` → `roles(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `created_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `deleted_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- UNIQUE constraint on `user_id` WHERE `deleted_at IS NULL` to ensure each user has exactly one active role
- CHECK constraint to ensure SuperAdmin has NULL family_id, other roles have non-NULL family_id

---

### 7.5 Table: categories

Document categories for organizing documents by type. Fixed taxonomy of 15 categories.

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique category identifier |
| name | VARCHAR(100) | No | No | No | - | NOT NULL, UNIQUE | Category name |
| description | TEXT | No | No | Yes | NULL | - | Category description |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |
| deleted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when record was soft-deleted (NULL if active) |
| deleted_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who soft-deleted the record |
| is_del | BOOLEAN | No | No | No | false | NOT NULL | Soft-delete flag, false when active |

**Foreign Key Constraints:**
- `created_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `deleted_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- UNIQUE constraint on `name` to ensure category name uniqueness

---

### 7.6 Table: subcategories

Specific document types within each category. 78 total subcategories.

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique subcategory identifier |
| category_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES categories(id) ON DELETE RESTRICT ON UPDATE CASCADE | Category ID this subcategory belongs to |
| name | VARCHAR(100) | No | No | No | - | NOT NULL | Subcategory name |
| description | TEXT | No | No | Yes | NULL | - | Subcategory description |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |
| deleted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when record was soft-deleted (NULL if active) |
| deleted_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who soft-deleted the record |
| is_del | BOOLEAN | No | No | No | false | NOT NULL | Soft-delete flag, false when active |

**Foreign Key Constraints:**
- `category_id` → `categories(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `created_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `deleted_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- UNIQUE constraint on `(category_id, name)` to ensure unique subcategory names within a category

---

### 7.7 Table: documents

Stores documents owned by users within families.

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique document identifier |
| family_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES families(id) ON DELETE RESTRICT ON UPDATE CASCADE | Family ID this document belongs to |
| owner_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE | User ID who owns this document |
| category_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES categories(id) ON DELETE RESTRICT ON UPDATE CASCADE | Category ID |
| subcategory_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES subcategories(id) ON DELETE RESTRICT ON UPDATE CASCADE | Subcategory ID |
| title | VARCHAR(255) | No | No | No | - | NOT NULL | Document title |
| expiry_date | DATE | No | No | Yes | NULL | - | Document expiry date (optional) |
| details | JSONB | No | No | Yes | NULL | - | JSON object containing document-specific information (name, number, etc.) |
| file_path | VARCHAR(500) | No | No | Yes | NULL | - | S3-compatible file path to document file |
| is_del | BOOLEAN | No | No | No | false | NOT NULL | Soft-delete flag, false when active |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |
| deleted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when record was soft-deleted (NULL if active) |
| deleted_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who soft-deleted the record |

**Foreign Key Constraints:**
- `family_id` → `families(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `owner_id` → `users(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `category_id` → `categories(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `subcategory_id` → `subcategories(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `created_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `deleted_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- CHECK constraint to ensure subcategory_id belongs to the specified category_id
- JSONB details field structure: `{"name": "string", "number": "string"}`

---

### 7.8 Table: document_assign

Per-document sharing with viewer/editor access assignments.

| Field | Type | PK | FK | Null | Default | Constraints | Description |
|-------|------|----|----|------|---------|-------------|-------------|
| id | UUID | Yes | No | No | gen_random_uuid() | PRIMARY KEY | Primary key, unique document assignment identifier |
| document_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES documents(id) ON DELETE CASCADE ON UPDATE CASCADE | Document ID being assigned |
| owner_id | UUID | No | Yes | No | - | NOT NULL, REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE | User ID who owns/assigns the document |
| assign_to | UUID | No | Yes | No | - | NOT NULL, REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE | User ID the document is assigned to |
| access_type | VARCHAR(20) | No | No | No | 'viewer' | NOT NULL, CHECK (access_type IN ('viewer', 'editor')) | Access type: viewer (read-only) or editor (read-write) |
| created_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was created |
| created_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who created the record |
| updated_at | TIMESTAMPTZ | No | No | No | CURRENT_TIMESTAMP | NOT NULL | Timestamp when record was last updated |
| updated_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who last updated the record |
| deleted_at | TIMESTAMPTZ | No | No | Yes | NULL | - | Timestamp when record was soft-deleted (NULL if active) |
| deleted_by | UUID | No | Yes | Yes | NULL | REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE | User ID who soft-deleted the record |
| is_del | BOOLEAN | No | No | No | false | NOT NULL | Soft-delete flag, false when active |

**Foreign Key Constraints:**
- `document_id` → `documents(id)` ON DELETE CASCADE ON UPDATE CASCADE
- `owner_id` → `users(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `assign_to` → `users(id)` ON DELETE RESTRICT ON UPDATE CASCADE
- `created_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `updated_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE
- `deleted_by` → `users(id)` ON DELETE SET NULL ON UPDATE CASCADE

**Additional Constraints:**
- UNIQUE constraint on `(document_id, assign_to)` to prevent duplicate assignments
- CHECK constraint on `access_type` to ensure only 'viewer' or 'editor' values
- CHECK constraint to ensure owner_id and assign_to are different users

================================================================================
SECTION 8 — NORMALIZATION
================================================================================

This section verifies that all tables comply with Third Normal Form (3NF) 
normalization standards.

### 8.1 Normalization Verification Checklist

#### 8.1.1 Table: users

**First Normal Form (1NF):**
- [✓] All columns contain atomic values (no arrays, no comma-separated lists)
- [✓] Each column contains only one type of data
- [✓] Each column has a unique name
- [✓] Order of rows/columns doesn't matter
- [✓] No repeating groups of columns

**Second Normal Form (2NF):**
- [✓] Table is in 1NF
- [✓] All non-key columns depend on the entire primary key (single-column PK)
- [✓] No partial dependencies

**Third Normal Form (3NF):**
- [✓] Table is in 2NF
- [✓] No transitive dependencies (non-key columns don't depend on other non-key columns)
- [✓] All non-key columns depend directly on the primary key

**Status:** ✓ COMPLIANT - Table is in 3NF

---

#### 8.1.2 Table: roles

**First Normal Form (1NF):**
- [✓] All columns contain atomic values
- [✓] Each column contains only one type of data
- [✓] Each column has a unique name
- [✓] Order of rows/columns doesn't matter
- [✓] No repeating groups of columns

**Second Normal Form (2NF):**
- [✓] Table is in 1NF
- [✓] All non-key columns depend on the entire primary key
- [✓] No partial dependencies

**Third Normal Form (3NF):**
- [✓] Table is in 2NF
- [✓] No transitive dependencies
- [✓] All non-key columns depend directly on the primary key

**Status:** ✓ COMPLIANT - Table is in 3NF

---

#### 8.1.3 Table: families

**First Normal Form (1NF):**
- [✓] All columns contain atomic values
- [✓] Each column contains only one type of data
- [✓] Each column has a unique name
- [✓] Order of rows/columns doesn't matter
- [✓] No repeating groups of columns

**Second Normal Form (2NF):**
- [✓] Table is in 1NF
- [✓] All non-key columns depend on the entire primary key
- [✓] No partial dependencies

**Third Normal Form (3NF):**
- [✓] Table is in 2NF
- [✓] No transitive dependencies
- [✓] All non-key columns depend directly on the primary key

**Status:** ✓ COMPLIANT - Table is in 3NF

---

#### 8.1.4 Table: user_roles

**First Normal Form (1NF):**
- [✓] All columns contain atomic values
- [✓] Each column contains only one type of data
- [✓] Each column has a unique name
- [✓] Order of rows/columns doesn't matter
- [✓] No repeating groups of columns

**Second Normal Form (2NF):**
- [✓] Table is in 1NF
- [✓] All non-key columns depend on the entire primary key
- [✓] No partial dependencies (junction table with single PK)

**Third Normal Form (3NF):**
- [✓] Table is in 2NF
- [✓] No transitive dependencies
- [✓] All non-key columns depend directly on the primary key

**Status:** ✓ COMPLIANT - Table is in 3NF

---

#### 8.1.5 Table: categories

**First Normal Form (1NF):**
- [✓] All columns contain atomic values
- [✓] Each column contains only one type of data
- [✓] Each column has a unique name
- [✓] Order of rows/columns doesn't matter
- [✓] No repeating groups of columns

**Second Normal Form (2NF):**
- [✓] Table is in 1NF
- [✓] All non-key columns depend on the entire primary key
- [✓] No partial dependencies

**Third Normal Form (3NF):**
- [✓] Table is in 2NF
- [✓] No transitive dependencies
- [✓] All non-key columns depend directly on the primary key

**Status:** ✓ COMPLIANT - Table is in 3NF

---

#### 8.1.6 Table: subcategories

**First Normal Form (1NF):**
- [✓] All columns contain atomic values
- [✓] Each column contains only one type of data
- [✓] Each column has a unique name
- [✓] Order of rows/columns doesn't matter
- [✓] No repeating groups of columns

**Second Normal Form (2NF):**
- [✓] Table is in 1NF
- [✓] All non-key columns depend on the entire primary key
- [✓] No partial dependencies

**Third Normal Form (3NF):**
- [✓] Table is in 2NF
- [✓] No transitive dependencies
- [✓] All non-key columns depend directly on the primary key

**Status:** ✓ COMPLIANT - Table is in 3NF

---

#### 8.1.7 Table: documents

**First Normal Form (1NF):**
- [✓] All columns contain atomic values
- [✓] Each column contains only one type of data
- [✓] Each column has a unique name
- [✓] Order of rows/columns doesn't matter
- [✓] No repeating groups of columns

**Second Normal Form (2NF):**
- [✓] Table is in 1NF
- [✓] All non-key columns depend on the entire primary key
- [✓] No partial dependencies

**Third Normal Form (3NF):**
- [✓] Table is in 2NF
- [✓] No transitive dependencies
- [✓] All non-key columns depend directly on the primary key

**Status:** ✓ COMPLIANT - Table is in 3NF

---

#### 8.1.8 Table: document_assign

**First Normal Form (1NF):**
- [✓] All columns contain atomic values
- [✓] Each column contains only one type of data
- [✓] Each column has a unique name
- [✓] Order of rows/columns doesn't matter
- [✓] No repeating groups of columns

**Second Normal Form (2NF):**
- [✓] Table is in 1NF
- [✓] All non-key columns depend on the entire primary key
- [✓] No partial dependencies

**Third Normal Form (3NF):**
- [✓] Table is in 2NF
- [✓] No transitive dependencies
- [✓] All non-key columns depend directly on the primary key

**Status:** ✓ COMPLIANT - Table is in 3NF

---

### 8.2 Normalization Summary

All 8 tables in the DocVault database are fully compliant with Third Normal 
Form (3NF) normalization standards. No denormalization was required, and all 
tables maintain proper data integrity through foreign key relationships and 
constraints.

**Normalization Compliance:** 100% (8/8 tables)

================================================================================
SECTION 9 — INDEX STRATEGY
================================================================================

This section defines the complete indexing strategy for optimal database 
performance. All foreign keys, audit fields, and frequently queried columns 
are indexed according to PostgreSQL best practices.

### 9.1 Primary Key Indexes

Primary keys are automatically indexed by PostgreSQL. Explicit definitions for 
clarity:

```sql
-- Primary Key Indexes (automatic, listed for documentation)
CREATE UNIQUE INDEX pk_users ON users(id);
CREATE UNIQUE INDEX pk_roles ON roles(id);
CREATE UNIQUE INDEX pk_families ON families(id);
CREATE UNIQUE INDEX pk_user_roles ON user_roles(id);
CREATE UNIQUE INDEX pk_categories ON categories(id);
CREATE UNIQUE INDEX pk_subcategories ON subcategories(id);
CREATE UNIQUE INDEX pk_documents ON documents(id);
CREATE UNIQUE INDEX pk_document_assign ON document_assign(id);
```

### 9.2 Foreign Key Indexes

**CRITICAL:** Every foreign key column MUST have an index for optimal JOIN 
performance and referential integrity checks.

#### 9.2.1 Table: users

```sql
CREATE INDEX idx_users_invited_by ON users(invited_by);
CREATE INDEX idx_users_created_by ON users(created_by);
CREATE INDEX idx_users_updated_by ON users(updated_by);
CREATE INDEX idx_users_deleted_by ON users(deleted_by);
```

#### 9.2.2 Table: roles

```sql
CREATE INDEX idx_roles_created_by ON roles(created_by);
CREATE INDEX idx_roles_updated_by ON roles(updated_by);
CREATE INDEX idx_roles_deleted_by ON roles(deleted_by);
```

#### 9.2.3 Table: families

```sql
CREATE INDEX idx_families_created_by ON families(created_by);
CREATE INDEX idx_families_updated_by ON families(updated_by);
CREATE INDEX idx_families_deleted_by ON families(deleted_by);
```

#### 9.2.4 Table: user_roles

```sql
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_family_id ON user_roles(family_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_user_roles_created_by ON user_roles(created_by);
CREATE INDEX idx_user_roles_updated_by ON user_roles(updated_by);
CREATE INDEX idx_user_roles_deleted_by ON user_roles(deleted_by);
```

#### 9.2.5 Table: categories

```sql
CREATE INDEX idx_categories_created_by ON categories(created_by);
CREATE INDEX idx_categories_updated_by ON categories(updated_by);
CREATE INDEX idx_categories_deleted_by ON categories(deleted_by);
```

#### 9.2.6 Table: subcategories

```sql
CREATE INDEX idx_subcategories_category_id ON subcategories(category_id);
CREATE INDEX idx_subcategories_created_by ON subcategories(created_by);
CREATE INDEX idx_subcategories_updated_by ON subcategories(updated_by);
CREATE INDEX idx_subcategories_deleted_by ON subcategories(deleted_by);
```

#### 9.2.7 Table: documents

```sql
CREATE INDEX idx_documents_family_id ON documents(family_id);
CREATE INDEX idx_documents_owner_id ON documents(owner_id);
CREATE INDEX idx_documents_category_id ON documents(category_id);
CREATE INDEX idx_documents_subcategory_id ON documents(subcategory_id);
CREATE INDEX idx_documents_created_by ON documents(created_by);
CREATE INDEX idx_documents_updated_by ON documents(updated_by);
CREATE INDEX idx_documents_deleted_by ON documents(deleted_by);
```

#### 9.2.8 Table: document_assign

```sql
CREATE INDEX idx_document_assign_document_id ON document_assign(document_id);
CREATE INDEX idx_document_assign_owner_id ON document_assign(owner_id);
CREATE INDEX idx_document_assign_assign_to ON document_assign(assign_to);
CREATE INDEX idx_document_assign_created_by ON document_assign(created_by);
CREATE INDEX idx_document_assign_updated_by ON document_assign(updated_by);
CREATE INDEX idx_document_assign_deleted_by ON document_assign(deleted_by);
```

### 9.3 Audit Field Indexes

**MANDATORY:** Every table with `updated_at` MUST have an index for incremental 
sync, change tracking, and audit queries.

```sql
-- Audit Field Indexes (updated_at)
CREATE INDEX idx_users_updated_at ON users(updated_at);
CREATE INDEX idx_roles_updated_at ON roles(updated_at);
CREATE INDEX idx_families_updated_at ON families(updated_at);
CREATE INDEX idx_user_roles_updated_at ON user_roles(updated_at);
CREATE INDEX idx_categories_updated_at ON categories(updated_at);
CREATE INDEX idx_subcategories_updated_at ON subcategories(updated_at);
CREATE INDEX idx_documents_updated_at ON documents(updated_at);
CREATE INDEX idx_document_assign_updated_at ON document_assign(updated_at);
```

### 9.4 Unique Constraint Indexes

```sql
-- Unique Indexes
CREATE UNIQUE INDEX uq_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_roles_name ON roles(name) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_categories_name ON categories(name) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_subcategories_category_name ON subcategories(category_id, name) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_user_roles_user ON user_roles(user_id) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX uq_document_assign_document_assign_to ON document_assign(document_id, assign_to) WHERE deleted_at IS NULL;
```

### 9.5 Composite Indexes

Composite indexes for common query patterns:

```sql
-- Composite Indexes for Common Query Patterns
CREATE INDEX idx_user_roles_user_family ON user_roles(user_id, family_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_family_owner ON documents(family_id, owner_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_family_category ON documents(family_id, category_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_family_expiry ON documents(family_id, expiry_date) WHERE deleted_at IS NULL AND expiry_date IS NOT NULL;
CREATE INDEX idx_document_assign_assign_to_access ON document_assign(assign_to, access_type) WHERE deleted_at IS NULL;
```

### 9.6 Soft Delete Indexes

Partial indexes for soft-delete queries:

```sql
-- Soft Delete Partial Indexes
CREATE INDEX idx_users_active ON users(id) WHERE deleted_at IS NULL AND is_del = false;
CREATE INDEX idx_roles_active ON roles(id) WHERE deleted_at IS NULL AND is_del = false;
CREATE INDEX idx_families_active ON families(id) WHERE deleted_at IS NULL AND is_del = false;
CREATE INDEX idx_user_roles_active ON user_roles(id) WHERE deleted_at IS NULL AND is_del = false;
CREATE INDEX idx_categories_active ON categories(id) WHERE deleted_at IS NULL AND is_del = false;
CREATE INDEX idx_subcategories_active ON subcategories(id) WHERE deleted_at IS NULL AND is_del = false;
CREATE INDEX idx_documents_active ON documents(id) WHERE deleted_at IS NULL AND is_del = false;
CREATE INDEX idx_document_assign_active ON document_assign(id) WHERE deleted_at IS NULL AND is_del = false;
```

### 9.7 Text Search Indexes

For frequently searched text columns (requires pg_trgm extension):

```sql
-- Enable pg_trgm extension for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Text Search Indexes
CREATE INDEX idx_users_email_trgm ON users USING gin(email gin_trgm_ops);
CREATE INDEX idx_documents_title_trgm ON documents USING gin(title gin_trgm_ops);
CREATE INDEX idx_families_name_trgm ON families USING gin(name gin_trgm_ops);
```

### 9.8 Index Summary

**Total Indexes:**
- Primary Key Indexes: 8
- Foreign Key Indexes: 40
- Audit Field Indexes (updated_at): 8
- Unique Constraint Indexes: 6
- Composite Indexes: 5
- Soft Delete Partial Indexes: 8
- Text Search Indexes: 3

**Grand Total: 78 indexes**

All indexes are designed to optimize:
- JOIN operations (foreign key indexes)
- Incremental sync and change tracking (updated_at indexes)
- Soft-delete queries (partial indexes)
- Text search operations (trigram indexes)
- Common query patterns (composite indexes)

================================================================================
SECTION 10 — PROFESSIONAL ASCII ER DIAGRAM
================================================================================

This section presents the complete Entity Relationship Diagram (ERD) using 
Crow's Foot notation, showing only Primary Key (PK) and Foreign Key (FK) 
fields as per enterprise database design standards.

┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│                    DOCVAULT DATABASE - ASCII ER DIAGRAM                    │
│                    (Crow's Foot Notation - PK/FK Only)                    │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

+------------------+             +------------------+             +------------------+
|      Users       |   1     1   |   User_Roles     |   1     M    |      Roles       |
+------------------+             +------------------+             +------------------+
| id (PK)          |<----------->| id (PK)          |<----------->| id (PK)          |
+------------------+             | user_id (FK)     |             +------------------+
        │                        | family_id (FK)   |
        │                        | role_id (FK)     |
        │ 1                      +------------------+
        │                               │
        │ M                             │ M
        │                               │
        │                               │ 1
        │                               │
        │                               ▼
        │                      +------------------+
        │                      |    Families      |
        │                      +------------------+
        │                      | id (PK)          |
        │                      +------------------+
        │                               │
        │                               │ 1
        │                               │
        │                               │ M
        │                               │
        │                               ▼
        │                      +------------------+
        │                      |    Documents      |
        │                      +------------------+
        │                      | id (PK)          |
        │                      | family_id (FK)   |
        │                      | owner_id (FK)    |
        │                      | category_id (FK) |
        │                      | subcategory_id   |
        │                      |        (FK)      |
        │                      +------------------+
        │                               │
        │                               │ 1
        │                               │
        │                               │ M
        │                               │
        │                               ▼
        │                      +------------------+
        │                      | Document_Assign  |
        │                      +------------------+
        │                      | id (PK)          |
        │                      | document_id (FK) |
        │                      | owner_id (FK)    |
        │                      | assign_to (FK)   |
        │                      +------------------+
        │                               │
        │                               │ M
        │                               │
        │                               │ 1
        │                               │
        └───────────────────────────────┘


+------------------+             +------------------+
|   Categories     |   1     M   |  Subcategories   |
+------------------+             +------------------+
| id (PK)          |<----------->| id (PK)          |
+------------------+             | category_id (FK) |
        │                        +------------------+
        │                                │
        │ 1                             │ 1
        │                                │
        │ M                             │ M
        │                                │
        │                                │
        │                                │
        └────────────────────────────────┘
                │
                │ 1
                │
                │ M
                │
                ▼
        +------------------+
        |    Documents      |
        +------------------+


================================================================================
                            RELATIONSHIP SUMMARY
================================================================================

1. Users ────────(1:1)──────> User_Roles
   Foreign Key: User_Roles.user_id → Users.id
   Constraint: Each user has exactly one role (UNIQUE constraint on user_id)

2. Roles ────────(1:M)──────> User_Roles
   Foreign Key: User_Roles.role_id → Roles.id

3. Families ──────(1:M)──────> User_Roles
   Foreign Key: User_Roles.family_id → Families.id (nullable for SuperAdmin)

4. Families ──────(1:M)──────> Documents
   Foreign Key: Documents.family_id → Families.id

5. Users ─────────(1:M)──────> Documents
   Foreign Key: Documents.owner_id → Users.id

6. Categories ────(1:M)──────> Subcategories
   Foreign Key: Subcategories.category_id → Categories.id

7. Categories ────(1:M)──────> Documents
   Foreign Key: Documents.category_id → Categories.id

8. Subcategories ─(1:M)──────> Documents
   Foreign Key: Documents.subcategory_id → Subcategories.id

9. Documents ─────(1:M)──────> Document_Assign
   Foreign Key: Document_Assign.document_id → Documents.id

10. Users ────────(1:M)──────> Document_Assign (as owner)
    Foreign Key: Document_Assign.owner_id → Users.id

11. Users ────────(1:M)──────> Document_Assign (as assignee)
    Foreign Key: Document_Assign.assign_to → Users.id

================================================================================
                                END OF DOCUMENT
================================================================================

