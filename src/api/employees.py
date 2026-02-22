from fastapi import APIRouter, status

from src.dependencies import EmployeeServiceDep
from src.models import Employee
from src.schemas.employee import EmployeeCreate, EmployeeResponse

router = APIRouter(prefix="/departments/{department_id}/employees", tags=["employees"])


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    department_id: int,
    employee_data: EmployeeCreate,
    service: EmployeeServiceDep,
) -> Employee:
    """Создать сотрудника в подразделении."""
    return await service.create_employee(
        department_id=department_id,
        full_name=employee_data.full_name,
        position=employee_data.position,
        hired_at=employee_data.hired_at.isoformat() if employee_data.hired_at else None,
    )
