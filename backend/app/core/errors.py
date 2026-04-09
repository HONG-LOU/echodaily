class AppError(Exception):
    def __init__(self, message: str, *, code: str, status_code: int) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str, *, code: str = "not_found") -> None:
        super().__init__(message, code=code, status_code=404)
