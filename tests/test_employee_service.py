import pytest
from unittest.mock import AsyncMock

from src.services.employee_service import EmployeeService
from src.services.exceptions import (
    DepartmentNotFoundError,
    InvalidDateError,
)
from src.db.department_repository import DepartmentRepository
from src.db.employee_repository import EmployeeRepository

from tests.conftest import create_mock_department, create_mock_employee


def create_employee_service(
    mock_department_repo: AsyncMock,
    mock_employee_repo: AsyncMock,
) -> EmployeeService:
    """Создание сервиса сотрудников с мокированными репозиториями."""
    service = EmployeeService.__new__(EmployeeService)
    service.department_repo = mock_department_repo
    service.employee_repo = mock_employee_repo
    return service


class TestEmployeeServiceCreate:
    """Тесты метода EmployeeService.create_employee."""

    @pytest.mark.asyncio
    async def test_create_employee_success(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: успешное создание сотрудника."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)

        created_emp = create_mock_employee(id=1, department_id=1)
        mock_employee_repo.create = AsyncMock(return_value=created_emp)

        service = create_employee_service(mock_department_repo, mock_employee_repo)
        result = await service.create_employee(
            department_id=1,
            full_name="John Doe",
            position="Developer",
        )

        assert result.id == 1
        mock_department_repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_create_employee_department_not_found(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: создание с несуществующим департаментом."""
        mock_department_repo.get_by_id = AsyncMock(return_value=None)

        service = create_employee_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentNotFoundError) as exc_info:
            await service.create_employee(
                department_id=999,
                full_name="John Doe",
                position="Developer",
            )

        assert exc_info.value.status_code == 404
        mock_employee_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_employee_with_hired_at(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: создание сотрудника с hired_at датой."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)

        created_emp = create_mock_employee(id=1, department_id=1)
        mock_employee_repo.create = AsyncMock(return_value=created_emp)

        service = create_employee_service(mock_department_repo, mock_employee_repo)
        result = await service.create_employee(
            department_id=1,
            full_name="John Doe",
            position="Developer",
            hired_at="2024-01-15",
        )

        assert result.id == 1

    @pytest.mark.asyncio
    async def test_create_employee_without_hired_at(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: создание сотрудника без hired_at."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)

        created_emp = create_mock_employee(id=1, department_id=1)
        mock_employee_repo.create = AsyncMock(return_value=created_emp)

        service = create_employee_service(mock_department_repo, mock_employee_repo)
        result = await service.create_employee(
            department_id=1,
            full_name="John Doe",
            position="Developer",
            hired_at=None,
        )

        assert result.id == 1

    @pytest.mark.asyncio
    async def test_create_employee_invalid_date_format(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: создание с некорректным форматом даты."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)

        service = create_employee_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(InvalidDateError) as exc_info:
            await service.create_employee(
                department_id=1,
                full_name="John Doe",
                position="Developer",
                hired_at="invalid-date",
            )

        assert exc_info.value.status_code == 400
        mock_employee_repo.create.assert_not_called()
