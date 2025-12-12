3. Data Requirements Per Screen (Continued)
─────────────────────────────────────────
SCR_INVITE_ACTIVATION_VALIDATE

Route: /invite/:token
Source: F01A, F01C

3.2 Reads (Server Data Required)

The screen performs an automatic server call to validate an invitation token. No user interaction occurs.

Reads:
- User (queried by invite_token):
    fields: [
        id,
        email,
        family_id,
        status,             # must be PendingActivation
        invite_token,
        invite_expire_at,
        is_del              # in case the user was soft-deleted after issuance
    ]

- Family:
    fields: [
        id,
        status              # required to detect soft-deleted family
    ]

Derived fields
Derived:
- is_token_valid = Boolean
- is_token_expired = NOW > invite_expire_at
- redirect_target:
      SCR_ACCOUNT_SETUP           if valid
      SCR_INVITE_EXPIRED         if expired / invalid / user.soft-deleted / family.soft-deleted

3.3 Writes (Actions)

None — validation-only.

3.4 Query Parameters

None.

3.5 Derived or Aggregated Fields
- is_token_valid
- is_token_expired
- redirect_target

3.6 UI Data Constraints

Must not expose existence of accounts via error messages.

Must treat invalid tokens the same as expired tokens.

Must redirect immediately on success/failure; no lingering on the screen.

Must detect Family soft-deletion and redirect to SCR_INVITE_EXPIRED.

─────────────────────────────────────────
SCR_INVITE_EXPIRED

Route: /invite/:token/expired
Source: F01A, F01C

3.2 Reads

There is no requirement to fetch the user, token, or family from backend for display, but optionally the UI may request basic metadata to customize messaging.

Minimum required:

Reads:
- None


Optional (if backend wants to provide context):

- expired_reason: enum("expired", "invalid", "family_soft_deleted", "user_soft_deleted")

3.3 Writes

None.

3.4 Query Parameters

None.

3.5 Derived Fields

None.

3.6 UI Data Constraints

This is a static informational page.

Must not reveal whether an email exists in the system.

Must allow navigation to SCR_LOGIN.

─────────────────────────────────────────
SCR_ACCOUNT_SETUP

Route: /invite/:token/setup
Source: F01A, F01C

3.2 Reads

This screen is loaded after successful SCR_INVITE_ACTIVATION_VALIDATE, so it requires the following validated data:

Reads:
- User:
    fields: [
        id,
        email,
        family_id,
        status,              # must still be PendingActivation
        invite_token,
        invite_expire_at,
        is_del
    ]

- Family:
    fields: [
        id,
        status               # must not be SoftDeleted
    ]

Derived Fields
Derived:
- token_still_valid = NOW < invite_expire_at
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
- activate_user:
    input_fields: [
        name,
        password,
        invite_token
    ]
    effects:
        - Set user.name
        - Set user.hash_password
        - Set user.status = Active
        - Set activated_at = NOW
        - Clear invite_token / invite_expire_at
        - Authenticate or redirect user

3.4 Query Parameters

None.

3.5 Derived or Aggregated Fields
- token_still_valid
- password_rules

3.6 UI Data Constraints

Must block submission if token expired between load and submit.

Must enforce strong password policy client-side and server-side.

Must show inline validation failures per rule.

Must treat SoftDeleted family or user as expired/invalid → redirect to SCR_INVITE_EXPIRED.

─────────────────────────────────────────
SCR_LOGIN

Route: /auth/login
Source: F01B

3.2 Reads

Minimal:

Reads:
- None


Optional (if server supplies contextual messaging):

- login_context_message

3.3 Writes
Writes:
- authenticate_user:
    input_fields: [
        email,
        password
    ]
    effects:
        - validate credentials
        - ensure user.status = Active
        - ensure family.status = Active
        - start authenticated session


Errors supported:

Invalid credentials

User not activated (PendingActivation)

User soft-deleted

Family soft-deleted

3.4 Query Parameters

None.

3.5 Derived Fields

None.

3.6 UI Data Constraints

Login must not leak whether email exists.

All user states must map to generic error messages except PendingActivation which gets a specific message.

If already authenticated, redirect to family dashboard.

─────────────────────────────────────────
SCR_LOGOUT_REDIRECT

Route: /auth/logout
Source: F01B

3.2 Reads

None.

3.3 Writes
Writes:
- logout_user:
    effects:
        - clear session
        - redirect to SCR_LOGIN

3.4 Query Parameters

None.

3.5 Derived Fields

None.

3.6 UI Data Constraints

Logout must always succeed, even if session was already invalid.

No user input is expected.