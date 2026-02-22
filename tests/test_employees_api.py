import pytest
from datetime import datetime
from unittest.mock import patch

from src.services.exceptions import DepartmentNotFoundError, InvalidDateError

from tests.conftest import create_mock_employee


class TestCreateEmployeeAPI:
    """Тесты для POST /api/v1/departments/{id}/employees/ эндпоинта."""

    @pytest.mark.asyncio
    async def test_create_employee_success(
        self,
        client,
    ):
        """Тест: успешное создание сотрудника."""
        created = create_mock_employee(id=1, department_id=1)
        created.hired_at = None
        created.created_at = datetime(2024, 1, 1, 0, 0, 0)

        with patch(
            "src.services.employee_service.EmployeeService.create_employee",
            return_value=created,
        ):
            response = await client.post(
                "/api/v1/departments/1/employees/",
                json={"full_name": "John Doe", "position": "Developer"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["full_name"] == "John Doe"
        assert data["department_id"] == 1

    @pytest.mark.asyncio
    async def test_create_employee_empty_name_validation(
        self,
        client,
    ):
        """Тест: пустое full_name отклоняется."""
        response = await client.post(
            "/api/v1/departments/1/employees/",
            json={"full_name": "", "position": "Developer"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_employee_empty_position_validation(
        self,
        client,
    ):
        """Тест: пустая позиция отклоняется."""
        response = await client.post(
            "/api/v1/departments/1/employees/",
            json={"full_name": "John Doe", "position": ""},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_employee_missing_fields_validation(
        self,
        client,
    ):
        """Тест: отсутствие обязательных полей отклоняется."""
        response = await client.post(
            "/api/v1/departments/1/employees/",
            json={},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_employee_name_too_long_validation(
        self,
        client,
    ):
        """Тест: full_name > 200 символов отклоняется."""
        response = await client.post(
            "/api/v1/departments/1/employees/",
            json={"full_name": "A" * 201, "position": "Developer"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_employee_position_too_long_validation(
        self,
        client,
    ):
        """Тест: позиция > 200 символов отклоняется."""
        response = await client.post(
            "/api/v1/departments/1/employees/",
            json={"full_name": "John", "position": "B" * 201},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_employee_department_not_found_response(
        self,
        client,
    ):
        """Тест: 404 ответ для несуществующего департамента."""
        with patch(
            "src.services.employee_service.EmployeeService.create_employee",
            side_effect=DepartmentNotFoundError(department_id=999),
        ):
            response = await client.post(
                "/api/v1/departments/999/employees/",
                json={"full_name": "John", "position": "Dev"},
            )

        assert response.status_code == 404
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_create_employee_with_hired_at(
        self,
        client,
    ):
        """Тест: создание сотрудника с hired_at датой."""
        created = create_mock_employee(id=1, department_id=1)
        created.hired_at = "2024-01-15"
        created.created_at = datetime(2024, 1, 1, 0, 0, 0)

        with patch(
            "src.services.employee_service.EmployeeService.create_employee",
            return_value=created,
        ):
            response = await client.post(
                "/api/v1/departments/1/employees/",
                json={
                    "full_name": "John Doe",
                    "position": "Developer",
                    "hired_at": "2024-01-15",
                },
            )

        assert response.status_code == 201
