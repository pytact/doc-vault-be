# DocFamily API Reference

This document contains the complete list of APIs with access permissions.

**Total Endpoints: 33**

---

## 4.1 Authentication APIs (10)

| Method | Endpoint                          | Access                         | Purpose                                  |
|--------|-----------------------------------|--------------------------------|------------------------------------------|
| POST   | `/v1/auth/send-invite`            | SuperAdmin, FamilyAdmin        | Send email invitation to new user        |
| GET    | `/v1/auth/verify-invite/{token}`  | Invited users                  | Validate invitation token                |
| POST   | `/v1/auth/setup-account`          | Invited users                  | Complete account setup using invite token|
| POST   | `/v1/auth/forgot-password`        | All users                      | Initiate password reset                  |
| GET    | `/v1/auth/verify-reset/{token}`   | Users with valid reset token   | Validate password reset token            |
| POST   | `/v1/auth/reset-password`         | Users with valid reset token   | Reset password using token               |
| POST   | `/v1/auth/resend-invite`          | Original inviter, SuperAdmin   | Resend invitation email                  |
| POST   | `/v1/auth/login`                  | All activated users            | User login                               |
| POST   | `/v1/auth/logout`                 | Authenticated users            | User logout                              |
| GET    | `/v1/auth/me`                     | Authenticated users            | Get current user profile                 |

---

## 4.2 User Management APIs (6)

| Method | Endpoint                              | Access                                              | Purpose                  |
|--------|---------------------------------------|-----------------------------------------------------|--------------------------|
| GET    | `/v1/users`                           | SuperAdmin                                          | List all users           |
| GET    | `/v1/users/{user_id}`                 | SuperAdmin, FamilyAdmin (own family)                | Get user profile         |
| PUT    | `/v1/users/{user_id}`                 | SuperAdmin, FamilyAdmin (own family), Self (name)   | Update user profile      |
| DELETE | `/v1/users/{user_id}`                 | SuperAdmin, FamilyAdmin (own family)                | Soft delete user         |
| POST   | `/v1/users/{user_id}/assign-role`     | SuperAdmin, FamilyAdmin (own family)                | Assign/reassign role     |
| POST   | `/v1/users/{user_id}/reassign-family` | SuperAdmin only                                     | Move user to new family  |

---

## 4.3 Family Management APIs (7)

| Method | Endpoint                                              | Access                               | Purpose                    |
|--------|-------------------------------------------------------|--------------------------------------|----------------------------|
| POST   | `/v1/families`                                        | SuperAdmin                           | Create family              |
| GET    | `/v1/families`                                        | SuperAdmin                           | List all families          |
| GET    | `/v1/families/{family_id}`                            | SuperAdmin, FamilyAdmin (own family) | Get family details         |
| PUT    | `/v1/families/{family_id}`                            | SuperAdmin                           | Update family              |
| DELETE | `/v1/families/{family_id}`                            | SuperAdmin only                      | Soft delete family         |
| GET    | `/v1/families/{family_id}/users`                      | SuperAdmin, FamilyAdmin (own family) | List family members        |

---

## 4.4 Document Management APIs (7)

| Method | Endpoint                                                          | Access                               | Purpose                    |
|--------|-------------------------------------------------------------------|--------------------------------------|----------------------------|
| POST   | `/v1/families/{family_id}/users/{user_id}/documents`              | Member (own), FamilyAdmin            | Create document            |
| PATCH  | `/v1/families/{family_id}/users/{user_id}/documents/{document_id}`| Document owner, FamilyAdmin          | Update document metadata   |
| DELETE | `/v1/families/{family_id}/users/{user_id}/documents/{document_id}`| Document owner, FamilyAdmin          | Delete document            |
| GET    | `/v1/families/{family_id}/documents`                              | FamilyAdmin                          | List family documents      |
| GET    | `/v1/documents/{doc_id}`                                          | Owner, Assigned users, FamilyAdmin   | Get single document        |
| PUT    | `/v1/documents/{doc_id}`                                          | Owner, Assigned editor, FamilyAdmin  | Edit document content      |
| DELETE | `/v1/documents/{doc_id}`                                          | Document owner, FamilyAdmin          | Delete document            |

---

## 4.5 Document Sharing APIs (3)

| Method | Endpoint                                | Access                                           | Purpose                      |
|--------|-----------------------------------------|--------------------------------------------------|------------------------------|
| POST   | `/v1/documents/{doc_id}/assign`         | Document owner, FamilyAdmin                      | Assign viewer/editor to doc  |
| DELETE | `/v1/documents/{doc_id}/assign/{user_id}`| Document owner, FamilyAdmin                      | Remove user assignment      |
| GET    | `/v1/documents/{doc_id}/assigned-users` | Owner, Editor (limited), Viewer (read), FamilyAdmin | List assigned users       |

---

## Summary

| Category                  | Count |
|---------------------------|-------|
| Authentication APIs       |    10 |
| User Management APIs      |     6 |
| Family Management APIs    |     7 |
| Document Management APIs  |     7 |
| Document Sharing APIs     |     3 |
| **Total**                 |**33** |
