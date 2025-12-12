Feature Brief: F-001 — Core Identity, Access & Organization
1. Context & Problem

Background:
DocValut operates as a multi-tenant family document vault, requiring secure authentication, role-based access control, family management, and user lifecycle handling. F-001 forms the foundational identity and access layer on which all other features rely.

Current Pain / Problem:
Without a structured identity and access system, users cannot securely onboard, authenticate, or operate within isolated family environments. No mechanism currently exists for controlled role assignment, strong password rules, or soft-delete lifecycle workflows.

Why Now:
All downstream features—documents, sharing, notifications, UI—depend on a stable and clearly defined identity and access foundation. F-001 must be implemented first to ensure tenant isolation, security, and consistent role-driven behavior.

2. Goal / Outcome

Primary Goal:
Provide a secure, RBAC-driven identity system with onboarding, authentication, user management, and family management.

Secondary Goals:

Enforce strong password policies

Maintain strict tenant isolation at the family level

Support multi-role permission merging

Implement robust soft-delete workflows for families and users

Success Criteria (Business View):

New users can onboard through invite flows without admin intervention

Users only see and operate within their assigned family

Role assignments reliably control capabilities across the system

3. In Scope

Invitation workflow with 24-hour expiry

Account setup and authentication (login/logout)

Strong password policy enforcement

User management (update name, update password, soft delete)

Family management (create, update, soft delete)

Role assignment and multi-role permission merging

Single-family membership rule

Soft-delete propagation rules (users & documents when family/user is deleted)

4. Out of Scope

MFA or advanced authentication methods

Account recovery outside password reset

Family restoration flows

Document operations (covered in F-003)

UI design/flows (covered in F-006)

5. Primary Actors
Actor	Description
SuperAdmin	Creates families, manages all users globally, assigns roles, performs soft deletes
FamilyAdmin	Manages users within their family, updates name/roles, and performs user soft deletion
Member	Standard user with ability to manage own documents (permissions handled in other features)
Viewer	Limited user with read access to assigned documents (identity handled here)
Editor	Limited user with read/write access to assigned documents (identity handled here)
6. User Stories

As a SuperAdmin, I want to create families so that new organizational units can be onboarded.

As a FamilyAdmin, I want to invite new users so that they can join my family.

As a User, I want to set up my account through an invite so that I can securely access the system.

As a User, I want to update my profile name and password so that my account remains accurate and secure.

As a FamilyAdmin, I want to assign multiple roles to a user so that permissions reflect their responsibilities.

As a SuperAdmin, I want to soft delete a family so all users and documents are deactivated.

7. Constraints & Assumptions
Constraints

Invite expires in 24 hours

Strong password policy: 12+ chars, upper/lower/number/special, cannot reuse last 5 passwords

No session timeout

No login-attempt lockout

Users can hold multiple roles with merged permissions

Soft-deleting a user permanently removes access and soft-deletes all their documents

Soft-deleting a family soft-deletes all users and documents permanently

Assumptions

Email is immutable after account creation

Password resets follow the same security policy as initial setup

Soft-deleted entities cannot be restored

SuperAdmin is the only actor who can create new families

8. Dependencies

SMTP email service for invite and password reset

Role permission JSON definitions (from role_permissions system)

Global soft-delete mechanism shared across features

Tenant isolation enforcement used by all other features

9. Open Questions

Should the system notify FamilyAdmins when a user they invited has not activated within the invite window?

Should audit logging be included for account and role changes?

Should SuperAdmin receive alerts when families approach user limits (if limits will be defined later)?

10. Acceptance Criteria

 Users receive invite with a 24-hour expiring token

 Users can complete account setup with strong password requirements enforced

 Login/logout and password reset flows function correctly

 Users can update name and password but not email

 FamilyAdmin can update roles for users in their family

 SuperAdmin can create families; FamilyAdmin cannot

 Soft-deleting a user soft-deletes all their documents and blocks login

 Soft-deleting a family soft-deletes all users and documents

 Role merging logic correctly aggregates permissions across assigned roles