from datetime import datetime, date

from pydantic import BaseModel, Field, field_validator


class DepartmentBase(BaseModel):
    """Базовая схема подразделения."""

    name: str = Field(..., min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def trim_name(cls, v: str) -> str:
        return v.strip()


class DepartmentCreate(DepartmentBase):
    """Схема для создания подразделения."""

    parent_id: int | None = None


class DepartmentUpdate(BaseModel):
    """Схема для обновления подразделения."""

    name: str | None = Field(None, min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip()
        return v


class DepartmentResponse(DepartmentBase):
    """Схема ответа подразделения."""

    id: int
    parent_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeResponse(BaseModel):
    """Схема ответа сотрудника (для вложенности)."""

    id: int
    full_name: str
    position: str
    hired_at: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DepartmentWithChildrenResponse(DepartmentResponse):
    """Схема подразделения с сотрудниками и дочерними подразделениями."""

    employees: list[EmployeeResponse] = Field(default_factory=list)
    children: list["DepartmentWithChildrenResponse"] = Field(default_factory=list)


DepartmentWithChildrenResponse.model_rebuild()
