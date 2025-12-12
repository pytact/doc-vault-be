3. Data Requirements Per Screen

This section defines Reads, Writes, Query Parameters, Derived Fields, and UI Data Constraints for each screen, strictly based on UF1, domain model, and feature brief.

─────────────────────────────────────────
SCR_USER_LIST

Route: /family/users
Source: F01A, F01F, F01G

3.2 Reads (Server Data Required)
User (domain entity)

The UI requires a list of users within the currently selected Family.

Reads:
- User:
    fields: [
        id,
        name,
        email,
        status,               # Active / PendingActivation / SoftDeleted
        invite_sent_at,       # Visible only if PendingActivation
        invite_expire_at,     # Derived UI need for countdown or status labeling
        activated_at,
        is_del,               # Soft-delete indicator
        created_at,
        updated_at
    ]
- User_Role:
    fields: [
        role_id,
        user_id
    ]
- Role:
    fields: [
        id,
        name                  # familyadmin, member, viewer, etc.
    ]
- Family:
    fields: [
        id,
        status                # Needed to disable user operations if family is SoftDeleted
    ]

Derived fields
Derived:
- roles_summary: Array<string> 
    Description: list of role.name for each user (flattened)
- activation_state_label:
    Derived from user.status + invite_expire_at
- is_activation_expired:
    Boolean: NOW > invite_expire_at (for PendingActivation only)

Filters / Pagination / Sorting
Filters:
- status (Active, PendingActivation, SoftDeleted)

Pagination:
- page
- page_size

Sorting:
- sort_by (name, email, status, created_at)
- sort_order (asc / desc)

3.3 Writes (Actions)
Writes Required by UI
Writes:
- create_invitation (via MODAL_INVITE_USER)
- soft_delete_user(user_id)
- navigate_to_user_detail(user_id)   # not an API op; UI action only


No role editing from this screen (that occurs in SCR_USER_DETAIL).

3.4 Query Parameters
Query Parameters:
- status
- sort_by
- sort_order
- page
- page_size

3.5 Derived or Aggregated Fields
- roles_summary
- activation_state_label
- is_activation_expired

3.6 UI Data Constraints

Must support server-side pagination for large families.

Must not request all users without filters for SoftDeleted lists—server must filter.

Must receive role assignments merged per user via aggregated role list.

Must gracefully handle when Family is SoftDeleted → all actions disabled.

─────────────────────────────────────────
SCR_USER_DETAIL

Route: /family/users/:user_id
Source: F01F, F01G

3.2 Reads
User
Reads:
- User:
    fields: [
        id,
        name,
        email,
        family_id,
        status,
        activated_at,
        invite_sent_at,
        invite_expire_at,
        is_del,
        created_at,
        updated_at
    ]

User_Role + Role
- User_Role:
    fields: [
        id,
        user_id,
        family_id,
        role_id
    ]

- Role:
    fields: [
        id,
        name,
        permissions   # May not be displayed but needed for some UI hints
    ]

Derived fields
Derived:
- roles_list: Array<{ id, name }>
- allowed_role_management: Boolean 
    (true if current user is SuperAdmin or FamilyAdmin AND target user not SoftDeleted)

Family
- Family:
    fields: [
        id,
        status             # Must disable actions if Family is SoftDeleted
    ]

3.3 Writes
Writes:
- update_user_roles(user_id)          # via MODAL_MANAGE_USER_ROLES
- soft_delete_user(user_id)           # via MODAL_SOFT_DELETE_USER


No email update, no password reset here.

3.4 Query Parameters

None.

3.5 Derived Fields
- roles_list
- allowed_role_management

3.6 UI Data Constraints

If user is SoftDeleted, all actions disabled.

If family is SoftDeleted, redirect to SCR_FAMILY_NOT_ACCESSIBLE.

Role list returned must include all assignable roles for the family.

─────────────────────────────────────────
MODAL_INVITE_USER

Purpose: Create PendingActivation user and send invitation
Source: F01A

3.2 Reads

Minimal pre-load required:

Reads:
- Family:
    fields: [ id, status ]  # Must ensure family is not soft-deleted

3.3 Writes
Writes:
- create_user_invitation:
    input_fields: [
        email
    ]
    effects:
        - Create User (status = PendingActivation)
        - Generate invite_token
        - Set invite_expire_at = now + 24h

3.4 Query Parameters

None.

3.5 Derived Fields
- invite_expiration_timestamp = now + 24h (returned by backend)

3.6 UI Data Constraints

Email uniqueness must be validated server-side.

Errors must be returned without exposing sensitive user information.

Must not allow invitation if Family is SoftDeleted.

─────────────────────────────────────────
MODAL_MANAGE_USER_ROLES

Purpose: Add/remove roles for a user
Source: F01F

3.2 Reads
Reads:
- User:
    fields: [ id, name, status, family_id ]

- Role:
    fields: [
        id,
        name,
        permissions
    ]

- User_Role:
    fields: [
        id,
        user_id,
        role_id
    ]

Derived:
Derived:
- available_roles: Array<Role>
- selected_roles: Array<Role.id>  # Pre-selected based on User_Role mappings
- can_edit_roles: Boolean

3.3 Writes
Writes:
- update_user_roles(user_id):
    input_fields: [
        selected_role_ids[]
    ]
    effects:
        - Replace User_Role mappings for user

3.4 Query Parameters

None.

3.5 Derived Fields
- available_roles
- selected_roles
- can_edit_roles

3.6 UI Data Constraints

Must not allow modification if user is SoftDeleted.

Must enforce Family isolation (roles belong to family context).

server must ensure user remains Active or PendingActivation; SoftDeleted cannot be updated.

─────────────────────────────────────────
MODAL_SOFT_DELETE_USER

Purpose: Confirm and execute soft delete
Source: F01G

3.2 Reads
Reads:
- User:
    fields: [
        id,
        name,
        email,
        status
    ]
- Family:
    fields: [
        id,
        status
    ]

3.3 Writes
Writes:
- soft_delete_user(user_id):
    effects:
        - set user.status = SoftDeleted
        - set user.is_del = true
        - cascade soft-delete to all user-owned documents
        - delete all User_Role mappings
        - invalidate invite tokens if PendingActivation

3.4 Query Parameters

None.

3.5 Derived Fields
- delete_warning_message: String    # UI uses a generic message

3.6 UI Data Constraints

User must not already be SoftDeleted.

After deletion, redirection must return to SCR_USER_LIST.

Must disable delete operation if Family is SoftDeleted.