import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, DBAPIError

from src.models.employee import Employee
from src.db.employee_repository import EmployeeRepository


class TestEmployeeConstraints:
    """Тесты ограничений на уровне БД."""

    async def test_full_name_not_null_constraint(
        self,
        db_session,
        employee_repo: EmployeeRepository,
    ):
        """Тест: full_name не может быть NULL."""
        with pytest.raises((IntegrityError, DBAPIError)):
            stmt = text(
                """
                INSERT INTO employees (department_id, full_name, position)
                VALUES (1, NULL, 'Developer')
            """
            )
            await db_session.execute(stmt)
            await db_session.commit()

    async def test_position_not_null_constraint(
        self,
        db_session,
        employee_repo: EmployeeRepository,
    ):
        """Тест: position не может быть NULL."""
        with pytest.raises((IntegrityError, DBAPIError)):
            stmt = text(
                """
                INSERT INTO employees (department_id, full_name, position)
                VALUES (1, 'John', NULL)
            """
            )
            await db_session.execute(stmt)
            await db_session.commit()

    async def test_department_id_foreign_key_constraint(
        self,
        db_session,
        employee_repo: EmployeeRepository,
    ):
        """Тест: department_id должен ссылаться на существующий департамент."""
        with pytest.raises((IntegrityError, DBAPIError)):
            stmt = text(
                """
                INSERT INTO employees (department_id, full_name, position)
                VALUES (99999, 'John', 'Developer')
            """
            )
            await db_session.execute(stmt)
            await db_session.commit()

    async def test_cascade_delete_on_department_delete(
        self,
        db_session,
        employee_repo: EmployeeRepository,
        department_repo,
        created_employee: Employee,
    ):
        """Тест: CASCADE удаление сотрудников при удалении департамента."""
        emp_id = created_employee.id
        dept = await department_repo.get_by_id(created_employee.department_id)

        await db_session.delete(dept)
        await db_session.commit()

        emp = await employee_repo.get_by_id(emp_id)
        assert emp is None


class TestEmployeePersistence:
    """Тесты корректного сохранения данных."""

    async def test_create_employee_persists_data(
        self,
        db_session,
        employee_repo: EmployeeRepository,
        created_department,
    ):
        """Тест: созданный сотрудник сохраняется в БД."""
        emp = await employee_repo.create(
            department_id=created_department.id,
            full_name="John Doe",
            position="Developer",
        )

        await db_session.refresh(emp)
        assert emp.id is not None
        assert emp.full_name == "John Doe"
        assert emp.position == "Developer"
        assert emp.department_id == created_department.id

    async def test_create_employee_with_hired_at(
        self,
        db_session,
        employee_repo: EmployeeRepository,
        created_department,
    ):
        """Тест: сотрудник с hired_at датой."""
        from datetime import date

        emp = await employee_repo.create(
            department_id=created_department.id,
            full_name="Jane Doe",
            position="Manager",
            hired_at=date(2024, 1, 15),
        )

        await db_session.refresh(emp)
        assert emp.hired_at is not None
        assert str(emp.hired_at) == "2024-01-15"

    async def test_create_employee_without_hired_at(
        self,
        db_session,
        employee_repo: EmployeeRepository,
        created_department,
    ):
        """Тест: сотрудник без hired_at (опциональное поле)."""
        emp = await employee_repo.create(
            department_id=created_department.id,
            full_name="Jane Doe",
            position="Manager",
            hired_at=None,
        )

        await db_session.refresh(emp)
        assert emp.hired_at is None

    async def test_employee_created_at_auto_generated(
        self,
        db_session,
        employee_repo: EmployeeRepository,
        created_department,
    ):
        """Тест: created_at генерируется автоматически."""
        emp = await employee_repo.create(
            department_id=created_department.id,
            full_name="Test",
            position="Test",
        )

        assert emp.created_at is not None


class TestEmployeeRepositoryQueries:
    """Тесты методов запросов репозитория."""

    async def test_get_by_id_existing(
        self,
        employee_repo: EmployeeRepository,
        created_employee: Employee,
    ):
        """Тест: получение существующего сотрудника по ID."""
        emp = await employee_repo.get_by_id(created_employee.id)

        assert emp is not None
        assert emp.id == created_employee.id
        assert emp.full_name == created_employee.full_name

    async def test_get_by_id_nonexistent(
        self,
        employee_repo: EmployeeRepository,
    ):
        """Тест: получение несуществующего сотрудника."""
        emp = await employee_repo.get_by_id(9999)

        assert emp is None

    async def test_get_by_department(
        self,
        employee_repo: EmployeeRepository,
        created_department,
        created_employee: Employee,
    ):
        """Тест: получение всех сотрудников департамента."""
        await employee_repo.create(
            department_id=created_department.id,
            full_name="Jane Doe",
            position="Manager",
        )

        employees = await employee_repo.get_by_department(created_department.id)

        assert len(employees) == 2

    async def test_update_department(
        self,
        db_session,
        employee_repo: EmployeeRepository,
        department_repo,
        created_employee: Employee,
    ):
        """Тест: перевод сотрудника в другой департамент."""
        new_dept = await department_repo.create(name="New Dept", parent_id=None)

        await employee_repo.update_department(
            employee_ids=[created_employee.id],
            new_department_id=new_dept.id,
        )

        await db_session.refresh(created_employee)
        assert created_employee.department_id == new_dept.id

    async def test_delete_employee(
        self,
        db_session,
        employee_repo: EmployeeRepository,
        created_employee: Employee,
    ):
        """Тест: удаление сотрудника."""
        emp_id = created_employee.id

        await employee_repo.delete(created_employee)
        await db_session.commit()

        emp = await employee_repo.get_by_id(emp_id)
        assert emp is None
