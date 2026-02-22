from datetime import datetime, date
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Date, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.base import Base, AsyncAttrs

if TYPE_CHECKING:
    from src.models.department import Department


class Employee(AsyncAttrs, Base):
    """Сотрудник организации."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    hired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    department: Mapped["Department"] = relationship("Department", back_populates="employees")
