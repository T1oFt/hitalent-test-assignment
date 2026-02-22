import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, DBAPIError

from src.models.department import Department
from src.models.employee import Employee
from src.db.department_repository import DepartmentRepository
from src.db.employee_repository import EmployeeRepository


class TestDepartmentConstraints:
    """Тесты ограничений на уровне БД."""

    async def test_name_not_null_constraint(
        self,
        db_session,
        department_repo: DepartmentRepository,
    ):
        """Тест: name не может быть NULL."""
        with pytest.raises((IntegrityError, DBAPIError)):
            stmt = text(
                """
                INSERT INTO departments (name, parent_id)
                VALUES (NULL, NULL)
            """
            )
            await db_session.execute(stmt)
            await db_session.commit()

    async def test_name_length_constraint(
        self,
        db_session,
        department_repo: DepartmentRepository,
    ):
        """Тест: длина name ограничена 200 символами."""
        long_name = "A" * 201
        with pytest.raises((IntegrityError, DBAPIError)):
            stmt = text(
                """
                INSERT INTO departments (name, parent_id)
                VALUES (:name, NULL)
            """
            )
            await db_session.execute(stmt, {"name": long_name})
            await db_session.commit()

    async def test_parent_id_foreign_key_constraint(
        self,
        db_session,
        department_repo: DepartmentRepository,
    ):
        """Тест: parent_id должен ссылаться на существующий департамент."""
        with pytest.raises((IntegrityError, DBAPIError)):
            stmt = text(
                """
                INSERT INTO departments (name, parent_id)
                VALUES ('Test', 99999)
            """
            )
            await db_session.execute(stmt)
            await db_session.commit()

    async def test_cascade_delete_children(
        self,
        db_session,
        department_repo: DepartmentRepository,
        department_tree: dict,
    ):
        """Тест: CASCADE удаление дочерних департаментов."""
        root_id = department_tree["root"].id
        child1_id = department_tree["child1"].id

        root = await department_repo.get_by_id(root_id)
        await db_session.delete(root)
        await db_session.commit()

        child1 = await department_repo.get_by_id(child1_id)
        assert child1 is None

    async def test_cascade_delete_employees(
        self,
        db_session,
        department_repo: DepartmentRepository,
        employee_repo: EmployeeRepository,
        created_department: Department,
        created_employee: Employee,
    ):
        """Тест: CASCADE удаление сотрудников при удалении департамента."""
        emp_id = created_employee.id

        await db_session.delete(created_department)
        await db_session.commit()

        emp = await employee_repo.get_by_id(emp_id)
        assert emp is None


class TestDepartmentPersistence:
    """Тесты корректного сохранения данных."""

    async def test_create_department_persists_data(
        self,
        db_session,
        department_repo: DepartmentRepository,
    ):
        """Тест: созданный департамент сохраняется в БД."""
        dept = await department_repo.create(name="Persistent Dept", parent_id=None)

        await db_session.refresh(dept)
        assert dept.id is not None
        assert dept.name == "Persistent Dept"
        assert dept.parent_id is None

    async def test_create_department_with_parent_persists(
        self,
        db_session,
        department_repo: DepartmentRepository,
        created_department: Department,
    ):
        """Тест: дочерний департамент сохраняется корректно."""
        child = await department_repo.create(
            name="Child Dept",
            parent_id=created_department.id,
        )

        await db_session.refresh(child)
        assert child.parent_id == created_department.id

    async def test_update_department_persists_changes(
        self,
        db_session,
        department_repo: DepartmentRepository,
        created_department: Department,
    ):
        """Тест: обновления сохраняются в БД."""
        updated = await department_repo.update(
            created_department,
            name="New Name",
            parent_id=None,
        )

        await db_session.refresh(updated)
        assert updated.name == "New Name"

    async def test_department_created_at_auto_generated(
        self,
        db_session,
        department_repo: DepartmentRepository,
    ):
        """Тест: created_at генерируется автоматически."""
        dept = await department_repo.create(name="Auto Timestamp", parent_id=None)

        assert dept.created_at is not None


class TestDepartmentRepositoryQueries:
    """Тесты методов запросов репозитория."""

    async def test_get_by_name_and_parent_same_name_different_parent(
        self,
        department_repo: DepartmentRepository,
        department_tree: dict,
    ):
        """Тест: проверка уникальности имени только в пределах одного родителя."""
        child1 = department_tree["child1"]
        child2 = department_tree["child2"]

        await department_repo.create(
            name="Same Name",
            parent_id=child1.id,
        )

        result = await department_repo.get_by_name_and_parent(
            name="Same Name",
            parent_id=child2.id,
        )
        assert result is None

    async def test_get_by_name_and_parent_same_name_same_parent(
        self,
        department_repo: DepartmentRepository,
        department_tree: dict,
    ):
        """Тест: дубликат имени под тем же родителем находится."""
        child1 = department_tree["child1"]

        await department_repo.create(
            name="Duplicate Name",
            parent_id=child1.id,
        )

        result = await department_repo.get_by_name_and_parent(
            name="Duplicate Name",
            parent_id=child1.id,
        )
        assert result is not None

    async def test_has_cycle_self_reference(
        self,
        department_repo: DepartmentRepository,
        created_department: Department,
    ):
        """Тест: обнаружение цикла при self-reference (свой ID как родитель)."""
        has_cycle = await department_repo.has_cycle(
            created_department.id,
            created_department.id,
        )
        assert has_cycle is True

    async def test_has_cycle_in_tree(
        self,
        department_repo: DepartmentRepository,
        department_tree: dict,
    ):
        """Тест: обнаружение цикла при перемещении родителя в поддеревом."""
        root = department_tree["root"]
        grandchild = department_tree["grandchild"]

        has_cycle = await department_repo.has_cycle(root.id, grandchild.id)
        assert has_cycle is True

    async def test_has_cycle_no_cycle_valid_move(
        self,
        department_repo: DepartmentRepository,
        department_tree: dict,
    ):
        """Тест: нет цикла при валидном изменении родителя."""
        child1 = department_tree["child1"]
        child2 = department_tree["child2"]

        has_cycle = await department_repo.has_cycle(child2.id, child1.id)
        assert has_cycle is False

    async def test_get_descendants_ids_recursive(
        self,
        department_repo: DepartmentRepository,
        department_tree: dict,
    ):
        """Тест: get_descendants_ids возвращает всех вложенных потомков."""
        root = department_tree["root"]

        descendants = await department_repo.get_descendants_ids(root.id)

        assert len(descendants) == 3
        assert department_tree["child1"].id in descendants
        assert department_tree["child2"].id in descendants
        assert department_tree["grandchild"].id in descendants

    async def test_get_tree_data_flat_builds_hierarchy(
        self,
        department_repo: DepartmentRepository,
        department_tree: dict,
    ):
        """Тест: данные дерева загружаются корректно."""
        root = department_tree["root"]

        tree_dict = await department_repo.get_with_children_tree(
            root.id,
            depth=2,
            include_employees=False,
        )

        assert tree_dict is not None
        assert tree_dict["id"] == root.id
        assert len(tree_dict["children"]) == 2
