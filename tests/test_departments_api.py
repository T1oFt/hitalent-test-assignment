import pytest
from datetime import datetime
from unittest.mock import AsyncMock, PropertyMock, patch

from src.services.exceptions import (
    DepartmentNotFoundError,
    DepartmentNameConflictError,
    DepartmentCycleError,
    ReassignTargetRequiredError,
    ReassignTargetNotFoundError,
)

from tests.conftest import create_mock_department


class TestCreateDepartmentAPI:
    """Тесты для POST /api/v1/departments/ эндпоинта."""

    @pytest.mark.asyncio
    async def test_create_department_success(
        self,
        client,
        mock_department_service: AsyncMock,
    ):
        """Тест: успешное создание департамента."""
        created = create_mock_department(id=1, name="Test", parent_id=None)
        created.created_at = datetime(2024, 1, 1, 0, 0, 0)
        mock_department_service.create_department = AsyncMock(return_value=created)

        with patch(
            "src.services.department_service.DepartmentService.create_department",
            return_value=created,
        ):
            response = await client.post(
                "/api/v1/departments/",
                json={"name": "Test", "parent_id": None},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test"

    @pytest.mark.asyncio
    async def test_create_department_empty_name_validation(
        self,
        client,
    ):
        """Тест: пустое имя отклоняется валидацией Pydantic."""
        response = await client.post(
            "/api/v1/departments/",
            json={"name": "", "parent_id": None},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_department_missing_name_validation(
        self,
        client,
    ):
        """Тест: отсутствие имени отклоняется."""
        response = await client.post(
            "/api/v1/departments/",
            json={"parent_id": None},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_department_name_too_long_validation(
        self,
        client,
    ):
        """Тест: имя > 200 символов отклоняется."""
        response = await client.post(
            "/api/v1/departments/",
            json={"name": "A" * 201, "parent_id": None},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_department_name_conflict_response(
        self,
        client,
    ):
        """Тест: 409 ответ при конфликте имён."""
        with patch(
            "src.services.department_service.DepartmentService.create_department",
            side_effect=DepartmentNameConflictError(parent_id=None),
        ):
            response = await client.post(
                "/api/v1/departments/",
                json={"name": "Existing", "parent_id": None},
            )

        assert response.status_code == 409
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_create_department_parent_not_found_response(
        self,
        client,
    ):
        """Тест: 404 ответ для несуществующего родителя."""
        with patch(
            "src.services.department_service.DepartmentService.create_department",
            side_effect=DepartmentNotFoundError(department_id=999),
        ):
            response = await client.post(
                "/api/v1/departments/",
                json={"name": "Child", "parent_id": 999},
            )

        assert response.status_code == 404


class TestGetDepartmentAPI:
    """Тесты для GET /api/v1/departments/{id} эндпоинта."""

    @pytest.mark.asyncio
    async def test_get_department_success(
        self,
        client,
    ):
        """Тест: успешное получение департамента."""
        tree_data = {
            "id": 1,
            "name": "Test",
            "parent_id": None,
            "created_at": "2024-01-01T00:00:00",
            "employees": [],
            "children": [],
        }

        with patch(
            "src.services.department_service.DepartmentService.get_department",
            return_value=tree_data,
        ):
            response = await client.get("/api/v1/departments/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "employees" in data
        assert "children" in data

    @pytest.mark.asyncio
    async def test_get_department_depth_validation_min(
        self,
        client,
    ):
        """Тест: depth < 1 отклоняется."""
        response = await client.get("/api/v1/departments/1?depth=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_department_depth_validation_max(
        self,
        client,
    ):
        """Тест: depth > 5 отклоняется."""
        response = await client.get("/api/v1/departments/1?depth=6")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_department_not_found_response(
        self,
        client,
    ):
        """Тест: 404 ответ для несуществующего департамента."""
        with patch(
            "src.services.department_service.DepartmentService.get_department",
            side_effect=DepartmentNotFoundError(department_id=999),
        ):
            response = await client.get("/api/v1/departments/999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_department_with_params(
        self,
        client,
    ):
        """Тест: параметры depth и include_employees передаются."""
        tree_data = {
            "id": 1,
            "name": "Test",
            "parent_id": None,
            "created_at": "2024-01-01T00:00:00",
            "employees": [],
            "children": [],
        }

        mock_method = AsyncMock(return_value=tree_data)
        with patch(
            "src.services.department_service.DepartmentService.get_department",
            mock_method,
        ):
            await client.get("/api/v1/departments/1?depth=3&include_employees=false")

        mock_method.assert_called_with(
            id=1,
            depth=3,
            include_employees=False,
        )


class TestUpdateDepartmentAPI:
    """Тесты для PATCH /api/v1/departments/{id} эндпоинта."""

    @pytest.mark.asyncio
    async def test_update_department_name_success(
        self,
        client,
    ):
        """Тест: успешное обновление имени."""
        updated = create_mock_department(id=1, name="New Name", parent_id=None)
        updated.created_at = datetime(2024, 1, 1, 0, 0, 0)

        with patch(
            "src.services.department_service.DepartmentService.update_department",
            return_value=updated,
        ):
            response = await client.patch(
                "/api/v1/departments/1",
                json={"name": "New Name"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_department_cycle_error_response(
        self,
        client,
    ):
        """Тест: 400 ответ при обнаружении цикла."""
        with patch(
            "src.services.department_service.DepartmentService.update_department",
            side_effect=DepartmentCycleError(),
        ):
            response = await client.patch(
                "/api/v1/departments/1",
                json={"parent_id": 5},
            )

        assert response.status_code == 400
        assert "message" in response.json()

    @pytest.mark.asyncio
    async def test_update_department_name_conflict_response(
        self,
        client,
    ):
        """Тест: 409 ответ при конфликте имён."""
        with patch(
            "src.services.department_service.DepartmentService.update_department",
            side_effect=DepartmentNameConflictError(parent_id=None),
        ):
            response = await client.patch(
                "/api/v1/departments/1",
                json={"name": "Conflicting"},
            )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_department_not_found_response(
        self,
        client,
    ):
        """Тест: 404 ответ для несуществующего департамента."""
        with patch(
            "src.services.department_service.DepartmentService.update_department",
            side_effect=DepartmentNotFoundError(department_id=999),
        ):
            response = await client.patch(
                "/api/v1/departments/999",
                json={"name": "New"},
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_department_empty_name_validation(
        self,
        client,
    ):
        """Тест: пустое имя отклоняется."""
        response = await client.patch(
            "/api/v1/departments/1",
            json={"name": ""},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_department_empty_body(
        self,
        client,
    ):
        """Тест: пустое тело разрешено (без изменений)."""
        updated = create_mock_department(id=1, name="Test", parent_id=None)
        updated.created_at = datetime(2024, 1, 1, 0, 0, 0)

        with patch(
            "src.services.department_service.DepartmentService.update_department",
            return_value=updated,
        ):
            response = await client.patch("/api/v1/departments/1", json={})

        assert response.status_code == 200


class TestDeleteDepartmentAPI:
    """Тесты для DELETE /api/v1/departments/{id} эндпоинта."""

    @pytest.mark.asyncio
    async def test_delete_department_cascade_mode(
        self,
        client,
    ):
        """Тест: cascade удаление возвращает 204."""
        with patch(
            "src.services.department_service.DepartmentService.delete_department",
            return_value=True,
        ):
            response = await client.delete("/api/v1/departments/1")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_department_reassign_mode(
        self,
        client,
    ):
        """Тест: reassign удаление с target."""
        with patch(
            "src.services.department_service.DepartmentService.delete_department",
            return_value=True,
        ):
            response = await client.delete(
                "/api/v1/departments/1?mode=reassign&reassign_to_department_id=2"
            )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_department_not_found_response(
        self,
        client,
    ):
        """Тест: 404 ответ для несуществующего департамента."""
        with patch(
            "src.services.department_service.DepartmentService.delete_department",
            side_effect=DepartmentNotFoundError(department_id=999),
        ):
            response = await client.delete("/api/v1/departments/999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_department_reassign_missing_target_response(
        self,
        client,
    ):
        """Тест: 400 когда reassign_to_department_id отсутствует."""
        with patch(
            "src.services.department_service.DepartmentService.delete_department",
            side_effect=ReassignTargetRequiredError(),
        ):
            response = await client.delete("/api/v1/departments/1?mode=reassign")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_department_reassign_target_not_found_response(
        self,
        client,
    ):
        """Тест: 404 когда target для reassign не существует."""
        with patch(
            "src.services.department_service.DepartmentService.delete_department",
            side_effect=ReassignTargetNotFoundError(department_id=999),
        ):
            response = await client.delete(
                "/api/v1/departments/1?mode=reassign&reassign_to_department_id=999"
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_department_invalid_mode_validation(
        self,
        client,
    ):
        """Тест: невалидный mode отклоняется."""
        response = await client.delete("/api/v1/departments/1?mode=invalid")

        assert response.status_code == 422
