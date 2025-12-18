"""Dashboard API documentation."""
from typing import ClassVar


class DashboardApiDocs:
    """API documentation for dashboard endpoints."""
    
    get_dashboard_analytics: ClassVar[dict] = {
        "summary": "Purpose of this API is to get platform-wide dashboard summary metrics",
        "description": "Gets platform-wide dashboard summary metrics. SuperAdmin only. Provides total families, users, and documents counts (including soft-deleted), active families and users counts, and soft-deleted families and users counts. Metrics are computed at request time. SuperAdmin cannot see document details or metadata (only counts)."
    }

