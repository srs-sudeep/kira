"""KIRA Identity Service — custom domain exceptions."""


class KiraBaseException(Exception):
    """Base exception for all KIRA errors."""


class NotFoundError(KiraBaseException):
    def __init__(self, resource: str, resource_id: str | int):
        self.resource = resource
        self.resource_id = resource_id
        super().__init__(f"{resource} '{resource_id}' not found.")


class ConflictError(KiraBaseException):
    def __init__(self, message: str):
        super().__init__(message)


class ForbiddenError(KiraBaseException):
    def __init__(self, message: str = "Access denied."):
        super().__init__(message)


class UnauthorizedError(KiraBaseException):
    def __init__(self, message: str = "Authentication required."):
        super().__init__(message)


class ValidationError(KiraBaseException):
    def __init__(self, message: str):
        super().__init__(message)
