from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import AsyncSessionLocal
from src.db.department_repository import DepartmentRepository
from src.db.employee_repository import EmployeeRepository
from src.services.department_service import DepartmentService
from src.services.employee_service import EmployeeService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения асинхронной сессии БД."""
    async with AsyncSessionLocal() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_department_service(db: DbSession) -> DepartmentService:
    """Зависимость для получения сервиса подразделений."""
    return DepartmentService(
        department_repo=DepartmentRepository(db),
        employee_repo=EmployeeRepository(db),
    )


async def get_employee_service(db: DbSession) -> EmployeeService:
    """Зависимость для получения сервиса сотрудников."""
    return EmployeeService(
        department_repo=DepartmentRepository(db),
        employee_repo=EmployeeRepository(db),
    )


DepartmentServiceDep = Annotated[DepartmentService, Depends(get_department_service)]
EmployeeServiceDep = Annotated[EmployeeService, Depends(get_employee_service)]


__all__ = [
    "DbSession",
    "DepartmentServiceDep",
    "EmployeeServiceDep",
    "get_db",
    "get_department_service",
    "get_employee_service",
]
