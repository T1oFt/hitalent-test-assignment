from datetime import datetime, date

from pydantic import BaseModel, Field, field_validator


class EmployeeBase(BaseModel):
    """Базовая схема сотрудника."""

    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)

    @field_validator("full_name", "position")
    @classmethod
    def trim_strings(cls, v: str) -> str:
        return v.strip()


class EmployeeCreate(EmployeeBase):
    """Схема для создания сотрудника."""

    hired_at: date | None = None


class EmployeeResponse(EmployeeBase):
    """Схема ответа сотрудника."""

    id: int
    department_id: int
    hired_at: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
