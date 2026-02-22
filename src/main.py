import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.departments import router as departments_router
from src.api.employees import router as employees_router
from src.api.exception_handlers import service_error_handler
from src.config import settings
from src.db.base import engine
from src.services.exceptions import ServiceError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Управление жизненным циклом приложения."""
    # Startup
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    await engine.dispose()


def create_application() -> FastAPI:
    """Создать и настроить приложение FastAPI."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="API организационной структуры",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Регистрация exception handlers
    app.add_exception_handler(ServiceError, service_error_handler)

    # Подключение роутов
    app.include_router(departments_router, prefix="/api/v1")
    app.include_router(employees_router, prefix="/api/v1")

    @app.get("/health")
    def health_check():
        """Проверка здоровья приложения."""
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_application()
