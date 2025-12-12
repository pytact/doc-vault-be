3. Data Requirements Per Screen (Continued)
Family Management + Family Soft Delete
─────────────────────────────────────────
SCR_FAMILY_LIST

Route: /families
Source: F01D, F01H

3.2 Reads (Server Data Required)

The UI displays all Families visible to the SuperAdmin.

Reads:
- Family:
    fields: [
        id,
        name,
        status,         # Active / SoftDeleted
        is_del,         # backend canonical deletion marker
        created_at,
        updated_at
    ]

Derived Fields
Derived:
- status_label: (Active / SoftDeleted)
- can_create_family = Boolean (true only for SuperAdmin)

Filtering / Sorting / Pagination
Filters:
- status  # optional if listing includes soft-deleted

Pagination:
- page
- page_size

Sorting:
- sort_by (name, created_at, status)
- sort_order (asc/desc)

3.3 Writes (Actions)
Writes:
- create_family    # via MODAL_CREATE_FAMILY
- navigate_to_family_detail(family_id)


No delete from list; delete occurs in SCR_FAMILY_DETAIL.

3.4 Query Parameters
- status
- page
- page_size
- sort_by
- sort_order

3.5 Derived Fields
- status_label
- can_create_family

3.6 UI Data Constraints

Must filter SoftDeleted families depending on global UX policy.

Must support server-side pagination for large orgs.

Must not expose Family-level secret metadata.

Must enforce "only SuperAdmin can create family" in server responses, not only UI.

─────────────────────────────────────────
SCR_FAMILY_DETAIL

Route: /families/:family_id
Source: F01D, F01H

3.2 Reads (Server Data Required)
Reads:
- Family:
    fields: [
        id,
        name,
        status,              # Active / SoftDeleted
        is_del,
        created_at,
        created_by,
        updated_at,
        updated_by
    ]

Derived Fields
Derived:
- can_edit_family = (currentUser.role = SuperAdmin AND family.status = Active)
- can_soft_delete_family = same as above
- show_locked_state = (family.status = SoftDeleted)

3.3 Writes (Actions)
Writes:
- update_family_name(family_id)           # via MODAL_EDIT_FAMILY_NAME
- soft_delete_family(family_id)           # via MODAL_SOFT_DELETE_FAMILY


No restore operation exists.

3.4 Query Parameters

None.

3.5 Derived Fields
- can_edit_family
- can_soft_delete_family
- show_locked_state

3.6 UI Data Constraints

If the family is SoftDeleted, redirect to SCR_FAMILY_NOT_ACCESSIBLE.

Family delete cascades to users & documents (domain rule). UI must not contradict this.

Modals must be disabled for non-SuperAdmins.

─────────────────────────────────────────
SCR_FAMILY_NOT_ACCESSIBLE

Route: /families/:family_id/not-accessible
Source: F01D, F01H

3.2 Reads

Minimum required:

Reads:
- Family:
    fields: [
        id,
        status            # SoftDeleted expected
    ]

3.3 Writes

None.

3.4 Query Parameters

None.

3.5 Derived Fields
Derived:
- locked_message

3.6 UI Data Constraints

User must not see family details if soft-deleted.

All navigations to subroutes /families/:id/* must redirect here.

─────────────────────────────────────────
MODAL_CREATE_FAMILY

Purpose: Create a new Family
Source: F01D

3.2 Reads
Reads:
- None (SuperAdmin-only, no contextual data needed)

3.3 Writes
Writes:
- create_family:
    input_fields: [
        name
    ]
    effects:
        - Create Family with status = Active
        - Set created_at, created_by

3.4 Query Parameters

None.

3.5 Derived Fields

None.

3.6 UI Data Constraints

Only SuperAdmin may create a family.

Name uniqueness policy (if enforced) must be validated server-side.

─────────────────────────────────────────
MODAL_EDIT_FAMILY_NAME

Purpose: Update Family name
Source: F01D

3.2 Reads
Reads:
- Family:
    fields: [
        id,
        name,
        status
    ]


Derived:

Derived:
- can_edit = (family.status = Active)

3.3 Writes
Writes:
- update_family_name:
    input_fields: [
        name
    ]
    effects:
        - Update Family.name
        - Update updated_at / updated_by

3.4 Query Parameters

None.

3.5 Derived Fields
- can_edit

3.6 UI Data Constraints

Cannot edit if family.status = SoftDeleted.

Name validation errors must be supported.

─────────────────────────────────────────
MODAL_DELETE_FAMILY

Purpose: Pre-soft-delete confirmation (but actual soft-delete handled by MODAL_SOFT_DELETE_FAMILY)
Source: F01D

3.2 Reads

Displays simple family identity:

Reads:
- Family:
    fields: [
        id,
        name,
        status
    ]

3.3 Writes

None — this modal is just a confirmation step.
Actual deletion is handled in MODAL_SOFT_DELETE_FAMILY.

3.4 Query Parameters

None.

3.5 Derived Fields
- warning_text

3.6 UI Data Constraints

Cannot proceed if Family is already SoftDeleted.

Must instruct that deletion is irreversible & cascades.

─────────────────────────────────────────
MODAL_SOFT_DELETE_FAMILY

Purpose: Execute Family soft-delete cascade
Source: F01H

3.2 Reads
Reads:
- Family:
    fields: [
        id,
        name,
        status,
        is_del
    ]


Derived:

Derived:
- cascade_preview_message

3.3 Writes
Writes:
- soft_delete_family(family_id):
    effects:
        - set family.status = SoftDeleted
        - set family.is_del = true
        - soft-delete ALL Users in the family
        - remove all User_Role mappings
        - soft-delete all documents
        - invalidate all pending invitations

3.4 Query Parameters

None.

3.5 Derived Fields
- cascade_preview_message

3.6 UI Data Constraints

Must confirm destructive action.

Operation only allowed for SuperAdmin.

After deletion, redirect to SCR_FAMILY_LIST.

Must disable delete if already SoftDeleted.