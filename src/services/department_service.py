import logging
from typing import Any

from src.db.department_repository import DepartmentRepository
from src.db.employee_repository import EmployeeRepository
from src.models import Department

from src.services.decorators import handle_service_errors
from src.services.exceptions import (
    DepartmentNotFoundError,
    DepartmentNameConflictError,
    DepartmentCycleError,
    ReassignTargetRequiredError,
    ReassignTargetNotFoundError,
)
from src.schemas.common import TransferMode


logger = logging.getLogger(__name__)


@handle_service_errors
class DepartmentService:
    """Сервис для работы с подразделениями."""

    def __init__(
        self,
        department_repo: DepartmentRepository,
        employee_repo: EmployeeRepository,
    ):
        self.department_repo = department_repo
        self.employee_repo = employee_repo

    async def create_department(self, name: str, parent_id: int | None = None) -> Department:
        """Создать подразделение с валидацией."""
        existing = await self.department_repo.get_by_name_and_parent(name, parent_id)
        if existing:
            raise DepartmentNameConflictError(parent_id)

        if parent_id is not None:
            parent = await self.department_repo.get_by_id(parent_id)
            if not parent:
                raise DepartmentNotFoundError(parent_id)

        return await self.department_repo.create(name=name, parent_id=parent_id)

    async def get_department(
        self,
        id: int,
        depth: int = 1,
        include_employees: bool = True,
    ) -> dict[str, Any]:
        """Получить подразделение с сотрудниками и дочерними подразделениями."""
        result = await self.department_repo.get_with_children_tree(
            id, depth=depth, include_employees=include_employees
        )
        if result is None:
            raise DepartmentNotFoundError(id)
        return result

    async def update_department(
        self,
        id: int,
        name: str | None = None,
        parent_id: int | None = None,
    ) -> Department:
        """Обновить подразделение с валидацией."""
        department = await self.department_repo.get_by_id(id)
        if not department:
            raise DepartmentNotFoundError(id)

        if name == department.name and parent_id == department.parent_id:
            return department

        if parent_id is not None and await self.department_repo.has_cycle(id, parent_id):
            raise DepartmentCycleError()

        check_parent_id = parent_id if parent_id is not None else department.parent_id
        check_name = name if name is not None else department.name
        existing = await self.department_repo.get_by_name_and_parent(check_name, check_parent_id)
        if existing and existing.id != id:
            raise DepartmentNameConflictError(check_parent_id)

        return await self.department_repo.update(department, name=name, parent_id=parent_id)

    async def delete_department(
        self,
        id: int,
        mode: TransferMode = TransferMode.cascade,
        reassign_to_department_id: int | None = None,
    ) -> bool:
        """Удалить подразделение."""
        department = await self.department_repo.get_by_id(id)
        if not department:
            raise DepartmentNotFoundError(id)

        if mode == TransferMode.cascade:
            await self.department_repo.delete(department)
        elif mode == TransferMode.reassign:
            if reassign_to_department_id is None:
                raise ReassignTargetRequiredError()

            target = await self.department_repo.get_by_id(reassign_to_department_id)
            if not target:
                raise ReassignTargetNotFoundError(reassign_to_department_id)

            employee_ids = await self.department_repo.get_all_employees_ids([id])

            if employee_ids:
                await self.employee_repo.update_department(employee_ids, reassign_to_department_id)

            children = await self.department_repo.get_children(id)
            if children:
                child_ids = [child.id for child in children]
                await self.department_repo.reassign_parent(child_ids, department.parent_id)

            await self.department_repo.delete(department)

        return True
