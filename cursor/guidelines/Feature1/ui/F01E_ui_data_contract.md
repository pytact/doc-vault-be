3. Data Requirements Per Screen (Continued)
Profile Settings + Change Password Modal
─────────────────────────────────────────
SCR_PROFILE_SETTINGS

Route: /settings/profile
Source: F01E

3.2 Reads (Server Data Required)

The authenticated user views and updates their own profile information.

Reads:
- User (current authenticated user):
    fields: [
        id,
        email,          # immutable
        name,
        status,         # must be Active, otherwise logout or error
        created_at,
        updated_at
    ]

Derived Fields
Derived:
- can_edit_profile = (user.status = Active)
- strong_password_rules: {
      min_length: 12,
      uppercase: true,
      lowercase: true,
      number: true,
      special: true,
      disallow_last_5: true
  }


No role data is required; this screen is not for role editing.

3.3 Writes (Actions)
Profile Name Update
Writes:
- update_profile_name:
    input_fields: [
        name
    ]
    effects:
        - updates user.name
        - updates updated_at

Open Password Modal

Not a backend write, just a UI action.

3.4 Query Parameters

None.

3.5 Derived Fields
- can_edit_profile
- strong_password_rules

3.6 UI Data Constraints

Email must be read-only and never sent as mutable.

Name update must be validated server-side.

If user is SoftDeleted mid-session, save attempts must fail and force logout.

Must not expose any password history in UI.

─────────────────────────────────────────
MODAL_CHANGE_PASSWORD

Purpose: Enable user to change password, requiring current password verification
Source: F01E

3.2 Reads (Server Data Required)
Reads:
- User (current authenticated user):
    fields: [
        id,
        status           # must be Active; otherwise operation forbidden
    ]

Derived
Derived:
- password_rules: {
      min_length: 12,
      uppercase: true,
      lowercase: true,
      number: true,
      special: true,
      disallow_last_5: true
  }

3.3 Writes
Writes:
- change_password:
    input_fields: [
        current_password,
        new_password
    ]
    effects:
        - verify current_password
        - enforce strong password rules
        - check last 5-password history
        - update hash_password
        - update updated_at

Error messages returned by backend must include:

Incorrect current password

Weak password rule failures

Password reuse violation

3.4 Query Parameters

None.

3.5 Derived Fields
- password_rules

3.6 UI Data Constraints

Must show rule-by-rule inline feedback.

Must not reveal whether previous passwords matched other accounts.

Must handle SoftDeleted user (if occurs mid-session) → deny and logout.

Passwords must never be logged or returned.