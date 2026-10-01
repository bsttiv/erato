from typing import Any, Dict, Optional


class AppError(Exception):
    """Base domain exception with HTTP status code and structured representation."""

    status_code: int = 500
    code: str = "internal_error"
    message: str = "Error interno del servidor"

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Any] = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.code = code or self.__class__.code
        self.status_code = status_code or self.__class__.status_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "error": self.code,
            "message": self.message,
            "detail": self.message,
        }
        if self.details is not None:
            result["details"] = self.details
        return result


class NotFoundError(AppError):
    status_code: int = 404
    code: str = "not_found"
    message: str = "Recurso no encontrado"


class ForbiddenError(AppError):
    status_code: int = 403
    code: str = "forbidden"
    message: str = "No tienes permiso para realizar esta acción"


class UnauthorizedError(AppError):
    status_code: int = 401
    code: str = "unauthorized"
    message: str = "No autenticado"


class ValidationError(AppError):
    status_code: int = 422
    code: str = "validation_error"
    message: str = "Datos de solicitud inválidos"


class ConflictError(AppError):
    status_code: int = 409
    code: str = "conflict"
    message: str = "El recurso ya existe"


class DatabaseConnectionError(AppError):
    status_code: int = 503
    code: str = "database_unavailable"
    message: str = "Servicio de base de datos no disponible temporalmente"


class InternalError(AppError):
    status_code: int = 500
    code: str = "internal_error"
    message: str = "Error interno del servidor"


def resolve_permission_denial(can_view: bool = False, message: Optional[str] = None) -> AppError:
    """Implement 404-vs-403 rule from design.md.

    If the caller cannot view a private composition, returns NotFoundError (404)
    to prevent existence probing. If the caller can view but lacks write rights,
    returns ForbiddenError (403).
    """
    if not can_view:
        return NotFoundError(message or "Recurso no encontrado")
    return ForbiddenError(message or "No tienes permiso para realizar esta acción")
