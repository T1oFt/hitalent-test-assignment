import logging
from functools import wraps
from typing import Any

from src.services.exceptions import ServiceError, InternalError


logger = logging.getLogger(__name__)


def _wrap_method(func: Any) -> Any:
    """Обернуть метод для защиты от непредвиденных ошибок."""

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except ServiceError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
            raise InternalError("Внутренняя ошибка сервера")

    return async_wrapper


def handle_service_errors(cls):
    """
    Декоратор класса для защиты от непредвиденных ошибок.

    Обёртывает все публичные методы класса. Кастомные исключения
    (ServiceError) пропускаются дальше для обработки в exception_handler,
    а все остальные ошибки оборачиваются в InternalError.
    """
    for attr_name, attr_value in cls.__dict__.items():
        if not attr_name.startswith("_") and callable(attr_value):
            setattr(cls, attr_name, _wrap_method(attr_value))
    return cls
