4. Proposed API Hints (Not Final API Spec)

These are logical endpoints inferred from UI data needs.
They are NOT API definitions and include no schemas, status codes, or transport details.

4.1 User Listing & Detail
GET   /api/v1/families/{family_id}/users
GET   /api/v1/families/{family_id}/users/{user_id}
PATCH /api/v1/families/{family_id}/users/{user_id}/roles
PATCH /api/v1/families/{family_id}/users/{user_id}/soft-delete

4.2 User Invitation & Activation
POST  /api/v1/families/{family_id}/users/invite
GET   /api/v1/invitations/validate?token={token}
POST  /api/v1/invitations/activate

4.3 Authentication & Session
POST  /api/v1/auth/login
POST  /api/v1/auth/logout

4.4 Account Setup & Password Management
POST  /api/v1/users/{user_id}/password/change
POST  /api/v1/invitations/activate

4.5 Family Management & Soft-Delete
GET    /api/v1/families
POST   /api/v1/families
GET    /api/v1/families/{family_id}
PATCH  /api/v1/families/{family_id}
PATCH  /api/v1/families/{family_id}/soft-delete

4.6 Profile Settings
PATCH /api/v1/users/{user_id}/profile

4.7 Role Listing (for Manage Roles Modal)
GET /api/v1/families/{family_id}/roles

5. Cross-Screen Data Dependencies

The following structures recur across multiple screens and modals.
This helps API designers avoid duplication and ensure consistent data shapes.

5.1 The User Summary Model

Used by:

SCR_USER_LIST

SCR_USER_DETAIL

All role-management screens

Soft-delete flows

Invitation validation flows

UserSummary:
- id
- name
- email
- status
- invite_sent_at
- invite_expire_at
- activated_at
- is_del

5.2 Role Information

Used by:

SCR_USER_DETAIL

MODAL_MANAGE_USER_ROLES

SCR_USER_LIST (role summary)

RoleInfo:
- id
- name
- permissions (not always displayed, but required for completeness)

5.3 Family Header

Used by:

SCR_FAMILY_LIST

SCR_FAMILY_DETAIL

SCR_FAMILY_NOT_ACCESSIBLE

All soft-delete checks

All user-related flows (to ensure family active)

FamilyHeader:
- id
- name
- status
- is_del

5.4 Password Rules

Used by:

SCR_ACCOUNT_SETUP

MODAL_CHANGE_PASSWORD

PasswordRules:
- min_length = 12
- uppercase: true
- lowercase: true
- number: true
- special: true
- disallow_last_5: true

5.5 Invite Validation Payload

Used by:

SCR_INVITE_ACTIVATION_VALIDATE

SCR_ACCOUNT_SETUP

SCR_INVITE_EXPIRED

InviteValidation:
- user_id
- invite_token
- invite_expire_at
- status
- family_status

5.6 Soft-Delete Cascades (User / Family)

Several screens need to know about soft-delete relationships:

SCR_USER_DETAIL

SCR_USER_LIST

SCR_FAMILY_DETAIL

SCR_FAMILY_NOT_ACCESSIBLE

Authentication attempts

Invite validation

SoftDeleteMetadata:
- user.is_del
- family.is_del

6. Data Edge Cases

Below are all UI-relevant edge cases that must be supported by the backend outputs to prevent inconsistent UI behavior.

6.1 Invitation + Activation Edge Cases
Token Expired

invite_expire_at < NOW

Must redirect to SCR_INVITE_EXPIRED

Token Invalid

No User with given token

Same treatment as expired (no distinction)

User SoftDeleted before activation

Must behave as expired

Family SoftDeleted before activation

Treat invitation as invalid

Redirect to SCR_INVITE_EXPIRED

6.2 Authentication Edge Cases

Invalid credentials

PendingActivation user attempts login

SoftDeleted user attempts login

Family SoftDeleted → all users must be blocked

Logged-in user accessing /auth/login → redirect to dashboard

6.3 User Soft-Delete Edge Cases

User already SoftDeleted → modal cannot open

Concurrent soft-delete requests → second must fail gracefully

PendingActivation user soft-deleted → token invalidated

6.4 Family Soft-Delete Edge Cases

Accessing deleted family’s detail → SCR_FAMILY_NOT_ACCESSIBLE

Accessing any child route → redirect to SCR_FAMILY_NOT_ACCESSIBLE

Concurrent delete attempts → second fails gracefully

After deletion, all user operations invalid

6.5 Manage Roles Edge Cases

Cannot edit roles for SoftDeleted user

Cannot edit roles when family SoftDeleted

Unauthorized user attempts → reject

Remove all roles is allowed

6.6 Profile Management Edge Cases

Incorrect current password

Password does not meet strong rules

Password reuse violation

User SoftDeleted mid-session → operation must fail, trigger logout

6.7 Account Setup Edge Cases

Token expires between load and submit

Family SoftDeleted during setup

User SoftDeleted during setup

Name missing or invalid

Password violating any rule

6.8 List Pagination / Filtering Edge Cases

Page out of range returns empty

SoftDeleted entries might be hidden depending on global UX

Sorting must be stable and deterministic

6.9 Data Consistency / Concurrent Updates

Backend must ensure:

Updating family while soft-delete is in progress fails cleanly

Editing user roles during user deletion fails

Renaming family during family deletion fails

Editing name/password after user SoftDeleted results in forced logout