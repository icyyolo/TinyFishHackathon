class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, payload=None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}


class ValidationError(AppError):
    def __init__(self, message, payload=None) -> None:
        super().__init__(message, status_code=422, payload=payload)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message, status_code=404)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)