import logging
from datetime import date

from src.db.department_repository import DepartmentRepository
from src.db.employee_repository import EmployeeRepository
from src.models import Employee

from src.services.decorators import handle_service_errors
from src.services.exceptions import DepartmentNotFoundError, InvalidDateError


logger = logging.getLogger(__name__)


@handle_service_errors
class EmployeeService:
    """Сервис для работы с сотрудниками."""

    def __init__(
        self,
        department_repo: DepartmentRepository,
        employee_repo: EmployeeRepository,
    ):
        self.department_repo = department_repo
        self.employee_repo = employee_repo

    async def create_employee(
        self,
        department_id: int,
        full_name: str,
        position: str,
        hired_at: str | None = None,
    ) -> Employee:
        """Создать сотрудника."""
        department = await self.department_repo.get_by_id(department_id)
        if not department:
            raise DepartmentNotFoundError(department_id)

        hired_at_date: date | None = None
        if hired_at:
            try:
                hired_at_date = date.fromisoformat(hired_at)
            except ValueError:
                raise InvalidDateError("hired_at")

        return await self.employee_repo.create(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=hired_at_date,
        )
