7. Final Assembly Notes & Integrity Confirmation

You have now received the entire unified F-001 UI Data Contract across Messages 1–6, containing:

Feature Summary

Screens Covered

Data Requirements per Screen (all 20+ screens and modals)

Proposed API Hints

Cross-Screen Data Dependencies

Data Edge Cases

This represents the complete UI-facing data specification needed for the API Spec Builder to design a correct backend contract.

✅ This Contract Is Fully Valid and Self-Contained

It meets all rules from your GPT instructions:

Does not define UI layouts

Does not define APIs

Does not contradict the domain model

Covers every screen from UF1 inputs

Stays within the single feature boundary (F-001)

Defines Reads / Writes / Query Params / Derived Fields / Constraints

Identifies cross-screen dependencies and edge cases

Provides logical API hints, without specifying schema/transport

📄 How to Assemble the Final ui_data_contract.md File

Combine the content from:

Message 1 → Sections 1–2

Message 2 → Section 3 (User List, User Detail, key modals)

Message 3 → Section 3 (Invite + Activation + Authentication)

Message 4 → Section 3 (Family Management + Soft Delete)

Message 5 → Section 3 (Profile Settings)

Message 6 → Sections 4–6

Message 7 → Section 7 (Assembly Notes)

Concatenate them in order into a single Markdown file named:

ui_data_contract.md


No additional rewriting is required—each section was written to be directly pasted into the final file without modification.

🔍 Optional: Recommended Final Structure Block

For clarity, here is the exact expected outline of the final file:

# ui_data_contract.md

1. Feature Summary
2. Screens Covered

3. Data Requirements Per Screen
   3.1 SCR_USER_LIST
   3.2 SCR_USER_DETAIL
   3.3 MODAL_INVITE_USER
   3.4 MODAL_MANAGE_USER_ROLES
   3.5 MODAL_SOFT_DELETE_USER
   3.6 SCR_INVITE_ACTIVATION_VALIDATE
   3.7 SCR_INVITE_EXPIRED
   3.8 SCR_ACCOUNT_SETUP
   3.9 SCR_LOGIN
   3.10 SCR_LOGOUT_REDIRECT
   3.11 SCR_FAMILY_LIST
   3.12 SCR_FAMILY_DETAIL
   3.13 SCR_FAMILY_NOT_ACCESSIBLE
   3.14 MODAL_CREATE_FAMILY
   3.15 MODAL_EDIT_FAMILY_NAME
   3.16 MODAL_DELETE_FAMILY
   3.17 MODAL_SOFT_DELETE_FAMILY
   3.18 SCR_PROFILE_SETTINGS
   3.19 MODAL_CHANGE_PASSWORD

4. Proposed API Hints
5. Cross-Screen Data Dependencies
6. Data Edge Cases
7. Final Assembly Notes & Integrity Confirmation