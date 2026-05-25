"""Custom application exceptions with error codes."""


class AppException(Exception):
    """Base application exception with code, message, and HTTP status."""

    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidCredentialsException(AppException):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(code=401001, message=message, status_code=401)


class TokenExpiredException(AppException):
    """Raised when the JWT token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(code=401002, message=message, status_code=401)


class PermissionDeniedException(AppException):
    """Raised when the user lacks required permissions."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(code=403001, message=message, status_code=403)


class ResourceNotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(code=404001, message=message, status_code=404)


class InvalidStateTransitionException(AppException):
    """Raised when a state transition is not allowed."""

    def __init__(self, message: str = "Invalid state transition"):
        super().__init__(code=400001, message=message, status_code=400)


class AIProviderUnavailableException(AppException):
    """Raised when an AI provider is not available."""

    def __init__(self, message: str = "AI provider unavailable"):
        super().__init__(code=503001, message=message, status_code=503)
