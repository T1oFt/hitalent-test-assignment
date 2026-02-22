from datetime import date

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Employee


class EmployeeRepository:
    """Репозиторий для сотрудников."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        department_id: int,
        full_name: str,
        position: str,
        hired_at: date | None = None,
    ) -> Employee:
        """Создать сотрудника."""
        employee = Employee(
            department_id=department_id,
            full_name=full_name,
            position=position,
            hired_at=hired_at,
        )
        self.db.add(employee)
        await self.db.commit()
        await self.db.refresh(employee)
        return employee

    async def get_by_id(self, id: int) -> Employee | None:
        """Получить сотрудника по ID."""
        stmt = select(Employee).where(Employee.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_department(self, department_id: int) -> list[Employee]:
        """Получить всех сотрудников подразделения."""
        stmt = (
            select(Employee)
            .where(Employee.department_id == department_id)
            .order_by(Employee.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_department(self, employee_ids: list[int], new_department_id: int) -> None:
        """Перевести сотрудников в другое подразделение."""
        stmt = (
            update(Employee)
            .where(Employee.id.in_(employee_ids))
            .values(department_id=new_department_id)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def delete(self, employee: Employee) -> None:
        """Удалить сотрудника."""
        await self.db.delete(employee)
        await self.db.commit()
