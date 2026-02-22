import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from src.services.exceptions import ServiceError


logger = logging.getLogger(__name__)


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """Обработчик кастомных ошибок сервиса."""
    if exc.status_code >= 500:
        logger.exception(f"Service error: {exc.code} - {exc.message}")
    else:
        logger.warning(f"Service error: {exc.code} - {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message},
    )
