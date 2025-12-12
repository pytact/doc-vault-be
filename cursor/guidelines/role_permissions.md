# DocFamily Role Permissions

This document contains the complete permission JSON for each role.

**Total Roles: 5**

---

## 1. SuperAdmin

Global system administrator with full control over families and users, but no document access by default.

```json
{
  "family:manage_all": true,
  "family:create": true,
  "family:update": true,
  "family:delete": true,
  "family:view_all": true,

  "user:manage_all": true,
  "user:create": true,
  "user:update": true,
  "user:delete": true,
  "user:view_all": true,

  "user:assign_roles": true,
  "user:reassign_roles": true,
  
  "user:assign_family": true,
  "user:reassign_family": true,

  "document:access": false
}
```

---

## 2. FamilyAdmin

Full control over all users and documents within their own family.

```json
{
  "family:view": true,
  "family:update": true,

  "user:manage_family": true,
  "user:create": true,
  "user:update": true,
  "user:delete": true,
  "user:view_family": true,
  "user:assign_roles": true,
  "user:reassign_roles": true,
  "user:add_familyadmin": true,
  "user:add_member": true,
  "user:add_editor": true,
  "user:add_viewer": true,

  "document:create": true,
  "document:view_all": true,
  "document:edit_all": true,
  "document:delete_all": true,
  "document:assign_viewer": true,
  "document:assign_editor": true
}
```

---

## 3. Member

Can create and manage their own documents, and assign viewer/editor access to others.

```json
{
  "document:create": true,
  "document:view_own": true,
  "document:edit_own": true,
  "document:delete_own": true,
  "document:assign_viewer": true,
  "document:assign_editor": true
}
```

---

## 4. Viewer

Can only view documents that are specifically assigned to them.

```json
{
  "document:view_assigned": true
}
```

---

## 5. Editor

Can view and edit documents that are assigned to them, but cannot delete or create.

```json
{
  "document:view_assigned": true,
  "document:edit_assigned": true
}
```

---

## Permission Summary

| Permission              | SuperAdmin | FamilyAdmin | Member | Viewer | Editor |
|-------------------------|------------|-------------|--------|--------|--------|
| family:manage_all       | Yes        | -           | -      | -      | -      |
| family:create           | Yes        | -           | -      | -      | -      |
| family:update           | Yes        | Yes         | -      | -      | -      |
| family:delete           | Yes        | -           | -      | -      | -      |
| family:view_all         | Yes        | -           | -      | -      | -      |
| family:view             | -          | Yes         | -      | -      | -      |
| user:manage_all         | Yes        | -           | -      | -      | -      |
| user:manage_family      | -          | Yes         | -      | -      | -      |
| user:create             | Yes        | Yes         | -      | -      | -      |
| user:update             | Yes        | Yes         | -      | -      | -      |
| user:delete             | Yes        | Yes         | -      | -      | -      |
| user:view_all           | Yes        | -           | -      | -      | -      |
| user:view_family        | -          | Yes         | -      | -      | -      |
| user:assign_roles       | Yes        | Yes         | -      | -      | -      |
| user:reassign_roles     | Yes        | Yes         | -      | -      | -      |
| user:assign_family      | Yes        | -           | -      | -      | -      |
| user:reassign_family    | Yes        | -           | -      | -      | -      |
| user:add_familyadmin    | -          | Yes         | -      | -      | -      |
| user:add_member         | -          | Yes         | -      | -      | -      |
| user:add_editor         | -          | Yes         | -      | -      | -      |
| user:add_viewer         | -          | Yes         | -      | -      | -      |
| document:access         | No         | -           | -      | -      | -      |
| document:create         | -          | Yes         | Yes    | -      | -      |
| document:view_all       | -          | Yes         | -      | -      | -      |
| document:view_own       | -          | -           | Yes    | -      | -      |
| document:view_assigned  | -          | -           | -      | Yes    | Yes    |
| document:edit_all       | -          | Yes         | -      | -      | -      |
| document:edit_own       | -          | -           | Yes    | -      | -      |
| document:edit_assigned  | -          | -           | -      | -      | Yes    |
| document:delete_all     | -          | Yes         | -      | -      | -      |
| document:delete_own     | -          | -           | Yes    | -      | -      |
| document:assign_viewer  | -          | Yes         | Yes    | -      | -      |
| document:assign_editor  | -          | Yes         | Yes    | -      | -      |

---

## Role Hierarchy

```
SuperAdmin (Global)
    │
    └── FamilyAdmin (Family Scope)
            │
            ├── Member (Own Documents)
            │
            ├── Editor (Assigned Documents - Edit)
            │
            └── Viewer (Assigned Documents - View Only)
```

---

## Permission Merging Rules

When a user has multiple roles, permissions are merged using these rules:

| Scenario                    | Result                                      |
|-----------------------------|---------------------------------------------|
| FamilyAdmin + Member        | Full family control + create own documents  |
| Member + Editor             | Own docs + edit assigned docs               |
| Member + Viewer             | Own docs + view assigned docs               |
| Viewer + Editor             | Editor wins (higher privilege)              |
| FamilyAdmin + Viewer/Editor | Redundant (FamilyAdmin has full access)     |
