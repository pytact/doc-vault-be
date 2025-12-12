# Domain Model: Core Identity, Access & Organization (F-001)

## 1. Domain Glossary
| Term | Definition | Examples |
|------|------------|----------|
| Family | Tenant-level organizational unit that isolates users, documents, and permissions. | “The Smith Family Vault” |
| User | An individual identity belonging to exactly one Family. Created via invitation. | PendingActivation → Active → SoftDeleted |
| Role | A predefined permission grouping applied to users. | superadmin, familyadmin, member, viewer, editor |
| User_Role | Mapping entity linking a User to a Role within a Family. | user_id=22, family_id=6, role=familyadmin |
| Invitation State | Fields on the User representing invite token, expiry, activation status. | invite_token, invite_expire_at |
| Soft Delete | Logical removal of entity from active visibility; cannot be restored. | user.is_del = true |
| Permission | JSON permission object associated to a Role. | `{ "family:manage_all": true }` |

---

## 2. Entities and Relationships

### 2.1 Entity List
| Entity | Description |
|--------|-------------|
| Family | Represents a tenant. Owns users, documents, and permission scope. |
| User | Identity with authentication, invitation lifecycle, and single-family membership. |
| Role | Predefined permission profile controlling capabilities. |
| User_Role | One-to-one mapping defining the single role a user holds within a family. |

---

### 2.2 Entity Details

---

### **Family**
- **Description**: Tenant entity providing isolation for users and their documents.
- **Key Fields (business-level)**:

  | Field | Description | Notes |
  |--------|-------------|--------|
  | id | Unique family identifier | |
  | name | Human-readable tenant name | Required |
  | status | Active / SoftDeleted | Soft delete enforced |
  | is_del | Indicates soft-deleted state | |
  | created_at / created_by | Audit fields | |
  | updated_at / updated_by | Audit fields | |

- **Relationships**:
  - One Family has many Users.
  - One Family has many User_Roles entries.
  - Family soft delete cascades: users and documents become soft-deleted.

---

### **User**
- **Description**: A single identity within one Family, created initially in PendingActivation state through invitation.
- **Key Fields (business-level)**:

  | Field | Description | Notes |
  |--------|-------------|--------|
  | id | Unique identifier | |
  | email | Immutable login identity | Unique system-wide |
  | name | Profile name | Editable |
  | family_id | Family membership | Required |
  | hash_password | Password hash | Null until activation |
  | status | PendingActivation / Active / SoftDeleted | |
  | invite_token | Token for account activation | Resets when re-sent |
  | invite_sent_at | When the invite was last sent | |
  | invite_expire_at | Set to 24h after send | Resets on resend |
  | invited_by | ID of user (SuperAdmin or FamilyAdmin) who created the invite | |
  | activated_at | Timestamp when user completed activation | |
  | is_del | Soft-delete marker | |
  | created_at / created_by | Audit metadata | |
  | updated_at / updated_by | Audit metadata | |

- **Relationships**:
  - Belongs to exactly one Family.
  - Has exactly one Role through User_Role.
  - Soft delete triggers deletion of all user-owned documents (domain rule link to document feature).

---

### **Role**
- **Description**: Predefined permission object for controlling capabilities across the system.
- **Key Fields (business-level)**:

  | Field | Description | Notes |
  |--------|-------------|--------|
  | id | Unique identifier | UUID |
  | name | Role name | superadmin, familyadmin, member, viewer, editor |
  | permissions | JSON permission blob | Imported from permission system |

- **Relationships**:
  - One Role is assigned to many Users (via User_Roles).

---

### **User_Role**
- **Description**: One-to-one mapping of User to Role within a Family. Each user has exactly one role.
- **Key Fields (business-level)**:

  | Field | Description | Notes |
  |--------|-------------|--------|
  | id | Unique identifier | |
  | user_id | User receiving the role | Unique per user (one role per user) |
  | family_id | Family scope for the role | Ensures role isolation, nullable for SuperAdmin |
  | role_id | Assigned role | |

- **Relationships**:
  - Many-to-one to Family.
  - One-to-one to User (each user has exactly one role).
  - Many-to-one to Role.

---

### 2.3 Relationship Overview (Text Diagram)
```text
Family 1..* User
User 1..1 Role (via User_Role)
Family 1..* User_Role
Role 1..* User_Role
