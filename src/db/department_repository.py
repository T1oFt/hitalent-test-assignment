from collections import defaultdict
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import Department, Employee


class DepartmentRepository:
    """Репозиторий для подразделений."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str, parent_id: int | None = None) -> Department:
        """Создать подразделение."""
        department = Department(name=name, parent_id=parent_id)
        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def get_by_id(self, id: int) -> Department | None:
        """Получить подразделение по ID."""
        stmt = select(Department).where(Department.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name_and_parent(self, name: str, parent_id: int | None) -> Department | None:
        """Проверить существование подразделения с таким именем у того же родителя."""
        stmt = select(Department).where(Department.name == name)
        if parent_id is None:
            stmt = stmt.where(Department.parent_id.is_(None))
        else:
            stmt = stmt.where(Department.parent_id == parent_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_employees(self, id: int) -> Department | None:
        """Получить подразделение с сотрудниками."""
        stmt = (
            select(Department)
            .options(selectinload(Department.employees))
            .where(Department.id == id)
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_children(self, parent_id: int | None) -> list[Department]:
        """Получить дочерние подразделения."""
        stmt = select(Department)
        if parent_id is None:
            stmt = stmt.where(Department.parent_id.is_(None))
        else:
            stmt = stmt.where(Department.parent_id == parent_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_descendants_ids(self, id: int) -> list[int]:
        """Получить IDs всех дочерних подразделений (рекурсивно)."""
        result = []
        children = await self.get_children(id)
        for child in children:
            result.append(child.id)
            result.extend(await self.get_descendants_ids(child.id))
        return result

    async def has_cycle(self, id: int, new_parent_id: int | None) -> bool:
        """Проверить, создаст ли новый родитель цикл."""
        if new_parent_id is None:
            return False
        if new_parent_id == id:
            return True
        stmt = select(Department).where(Department.id == new_parent_id)
        result = await self.db.execute(stmt)
        current = result.scalar_one_or_none()
        while current:
            if current.id == id:
                return True
            if current.parent_id is None:
                break
            stmt = select(Department).where(Department.id == current.parent_id)
            result = await self.db.execute(stmt)
            current = result.scalar_one_or_none()
        return False

    async def update(self, department: Department, name: str | None = None, parent_id: int | None = None) -> Department:
        """Обновить подразделение."""
        if name is not None:
            department.name = name
        if parent_id is not None:
            department.parent_id = parent_id
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def reassign_parent(self, department_ids: list[int], new_parent_id: int | None) -> None:
        """Переназначить родительское подразделение для нескольких департаментов."""
        if not department_ids:
            return
        stmt = (
            update(Department)
            .where(Department.id.in_(department_ids))
            .values(parent_id=new_parent_id)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def delete(self, department: Department) -> None:
        """Удалить подразделение."""
        await self.db.delete(department)
        await self.db.commit()

    async def get_all_employees_ids(self, department_ids: list[int]) -> list[int]:
        """Получить IDs всех сотрудников в подразделениях."""
        if not department_ids:
            return []
        stmt = select(Employee.id).where(Employee.department_id.in_(department_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_tree_data_flat(
        self,
        root_id: int,
        max_depth: int,
        include_employees: bool,
    ) -> tuple[Department | None, list[Department]]:
        """
        Загружает корень и всех потомков до max_depth одним запросом.
        Возвращает (корень, список_всех_отделов_с_сотрудниками).
        """
        ids_to_load = {root_id}
        current_level_ids = {root_id}

        for _ in range(max_depth):
            if not current_level_ids:
                break
            stmt = select(Department.id).where(Department.parent_id.in_(current_level_ids))
            res = await self.db.execute(stmt)
            next_level_ids = set(res.scalars().all())
            if not next_level_ids:
                break
            ids_to_load.update(next_level_ids)
            current_level_ids = next_level_ids

        if not ids_to_load:
            return None, []

        stmt = select(Department).where(Department.id.in_(ids_to_load))
        if include_employees:
            stmt = stmt.options(selectinload(Department.employees))

        result = await self.db.execute(stmt)
        all_depts = list(result.scalars().unique().all())

        root = next((d for d in all_depts if d.id == root_id), None)
        return root, all_depts

    async def get_with_children_tree(
        self,
        id: int,
        depth: int = 1,
        include_employees: bool = True,
    ) -> dict[str, Any] | None:
        """Получить подразделение с сотрудниками и дочерними подразделениями."""
        root, all_depts = await self.get_tree_data_flat(
            root_id=id,
            max_depth=depth,
            include_employees=include_employees,
        )

        if not root:
            return None

        children_map: dict[int, list[Department]] = defaultdict(list)

        for dept in all_depts:
            if dept.parent_id is not None:
                children_map[dept.parent_id].append(dept)

        def build_tree_dict(dept: Department) -> dict[str, Any]:
            employees_data: list[dict[str, Any]] = []
            if include_employees:
                sorted_emps = sorted(dept.employees, key=lambda e: e.created_at)
                employees_data = [
                    {
                        "id": emp.id,
                        "full_name": emp.full_name,
                        "position": emp.position,
                        "hired_at": emp.hired_at,
                        "created_at": emp.created_at,
                    }
                    for emp in sorted_emps
                ]

            raw_children = children_map.get(dept.id, [])
            children_data = [
                build_tree_dict(child)
                for child in sorted(raw_children, key=lambda x: x.id)
            ]

            result: dict[str, Any] = {
                "id": dept.id,
                "name": dept.name,
                "parent_id": dept.parent_id,
                "created_at": dept.created_at,
            }

            result["employees"] = employees_data if include_employees else []

            result["children"] = children_data if children_data else []

            return result

        return build_tree_dict(root)
