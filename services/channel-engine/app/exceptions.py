class KiraBaseException(Exception):
    """Base exception for Project Kira."""


class NotFoundError(KiraBaseException):
    def __init__(self, resource: str, id: str | int):
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} '{id}' not found")


class ConflictError(KiraBaseException):
    def __init__(self, message: str):
        super().__init__(message)


class ForbiddenError(KiraBaseException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message)


class UnauthorizedError(KiraBaseException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message)


class ValidationError(KiraBaseException):
    def __init__(self, message: str):
        super().__init__(message)


class ChannelSyncError(KiraBaseException):
    def __init__(self, channel_id: str, message: str):
        super().__init__(f"Channel '{channel_id}' sync error: {message}")
