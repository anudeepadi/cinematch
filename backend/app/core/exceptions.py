from fastapi import HTTPException, status


class CineMatchException(HTTPException):
    """Base exception for CineMatch application"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict | None = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthenticationError(CineMatchException):
    """Raised when authentication fails"""
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(CineMatchException):
    """Raised when user lacks permission"""
    def __init__(self, detail: str = "Not authorized to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundError(CineMatchException):
    """Raised when a resource is not found"""
    def __init__(self, resource: str = "Resource", detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or f"{resource} not found"
        )


class ValidationError(CineMatchException):
    """Raised when validation fails"""
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class ExternalAPIError(CineMatchException):
    """Raised when an external API call fails"""
    def __init__(self, service: str, detail: str | None = None):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail or f"Error communicating with {service}"
        )


class RateLimitError(CineMatchException):
    """Raised when rate limit is exceeded"""
    def __init__(self, detail: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )


class ConflictError(CineMatchException):
    """Raised when there's a conflict (e.g., duplicate resource)"""
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )
