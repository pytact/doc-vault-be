"""Authentication constants."""

# Error Messages
ERROR_INVALID_CREDENTIALS = "Invalid email or password"
ERROR_USER_NOT_ACTIVATED = "Account not activated. Please check your invitation email."
ERROR_USER_SOFT_DELETED = "User account has been deleted"
ERROR_FAMILY_SOFT_DELETED = "User's family has been deleted"
ERROR_TOKEN_EXPIRED = "Token has expired"
ERROR_INVALID_TOKEN = "Invalid token"

# Success Messages
SUCCESS_LOGIN = "Login successful"
SUCCESS_LOGOUT = "Logout successful"

# Error Codes
ERROR_CODE_INVALID_CREDENTIALS = "UNAUTHENTICATED"
ERROR_CODE_USER_NOT_ACTIVATED = "USER_NOT_ACTIVATED"
ERROR_CODE_USER_SOFT_DELETED = "USER_SOFT_DELETED"
ERROR_CODE_FAMILY_SOFT_DELETED = "FAMILY_SOFT_DELETED"
ERROR_CODE_TOKEN_EXPIRED = "TOKEN_EXPIRED"
ERROR_CODE_INVALID_TOKEN = "INVALID_TOKEN"

# Token Configuration
TOKEN_TYPE_BEARER = "bearer"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600  # 1 hour

# User Status Values
USER_STATUS_ACTIVE = "active"
USER_STATUS_PENDING = "pending"
USER_STATUS_INACTIVE = "inactive"

# Family Status Values
FAMILY_STATUS_ACTIVE = "active"
FAMILY_STATUS_SOFT_DELETED = "inactive"
