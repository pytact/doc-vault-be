"""Document API documentation."""
from typing import ClassVar


class DocumentApiDocs:
    """API documentation for Document endpoints."""
    
    create: ClassVar[dict] = {
        "summary": "Purpose of this API is to create document with metadata and optionally upload file",
        "description": (
            "Creates a new document with metadata and optionally uploads the PDF file in a single request. "
            "Accepts multipart/form-data with document metadata fields and an optional file. "
            "Only Member (Owner) and FamilyAdmin can create documents. Document is created with owner_user_id "
            "set to current user ID. Category and subcategory must be valid and subcategory must belong "
            "to the selected category. File must be PDF format (application/pdf) and maximum 5MB. "
            "Returns created document with all metadata fields including file information if uploaded."
        ),
    }
    
    replace_file: ClassVar[dict] = {
        "summary": "Purpose of this API is to replace existing PDF file",
        "description": (
            "Replaces existing PDF file (overwrite behavior, no versioning). Document Owner, "
            "Editor, and FamilyAdmin can replace files. File must be PDF format (application/pdf) "
            "and maximum 5MB. Requires If-Match header for ETag validation to prevent concurrent "
            "modifications. Previous file versions are not retained. Returns updated file metadata."
        ),
    }
    
    get_file: ClassVar[dict] = {
        "summary": "Purpose of this API is to preview or download PDF file",
        "description": (
            "Retrieves PDF file for preview (inline viewing) or download (attachment). Document "
            "Owner, Viewer, Editor, and FamilyAdmin can access files. Supports cache validation "
            "via If-None-Match header (returns 304 if unchanged). Query parameter 'mode' controls "
            "Content-Disposition header: 'preview' for inline viewing, 'download' for attachment. "
            "Returns raw binary PDF file data with appropriate headers."
        ),
    }
    
    list: ClassVar[dict] = {
        "summary": "Purpose of this API is to list documents with pagination, filtering, search, and sorting",
        "description": (
            "Retrieves a paginated list of documents accessible to the user. Member (Owner) sees "
            "own documents and shared documents via F-004. Viewer and Editor see assigned documents "
            "only. FamilyAdmin sees all documents in their family. Supports filtering by category_id, "
            "subcategory_id, owner_user_id, expiry_date. Search is case-insensitive partial match "
            "on title + category/subcategory names (details_json is NOT searchable). Supports "
            "sorting by created_at, updated_at, title, expiry_date. Soft-deleted documents are "
            "excluded from results."
        ),
    }
    
    get: ClassVar[dict] = {
        "summary": "Purpose of this API is to get single document with full metadata",
        "description": (
            "Retrieves a single document with full metadata, including user's permission level "
            "for the document. Document Owner, Viewer, Editor, and FamilyAdmin can access. "
            "Supports cache validation via If-None-Match header (returns 304 if unchanged). "
            "Response includes permission field indicating user's access level: 'owner', 'editor', "
            "or 'viewer'. Returns 404 if document not found or soft-deleted."
        ),
    }
    
    update: ClassVar[dict] = {
        "summary": "Purpose of this API is to update document metadata",
        "description": (
            "Updates document metadata (title, category, subcategory, expiry_date, details_json). "
            "All editable metadata fields are editable by Owner, Editor, and FamilyAdmin. "
            "Category-subcategory pairing is validated (subcategory must belong to selected category). "
            "Requires If-Match header for ETag validation to prevent concurrent modifications. "
            "Returns updated document with new ETag. Use null to clear expiry_date or details_json."
        ),
    }
    
    delete: ClassVar[dict] = {
        "summary": "Purpose of this API is to soft delete document",
        "description": (
            "Soft deletes document (permanent and irreversible). Sets is_del=true, removes "
            "document from access and listings. Only Document Owner and FamilyAdmin can delete. "
            "Requires If-Match header for ETag validation to prevent concurrent modifications. "
            "Soft-deleted documents cannot be recovered and are excluded from all listings and "
            "access checks. Returns 204 No Content on success."
        ),
    }
