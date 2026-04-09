class AppError(Exception):
    def __init__(self, message: str, *, code: str, status_code: int) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class BadRequestError(AppError):
    def __init__(self, message: str, *, code: str = "bad_request") -> None:
        super().__init__(message, code=code, status_code=400)


class UnauthorizedError(AppError):
    def __init__(self, message: str, *, code: str = "unauthorized") -> None:
        super().__init__(message, code=code, status_code=401)


class NotFoundError(AppError):
    def __init__(self, message: str, *, code: str = "not_found") -> None:
        super().__init__(message, code=code, status_code=404)


class IntegrationError(AppError):
    def __init__(self, message: str, *, code: str = "integration_error") -> None:
        super().__init__(message, code=code, status_code=502)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str, *, code: str = "service_unavailable") -> None:
        super().__init__(message, code=code, status_code=503)
