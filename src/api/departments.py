from fastapi import APIRouter, Query, status, Request
from fastapi.responses import JSONResponse

from src.api.decorators import etag_decorator
from src.dependencies import DepartmentServiceDep
from src.models import Department
from src.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentWithChildrenResponse,
)
from src.schemas.common import TransferMode

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    service: DepartmentServiceDep,
) -> Department:
    """Создать подразделение."""
    return await service.create_department(
        name=department_data.name,
        parent_id=department_data.parent_id,
    )


@router.get("/{department_id}")
@etag_decorator(max_age=5)
async def get_department(
    department_id: int,
    request: Request,
    service: DepartmentServiceDep,
    depth: int = Query(default=1, ge=1, le=5, description="Глубина вложенных подразделений"),
    include_employees: bool = Query(default=True, description="Включать сотрудников"),
) -> JSONResponse:
    """Получить подразделение с сотрудниками и поддерево."""
    raw_data = await service.get_department(
        id=department_id,
        depth=depth,
        include_employees=include_employees,
    )
    validated_data = DepartmentWithChildrenResponse.model_validate(raw_data)
    
    return JSONResponse(content=validated_data.model_dump(mode='json'))


@router.patch("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    service: DepartmentServiceDep,
) -> Department:
    """Обновить подразделение (переместить в другое или изменить имя)."""
    return await service.update_department(
        id=department_id,
        name=department_data.name,
        parent_id=department_data.parent_id,
    )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int,
    service: DepartmentServiceDep,
    mode: TransferMode = Query(default=TransferMode.cascade, description="Режим перевода"),
    reassign_to_department_id: int | None = Query(
        default=None,
        description="ID подразделения для перевода сотрудников (обязателен для mode=reassign)",
    ),
) -> None:
    """Удалить подразделение."""
    await service.delete_department(
        id=department_id,
        mode=mode,
        reassign_to_department_id=reassign_to_department_id,
    )
