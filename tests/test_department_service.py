import pytest
from unittest.mock import AsyncMock

from src.services.department_service import DepartmentService
from src.services.employee_service import EmployeeService
from src.services.exceptions import (
    DepartmentNotFoundError,
    DepartmentNameConflictError,
    DepartmentCycleError,
    InvalidDateError,
    ReassignTargetRequiredError,
    ReassignTargetNotFoundError,
)
from src.schemas.common import TransferMode
from src.db.department_repository import DepartmentRepository
from src.db.employee_repository import EmployeeRepository

from tests.conftest import create_mock_department, create_mock_employee


def create_department_service(
    mock_department_repo: AsyncMock,
    mock_employee_repo: AsyncMock,
) -> DepartmentService:
    """Создание сервиса департаментов с мокированными репозиториями."""
    service = DepartmentService.__new__(DepartmentService)
    service.department_repo = mock_department_repo
    service.employee_repo = mock_employee_repo
    return service


class TestDepartmentServiceCreate:
    """Тесты метода DepartmentService.create_department."""

    @pytest.mark.asyncio
    async def test_create_department_success(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: успешное создание департамента."""
        mock_department_repo.get_by_name_and_parent = AsyncMock(return_value=None)

        created_dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.create = AsyncMock(return_value=created_dept)

        service = create_department_service(mock_department_repo, mock_employee_repo)
        result = await service.create_department(name="Test", parent_id=None)

        assert result.id == 1
        mock_department_repo.get_by_name_and_parent.assert_called_once_with("Test", None)
        mock_department_repo.create.assert_called_once_with(name="Test", parent_id=None)

    @pytest.mark.asyncio
    async def test_create_department_name_conflict(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: создание департамента с конфликтом имён."""
        existing = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_name_and_parent = AsyncMock(return_value=existing)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentNameConflictError) as exc_info:
            await service.create_department(name="Test", parent_id=None)

        assert exc_info.value.status_code == 409
        mock_department_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_department_parent_not_found(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: создание департамента с несуществующим родителем."""
        mock_department_repo.get_by_name_and_parent = AsyncMock(return_value=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=None)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentNotFoundError) as exc_info:
            await service.create_department(name="Child", parent_id=999)

        assert exc_info.value.status_code == 404
        mock_department_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_department_with_parent_success(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: успешное создание с валидным родителем."""
        mock_department_repo.get_by_name_and_parent = AsyncMock(return_value=None)

        parent = create_mock_department(id=1, name="Parent", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=parent)

        created = create_mock_department(id=2, name="Child", parent_id=1)
        mock_department_repo.create = AsyncMock(return_value=created)

        service = create_department_service(mock_department_repo, mock_employee_repo)
        result = await service.create_department(name="Child", parent_id=1)

        assert result.id == 2
        assert result.parent_id == 1


class TestDepartmentServiceGet:
    """Тесты метода DepartmentService.get_department."""

    @pytest.mark.asyncio
    async def test_get_department_success(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: успешное получение департамента с деревом."""
        tree_data = {
            "id": 1,
            "name": "Test",
            "parent_id": None,
            "created_at": "2024-01-01T00:00:00",
            "employees": [],
            "children": [],
        }
        mock_department_repo.get_with_children_tree = AsyncMock(return_value=tree_data)

        service = create_department_service(mock_department_repo, mock_employee_repo)
        result = await service.get_department(id=1, depth=1, include_employees=True)

        assert result == tree_data
        mock_department_repo.get_with_children_tree.assert_called_once_with(
            1, depth=1, include_employees=True
        )

    @pytest.mark.asyncio
    async def test_get_department_not_found(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: получение несуществующего департамента."""
        mock_department_repo.get_with_children_tree = AsyncMock(return_value=None)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentNotFoundError) as exc_info:
            await service.get_department(id=999)

        assert exc_info.value.status_code == 404


class TestDepartmentServiceUpdate:
    """Тесты метода DepartmentService.update_department."""

    @pytest.mark.asyncio
    async def test_update_department_cycle_self_reference(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: установка parent_id в свой ID вызывает ошибку цикла."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)
        mock_department_repo.has_cycle = AsyncMock(return_value=True)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentCycleError) as exc_info:
            await service.update_department(id=1, parent_id=1)

        assert exc_info.value.status_code == 400
        mock_department_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_department_cycle_in_tree(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: перемещение департамента в поддеревом вызывает ошибку цикла."""
        dept = create_mock_department(id=1, name="Root", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)
        mock_department_repo.has_cycle = AsyncMock(return_value=True)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentCycleError):
            await service.update_department(id=1, parent_id=5)

        mock_department_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_department_name_conflict(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: дубликат имени под тем же родителем вызывает ошибку конфликта."""
        dept = create_mock_department(id=1, name="Old", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)
        mock_department_repo.has_cycle = AsyncMock(return_value=False)

        existing = create_mock_department(id=2, name="New", parent_id=None)
        mock_department_repo.get_by_name_and_parent = AsyncMock(return_value=existing)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentNameConflictError) as exc_info:
            await service.update_department(id=1, name="New")

        assert exc_info.value.status_code == 409
        mock_department_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_department_not_found(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: обновление несуществующего департамента."""
        mock_department_repo.get_by_id = AsyncMock(return_value=None)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentNotFoundError) as exc_info:
            await service.update_department(id=999, name="New")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_department_no_changes(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: обновление не выполняется, если ничего не изменилось."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)

        service = create_department_service(mock_department_repo, mock_employee_repo)
        result = await service.update_department(id=1, name="Test", parent_id=None)

        assert result == dept
        mock_department_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_department_success(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: успешное обновление."""
        dept = create_mock_department(id=1, name="Old", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)
        mock_department_repo.has_cycle = AsyncMock(return_value=False)
        mock_department_repo.get_by_name_and_parent = AsyncMock(return_value=None)

        updated = create_mock_department(id=1, name="New", parent_id=2)
        mock_department_repo.update = AsyncMock(return_value=updated)

        service = create_department_service(mock_department_repo, mock_employee_repo)
        result = await service.update_department(id=1, name="New", parent_id=2)

        assert result.id == 1
        assert result.parent_id == 2


class TestDepartmentServiceDelete:
    """Тесты метода DepartmentService.delete_department."""

    @pytest.mark.asyncio
    async def test_delete_department_cascade_mode(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: cascade удаление удаляет департамент."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)
        mock_department_repo.delete = AsyncMock(return_value=None)

        service = create_department_service(mock_department_repo, mock_employee_repo)
        result = await service.delete_department(id=1, mode=TransferMode.cascade)

        assert result is True
        mock_department_repo.delete.assert_called_once_with(dept)

    @pytest.mark.asyncio
    async def test_delete_department_reassign_target_required(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: режим reassign без target вызывает ошибку."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(return_value=dept)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(ReassignTargetRequiredError) as exc_info:
            await service.delete_department(
                id=1,
                mode=TransferMode.reassign,
                reassign_to_department_id=None,
            )

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_department_reassign_target_not_found(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: режим reassign с несуществующим target."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(side_effect=[dept, None])

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(ReassignTargetNotFoundError) as exc_info:
            await service.delete_department(
                id=1,
                mode=TransferMode.reassign,
                reassign_to_department_id=999,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_department_reassign_success(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: успешное reassign удаление."""
        dept = create_mock_department(id=1, name="Test", parent_id=None)
        target = create_mock_department(id=2, name="Target", parent_id=None)
        mock_department_repo.get_by_id = AsyncMock(side_effect=[dept, target])

        mock_department_repo.get_all_employees_ids = AsyncMock(return_value=[1, 2])
        mock_department_repo.get_children = AsyncMock(return_value=[])
        mock_department_repo.delete = AsyncMock(return_value=None)

        service = create_department_service(mock_department_repo, mock_employee_repo)
        result = await service.delete_department(
            id=1,
            mode=TransferMode.reassign,
            reassign_to_department_id=2,
        )

        assert result is True
        mock_employee_repo.update_department.assert_called_once_with([1, 2], 2)

    @pytest.mark.asyncio
    async def test_delete_department_reassign_with_children(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: reassign перемещает детей к грандпаренту."""
        dept = create_mock_department(id=1, name="Test", parent_id=10)
        target = create_mock_department(id=2, name="Target", parent_id=None)
        child = create_mock_department(id=3, name="Child", parent_id=1)

        mock_department_repo.get_by_id = AsyncMock(side_effect=[dept, target])
        mock_department_repo.get_all_employees_ids = AsyncMock(return_value=[])
        mock_department_repo.get_children = AsyncMock(return_value=[child])
        mock_department_repo.reassign_parent = AsyncMock(return_value=None)
        mock_department_repo.delete = AsyncMock(return_value=None)

        service = create_department_service(mock_department_repo, mock_employee_repo)
        result = await service.delete_department(
            id=1,
            mode=TransferMode.reassign,
            reassign_to_department_id=2,
        )

        assert result is True
        mock_department_repo.reassign_parent.assert_called_once_with([3], 10)

    @pytest.mark.asyncio
    async def test_delete_department_not_found(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ):
        """Тест: удаление несуществующего департамента."""
        mock_department_repo.get_by_id = AsyncMock(return_value=None)

        service = create_department_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(DepartmentNotFoundError) as exc_info:
            await service.delete_department(id=999)

        assert exc_info.value.status_code == 404


class TestEmployeeServiceCreate:
    """Тесты метода EmployeeService.create_employee."""

    def create_employee_service(
        self,
        mock_department_repo: AsyncMock,
        mock_employee_repo: AsyncMock,
    ) -> EmployeeService:
        """Создание сервиса сотрудников с мокированными репозиториями."""
        service = EmployeeService.__new__(EmployeeService)
        service.department_repo = mock_department_repo
        service.employee_repo = mock_employee_repo
        return service

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

        service = self.create_employee_service(mock_department_repo, mock_employee_repo)
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

        service = self.create_employee_service(mock_department_repo, mock_employee_repo)

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

        service = self.create_employee_service(mock_department_repo, mock_employee_repo)
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

        service = self.create_employee_service(mock_department_repo, mock_employee_repo)
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

        service = self.create_employee_service(mock_department_repo, mock_employee_repo)

        with pytest.raises(InvalidDateError) as exc_info:
            await service.create_employee(
                department_id=1,
                full_name="John Doe",
                position="Developer",
                hired_at="invalid-date",
            )

        assert exc_info.value.status_code == 400
        mock_employee_repo.create.assert_not_called()
