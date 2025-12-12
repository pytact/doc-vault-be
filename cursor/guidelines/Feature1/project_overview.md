# Project Overview: DocValut

## 1. Project Goal & Context

### 1.1 Background
DocValut is a secure, role-based family document vault designed for families, general consumers, and enterprises. Users are organized into families, each functioning as an isolated tenant. The platform provides controlled document storage, classification, sharing, and expiry notifications through an intuitive web interface.

### 1.2 Problem Statement
Families and small organizations lack a unified, secure system for storing essential documents, managing access, organizing information, and ensuring timely reminders for document renewals. DocValut centralizes document management, ensures privacy through RBAC, and provides proactive notifications for critical expiry dates.

### 1.3 High-Level Goals
- Provide a secure vault for storing and managing family documents
- Implement robust role-based access control for permissions
- Enable document sharing with granular viewer/editor options
- Deliver reliable expiry notifications via email and in-app alerts
- Offer a minimal, functional, easy-to-use web UI

### 1.4 Global/Non-Functional Requirements
- Soft-delete system across entities (documents, families, users)
- S3-compatible storage (LocalStack in development)
- Basic SMTP for email notifications
- Metadata-based searching
- Single-family membership per user
- Scalable for families and enterprises

---

## 2. Feature Breakdown

### 2.1 Feature List Summary
| Feature ID | Name | Summary | Priority | Size | Depends On |
|------------|------|---------|----------|------|------------|
| F-001 | Core Identity, Access & Organization | Authentication, onboarding, roles, families, and user management | High | Large | None |
| F-002 | Categories & Subcategories | Fixed taxonomy of 15 categories and 78 subcategories | High | Small | F-001 |
| F-003 | Document Management | Upload, view, edit, delete, search, and list documents | High | Large | F-001, F-002 |
| F-004 | Document Sharing | Assign viewer/editor roles to specific users | High | Medium | F-003 |
| F-005 | Expiry Notification System | Scheduled alerts via email & in-app for document expiry | Medium | Medium | F-003 |
| F-006 | Web UI | Minimal functional interface for all user operations | High | Large | F-001–F-005 |
| F-007 | SuperAdmin Console | Manage families, users, and soft-deleted entities | Medium | Medium | F-001 |

---

### 2.2 Feature Details

#### F-001 — Core Identity, Access & Organization
- **Short Summary**:  
  Consolidates authentication, onboarding, RBAC, user management, and family management.
- **Business Value**:  
  Establishes secure access control and tenant boundaries essential for data protection.
- **Key Capabilities**:
  - Invite acceptance, account setup, login/logout, password reset  
  - Role management (SuperAdmin, FamilyAdmin, Member, Viewer, Editor)  
  - Family creation, update, soft-delete  
  - User listing, updates, soft deletion, family reassignment  
  - Enforce single-family membership rule
- **Actors**:  
  SuperAdmin, FamilyAdmin, Member, Viewer, Editor
- **Dependencies**:  
  None
- **Notes / Risks / Open Questions**:
  - Must ensure strict tenant isolation

---

#### F-002 — Categories & Subcategories
- **Short Summary**:  
  Predefined, fixed taxonomy of document categories and subcategories.
- **Business Value**:  
  Ensures consistent organization and improves searchability.
- **Key Capabilities**:
  - 15 categories  
  - 78 subcategories  
  - Non-editable by administrators
- **Actors**:  
  All authenticated users
- **Dependencies**:  
  F-001
- **Notes / Risks / Open Questions**:
  - None

---

#### F-003 — Document Management
- **Short Summary**:  
  Core document operations including upload, metadata management, and soft deletion.
- **Business Value**:  
  Enables secure storage and management of essential documents.
- **Key Capabilities**:
  - Upload/store files (LocalStack S3 for dev)  
  - Add/edit metadata (title, expiry date, category)  
  - View documents (permissions applied)  
  - Replace file (overwrite; no versioning)  
  - Soft delete and recover  
  - Metadata search (owner, category, expiry, subcategory)  
  - FamilyAdmin full document access
- **Actors**:  
  FamilyAdmin, Member, Viewer, Editor
- **Dependencies**:  
  F-001, F-002
- **Notes / Risks / Open Questions**:
  - File size limits undefined

---

#### F-004 — Document Sharing
- **Short Summary**:  
  Assign viewer or editor permissions to specific users.
- **Business Value**:  
  Supports controlled collaboration within families.
- **Key Capabilities**:
  - Assign viewer/editor roles  
  - Remove access  
  - List assigned users  
  - Permissions to enforce view/edit rights
- **Actors**:  
  FamilyAdmin, Member, Editor, Viewer
- **Dependencies**:  
  F-003
- **Notes / Risks / Open Questions**:
  - Access conflicts must be resolved by RBAC

---

#### F-005 — Expiry Notification System
- **Short Summary**:  
  Scheduled reminders for upcoming document expirations.
- **Business Value**:  
  Helps families avoid missed renewals for important documents.
- **Key Capabilities**:
  - Alerts at 30 days, 7 days, and on expiry date  
  - Email notifications via SMTP  
  - In-app dashboard alerts  
  - Track read/unread state
- **Actors**:  
  All roles except Viewer (read-only)
- **Dependencies**:  
  F-003
- **Notes / Risks / Open Questions**:
  - Scheduler reliability required

---

#### F-006 — Web UI
- **Short Summary**:  
  Minimal but functional web interface for all core flows.
- **Business Value**:  
  Provides usability and accessibility for non-technical users.
- **Key Capabilities**:
  - Onboarding flows (invite acceptance, password setup)  
  - Login/logout  
  - Dashboard with alerts  
  - Document upload, edit, view  
  - Sharing management  
  - Search & filters  
  - FamilyAdmin user and document screens  
  - Profile settings
- **Actors**:  
  SuperAdmin, FamilyAdmin, Member, Editor, Viewer
- **Dependencies**:  
  F-001–F-005
- **Notes / Risks / Open Questions**:
  - Minimal UI scope, not an enterprise dashboard

---

#### F-007 — SuperAdmin Console
- **Short Summary**:  
  Management tools for global oversight of families and users.
- **Business Value**:  
  Supports operational control and troubleshooting.
- **Key Capabilities**:
  - View/create/update families  
  - Manage users (assign roles, reassign families)  
  - Soft-deleted entity monitoring
- **Actors**:  
  SuperAdmin
- **Dependencies**:  
  F-001
- **Notes / Risks / Open Questions**:
  - Advanced analytics not included

---

## 3. Shared Domain Concepts

### 3.1 Shared Entities
| Entity | Description | Used In |
|--------|-------------|---------|
| User | System account belonging to one family | F-001, F-003, F-004, F-006, F-007 |
| Family | Tenant grouping users and documents | F-001, F-003, F-006 |
| Role | Permission set assigned to users | F-001 |
| Document | User-owned resource with metadata and file | F-003, F-004, F-005 |
| Category/Subcategory | Fixed classification taxonomy | F-002, F-003 |
| Notification | Alerts for upcoming expiries | F-005, F-006 |

### 3.2 Cross-Cutting Concerns
- Soft-delete support  
- RBAC permission enforcement  
- SMTP email service  
- LocalStack S3 file storage (dev/test)  
- Scheduled jobs for notifications  
- Tenant isolation by family  
- Global SuperAdmin privileges  

---

## 4. Recommended Implementation Sequence

### 4.1 Sequential Order
1. **F-001 – Core Identity, Access & Organization**  
   Establishes system foundation and RBAC.
2. **F-002 – Categories & Subcategories**  
   Needed before document workflows.
3. **F-003 – Document Management**  
   Critical core functionality.
4. **F-004 – Document Sharing**  
   Builds on document management.
5. **F-005 – Expiry Notification System**  
   Requires documents to exist first.
6. **F-006 – Web UI**  
   Depends on all backend functionality.
7. **F-007 – SuperAdmin Console**  
   Final administrative layer.

### 4.2 Parallelizable Features
- F-002 (Categories) can run parallel to F-001  
- F-005 (Notifications) can partially run parallel once F-003 metadata is ready  
- F-007 (SuperAdmin Console) can begin during F-006  

---

## 5. Cross-Feature Integration Notes
- RBAC must be uniformly enforced across UI and API layers  
- Document sharing logic extends base document permissions  
- Notification scheduler depends on expiry metadata  
- UI must handle soft-deleted records gracefully  
- FamilyAdmin elevated access affects document listing, search, and editing flows  

---

## 6. Open Questions
- Should audit logging be included for document edits and user actions?
- Should there be UI support for recovering soft-deleted documents?
- Any maximum file size or restricted file types?

---

## 7. Assumptions
- Categories and subcategories will never be editable.  
- No MFA is required.  
- No document versioning required.  
- Web UI is minimal, not enterprise-grade.  
- SMTP is sufficient for all email sending needs.

```markdown
