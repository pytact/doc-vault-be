1. Feature Summary

The F-001: Core Identity, Access & Organization feature provides the full identity and tenant-isolation framework for DocValut. It includes all UI flows required for:

Managing Families (tenants)

Managing Users within Families

Assigning Roles to Users

Inviting and onboarding new Users

Authenticating (login/logout)

User Profile management (name & password updates)

User soft-delete and Family soft-delete operations

This contract unifies all the UI data needs from F01A–F01H as a single feature, ensuring backend API design can satisfy all end-to-end identity-layer requirements.

2. Screens Covered

Below are all screens and modals defined across F01A–F01H.
Names follow the required format SCR_<FEATURE>_<NAME> or MODAL_<NAME>.

2.1 User List / User Management Screens
- SCR_USER_LIST
- SCR_USER_DETAIL

2.2 Invitation & Onboarding Screens
- SCR_INVITE_ACTIVATION_VALIDATE
- SCR_INVITE_EXPIRED
- SCR_ACCOUNT_SETUP

2.3 Authentication Screens
- SCR_LOGIN
- SCR_LOGOUT_REDIRECT

2.4 Family Management Screens
- SCR_FAMILY_LIST
- SCR_FAMILY_DETAIL
- SCR_FAMILY_NOT_ACCESSIBLE

2.5 Profile Settings Screens
- SCR_PROFILE_SETTINGS

2.6 Modals
- MODAL_INVITE_USER
- MODAL_MANAGE_USER_ROLES
- MODAL_SOFT_DELETE_USER
- MODAL_CREATE_FAMILY
- MODAL_EDIT_FAMILY_NAME
- MODAL_DELETE_FAMILY
- MODAL_CHANGE_PASSWORD
- MODAL_SOFT_DELETE_FAMILY

✔ All screens above are directly supported by uploaded UF1 files:

F01A Invitation & Onboarding

F01B Authentication

F01C Account Setup

F01D Family Management

F01E Profile Management

F01F Role Assignment

F01G User Soft Delete

F01H Family Soft Delete