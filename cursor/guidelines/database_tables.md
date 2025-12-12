# DocFamily Database Tables

This document contains all database tables with dummy records.

**Total Tables: 8**

---

## 1. Users Table

Stores user accounts with invite/activation workflow.

| id     | email              | hash_password | status | invite_token | invite_sent_at | invite_expire_at | invited_by | activated_at | is_del | created_at | created_by | updated_at | updated_by |
|--------|--------------------|---------------|--------|--------------|----------------|------------------|------------|--------------|--------|------------|------------|------------|------------|
| USR001 | superadmin@df.com  | $hash1        | active | -            | -              | -                | -          | 2024-01-01   | false  | 2024-01-01 | system     | 2024-01-01 | system     |
| USR002 | raj@df.com         | $hash2        | active | -            | 2024-01-10     | 2024-01-17       | USR001     | 2024-01-15   | false  | 2024-01-10 | USR001     | 2024-01-15 | USR001     |
| USR003 | meera@df.com       | $hash3        | active | -            | -              | -                | USR002     | 2024-01-12   | false  | 2024-01-12 | USR002     | 2024-01-12 | USR002     |
| USR004 | amit@df.com        | $hash4        | active | -            | -              | -                | USR002     | 2024-01-13   | false  | 2024-01-13 | USR002     | 2024-01-13 | USR002     |

---

## 2. Roles Table

Defines 5 role types with JSON permission definitions.

| id      | name        | permissions (json)                        |
|---------|-------------|-------------------------------------------|
| ROLE001 | superadmin  | `{ "family:manage_all": true, ... }`      |
| ROLE002 | familyadmin | `{ "document:view_all": true, ... }`      |
| ROLE003 | member      | `{ "document:create": true, ... }`        |
| ROLE004 | viewer      | `{ "document:view_assigned": true }`      |
| ROLE005 | editor      | `{ "document:edit_assigned": true, ... }` |

---

## 3. Families Table

Organizational units (tenants) for grouping users and documents.

| id     | name          | status | is_del | created_at | created_by | updated_at | updated_by |
|--------|---------------|--------|--------|------------|------------|------------|------------|
| FAM001 | Sharma Family | active | false  | 2024-01-01 | USR001     | 2024-01-01 | USR001     |
| FAM002 | Patel Family  | active | false  | 2024-03-01 | USR001     | 2024-03-01 | USR001     |

---

## 4. User_Roles Table

Maps users to roles within families (many-to-many relationship).

| id    | user_id | family_id | role_id |
|-------|---------|-----------|---------|
| UR001 | USR001  | NULL      | ROLE001 |
| UR002 | USR002  | FAM001    | ROLE002 |
| UR003 | USR002  | FAM001    | ROLE003 |
| UR004 | USR003  | FAM001    | ROLE003 |
| UR005 | USR004  | FAM001    | ROLE004 |

---

## 5. Categories Table

Document categories for organizing documents by type.

| id     | name             | description                              |
|--------|------------------|------------------------------------------|
| CAT001 | Identity         | Personal identification documents        |
| CAT002 | Educational      | Academic certificates and records        |
| CAT003 | Professional     | Employment and career documents          |
| CAT004 | Financial        | Banking, tax, and investment documents   |
| CAT005 | Insurance        | Insurance policies and claims            |
| CAT006 | Bills & Receipts | Utility bills and purchase receipts      |
| CAT007 | Contracts        | Legal agreements and contracts           |
| CAT008 | Property         | Real estate and property documents       |
| CAT009 | Vehicle          | Vehicle registration and related docs    |
| CAT010 | Medical          | Health records and prescriptions         |
| CAT011 | Legal            | Court orders and legal documents         |
| CAT012 | Travel           | Visa and travel related documents        |
| CAT013 | Warranty         | Product warranties and AMC documents     |
| CAT014 | Membership       | Club and subscription memberships        |
| CAT015 | Others           | Miscellaneous documents                  |

---

## 6. Subcategories Table

Specific document types within each category.

| id     | category_id | name                   | description                              |
|--------|-------------|------------------------|------------------------------------------|
| SUB001 | CAT001      | Aadhar Card            | 12-digit unique identification           |
| SUB002 | CAT001      | PAN Card               | Permanent Account Number for tax         |
| SUB003 | CAT001      | Voter ID               | Election identity card                   |
| SUB004 | CAT001      | Passport               | International travel document            |
| SUB005 | CAT001      | Driving License        | Vehicle driving permit                   |
| SUB006 | CAT001      | Birth Certificate      | Proof of birth                           |
| SUB007 | CAT001      | Marriage Certificate   | Proof of marriage                        |
| SUB008 | CAT001      | Ration Card            | Food subsidy entitlement                 |
| SUB009 | CAT002      | Degree Certificate     | University degree                        |
| SUB010 | CAT002      | Marksheet              | Academic score records                   |
| SUB011 | CAT002      | Transcript             | Detailed academic records                |
| SUB012 | CAT002      | Migration Certificate  | Transfer between institutions            |
| SUB013 | CAT002      | Diploma Certificate    | Professional diploma                     |
| SUB014 | CAT002      | Course Certificate     | Short course completion                  |
| SUB015 | CAT003      | Resume/CV              | Career summary document                  |
| SUB016 | CAT003      | Offer Letter           | Job offer documentation                  |
| SUB017 | CAT003      | Experience Letter      | Work experience proof                    |
| SUB018 | CAT003      | Payslip                | Monthly salary statement                 |
| SUB019 | CAT003      | Relieving Letter       | Employment termination proof             |
| SUB020 | CAT003      | Appraisal Letter       | Performance review document              |
| SUB021 | CAT004      | Bank Statement         | Account transaction records              |
| SUB022 | CAT004      | Tax Returns            | Income tax filing documents              |
| SUB023 | CAT004      | Investment Document    | Mutual funds, stocks, bonds              |
| SUB024 | CAT004      | FD Receipt             | Fixed deposit certificate                |
| SUB025 | CAT004      | Loan Document          | Loan agreement and EMI details           |
| SUB026 | CAT004      | Credit Card Statement  | Monthly credit card records              |
| SUB027 | CAT005      | Life Insurance         | Life coverage policy                     |
| SUB028 | CAT005      | Health Insurance       | Medical coverage policy                  |
| SUB029 | CAT005      | Vehicle Insurance      | Car/bike insurance policy                |
| SUB030 | CAT005      | Home Insurance         | Property insurance policy                |
| SUB031 | CAT005      | Travel Insurance       | Trip coverage policy                     |
| SUB032 | CAT005      | Insurance Claim        | Claim submission documents               |
| SUB033 | CAT006      | Electricity Bill       | Power utility bill                       |
| SUB034 | CAT006      | Water Bill             | Water utility bill                       |
| SUB035 | CAT006      | Gas Bill               | Gas utility bill                         |
| SUB036 | CAT006      | Internet Bill          | Broadband/WiFi bill                      |
| SUB037 | CAT006      | Mobile Bill            | Phone bill                               |
| SUB038 | CAT006      | Purchase Receipt       | Product purchase proof                   |
| SUB039 | CAT006      | Invoice                | Service/product invoice                  |
| SUB040 | CAT007      | Rental Agreement       | House/office rent contract               |
| SUB041 | CAT007      | Employment Contract    | Job terms and conditions                 |
| SUB042 | CAT007      | NDA                    | Non-disclosure agreement                 |
| SUB043 | CAT007      | Sale Deed              | Property sale agreement                  |
| SUB044 | CAT007      | Service Agreement      | Service provider contract                |
| SUB045 | CAT008      | Property Registration  | Registered property deed                 |
| SUB046 | CAT008      | Land Records           | Land ownership documents                 |
| SUB047 | CAT008      | House Tax Receipt      | Property tax payment                     |
| SUB048 | CAT008      | Society Documents      | Housing society papers                   |
| SUB049 | CAT008      | Encumbrance Certificate| Property liability proof                 |
| SUB050 | CAT009      | RC Book                | Vehicle registration certificate         |
| SUB051 | CAT009      | PUC Certificate        | Pollution under control certificate      |
| SUB052 | CAT009      | Vehicle Service Record | Maintenance history                      |
| SUB053 | CAT009      | Challan Receipt        | Traffic fine payment                     |
| SUB054 | CAT010      | Health Report          | Medical checkup results                  |
| SUB055 | CAT010      | Prescription           | Doctor's medication order                |
| SUB056 | CAT010      | Lab Report             | Diagnostic test results                  |
| SUB057 | CAT010      | Vaccination Record     | Immunization history                     |
| SUB058 | CAT010      | Discharge Summary      | Hospital discharge papers                |
| SUB059 | CAT010      | Medical Bill           | Hospital/clinic payment                  |
| SUB060 | CAT011      | Court Order            | Judicial order document                  |
| SUB061 | CAT011      | Affidavit              | Sworn statement                          |
| SUB062 | CAT011      | FIR Copy               | Police complaint copy                    |
| SUB063 | CAT011      | Power of Attorney      | Legal authority delegation               |
| SUB064 | CAT011      | Will                   | Testament document                       |
| SUB065 | CAT011      | Succession Certificate | Inheritance proof                        |
| SUB066 | CAT012      | Visa Document          | Travel visa                              |
| SUB067 | CAT012      | Boarding Pass          | Flight boarding ticket                   |
| SUB068 | CAT012      | Hotel Booking          | Accommodation confirmation               |
| SUB069 | CAT012      | Itinerary              | Travel plan details                      |
| SUB070 | CAT012      | Travel Ticket          | Train/bus/flight ticket                  |
| SUB071 | CAT013      | Product Warranty       | Manufacturer warranty card               |
| SUB072 | CAT013      | Extended Warranty      | Additional warranty coverage             |
| SUB073 | CAT013      | AMC Document           | Annual maintenance contract              |
| SUB074 | CAT014      | Gym Membership         | Fitness club membership                  |
| SUB075 | CAT014      | Club Membership        | Social/sports club membership            |
| SUB076 | CAT014      | Library Card           | Library membership                       |
| SUB077 | CAT014      | Subscription           | Digital/service subscription             |
| SUB078 | CAT015      | Other Document         | Miscellaneous document                   |

---

## 7. Documents Table

Stores documents owned by users within families.

| id    | family_id | owner_id | category_id | subcategory_id | title            | expiry_date | details (json)                                                                 |
|-------|-----------|----------|-------------|----------------|------------------|-------------|--------------------------------------------------------------------------------|
| DOC01 | FAM001    | USR003   | CAT008      | SUB045         | Property Docs    | -           | `{ "name": "Meera Sharma", "number": "PROP-2024-12345" }`                      |
| DOC02 | FAM001    | USR003   | CAT010      | SUB054         | Medical Reports  | -           | `{ "name": "Meera Sharma", "number": "MED-RPT-2024-001" }`                     |
| DOC03 | FAM001    | USR002   | CAT004      | SUB022         | Tax Returns 2024 | 2025-03-31  | `{ "name": "Raj Sharma", "number": "PAN-ABCDE1234F" }`                         |
| DOC04 | FAM001    | USR003   | CAT001      | SUB001         | Aadhar Card      | -           | `{ "name": "Meera Sharma", "number": "1234-5678-9012" }`                       |
| DOC05 | FAM001    | USR002   | CAT001      | SUB002         | PAN Card         | -           | `{ "name": "Raj Sharma", "number": "ABCDE1234F" }`                             |
| DOC06 | FAM001    | USR003   | CAT001      | SUB004         | Passport         | 2034-05-15  | `{ "name": "Meera Sharma", "number": "J1234567" }`                             |
| DOC07 | FAM001    | USR002   | CAT001      | SUB005         | Driving License  | 2030-01-20  | `{ "name": "Raj Sharma", "number": "MH01-2020-0012345" }`                      |
| DOC08 | FAM001    | USR003   | CAT005      | SUB028         | Health Insurance | 2025-12-31  | `{ "name": "Meera Sharma", "number": "HI-2024-98765" }`                        |

### Details JSON Structure

The `details` column stores document-specific information in JSON format:

```json
{
  "name": "Name as per document",
  "number": "Document number/ID"
}
```

#### Examples by Document Type:

| Subcategory        | Example JSON                                              |
|--------------------|-----------------------------------------------------------|
| Aadhar Card        | `{ "name": "Meera Sharma", "number": "1234-5678-9012" }`  |
| PAN Card           | `{ "name": "Raj Sharma", "number": "ABCDE1234F" }`        |
| Passport           | `{ "name": "Meera Sharma", "number": "J1234567" }`        |
| Driving License    | `{ "name": "Raj Sharma", "number": "MH01-2020-0012345" }` |
| Voter ID           | `{ "name": "Amit Kumar", "number": "ABC1234567" }`        |
| Health Insurance   | `{ "name": "Meera Sharma", "number": "HI-2024-98765" }`   |
| Vehicle Insurance  | `{ "name": "Raj Sharma", "number": "POL-VEH-123456" }`    |
| RC Book            | `{ "name": "Raj Sharma", "number": "MH01AB1234" }`        |
| Bank Statement     | `{ "name": "Meera Sharma", "number": "ACC-123456789" }`   |
| Degree Certificate | `{ "name": "Amit Kumar", "number": "DEG-2020-5678" }`     |

---

## 8. Document_Assign Table

Per-document sharing with viewer/editor access assignments.

| id    | document_id | owner_id | assign_to | access_type |
|-------|-------------|----------|-----------|-------------|
| DA001 | DOC01       | USR003   | USR004    | viewer      |
| DA002 | DOC01       | USR003   | USR002    | editor      |

---

## Table Relationships

```
                              Categories
                                  │
                                  ▼
                            Subcategories
                                  │
                                  ▼
Users ──────┬────────────> User_Roles <──────────── Roles
            │                  │
            │                  │
            │                  ▼
            │              Families
            │                  │
            ▼                  ▼
        Documents <────── Document_Assign
            │
            └──────────> Categories / Subcategories
```

---

## User Summary

| User   | Email             | Role(s)              | Family        |
|--------|-------------------|----------------------|---------------|
| USR001 | superadmin@df.com | SuperAdmin           | None (global) |
| USR002 | raj@df.com        | FamilyAdmin + Member | Sharma Family |
| USR003 | meera@df.com      | Member               | Sharma Family |
| USR004 | amit@df.com       | Viewer               | Sharma Family |

---

## Summary

| Table           | Records |
|-----------------|---------|
| Users           |       4 |
| Roles           |       5 |
| Families        |       2 |
| User_Roles      |       5 |
| Categories      |      15 |
| Subcategories   |      78 |
| Documents       |       3 |
| Document_Assign |       2 |
| **Total**       | **114** |
