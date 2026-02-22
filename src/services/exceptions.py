from http import HTTPStatus


class ServiceError(Exception):
    """Базовое исключение сервиса."""

    status_code: int = HTTPStatus.BAD_REQUEST
    code: str = "SERVICE_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class NotFoundError(ServiceError):
    """Ресурс не найден."""

    status_code: int = HTTPStatus.NOT_FOUND
    code: str = "NOT_FOUND"


class ValidationError(ServiceError):
    """Ошибка валидации."""

    status_code: int = HTTPStatus.BAD_REQUEST
    code: str = "VALIDATION_ERROR"


class ConflictError(ServiceError):
    """Конфликт (например, дубликат)."""

    status_code: int = HTTPStatus.CONFLICT
    code: str = "CONFLICT"


class InternalError(ServiceError):
    """Внутренняя ошибка сервиса."""

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"


class DepartmentNotFoundError(NotFoundError):
    """Подразделение не найдено."""

    code: str = "DEPARTMENT_NOT_FOUND"

    def __init__(self, department_id: int):
        super().__init__(f"Подразделение с ID {department_id} не найдено")


class DepartmentNameConflictError(ConflictError):
    """Подразделение с таким именем уже существует."""

    code: str = "DEPARTMENT_NAME_CONFLICT"

    def __init__(self, parent_id: int | None):
        parent_info = f"у родителя (ID: {parent_id})" if parent_id else "корневого уровня"
        super().__init__(f"Подразделение с таким именем уже существует {parent_info}")


class DepartmentCycleError(ValidationError):
    """Обнаружен цикл в дереве подразделений."""

    code: str = "DEPARTMENT_CYCLE_ERROR"

    def __init__(self):
        super().__init__("Нельзя создать цикл в дереве подразделений")


class EmployeeNotFoundError(NotFoundError):
    """Сотрудник не найден."""

    code: str = "EMPLOYEE_NOT_FOUND"

    def __init__(self, employee_id: int):
        super().__init__(f"Сотрудник с ID {employee_id} не найден")


class InvalidDateError(ValidationError):
    """Некорректный формат даты."""

    code: str = "INVALID_DATE_FORMAT"

    def __init__(self, field_name: str):
        super().__init__(f"Некорректный формат даты в поле '{field_name}'. Ожидается YYYY-MM-DD")


class ReassignTargetNotFoundError(NotFoundError):
    """Подразделение для перевода сотрудников не найдено."""

    code: str = "REASSIGN_TARGET_NOT_FOUND"

    def __init__(self, department_id: int):
        super().__init__(f"Подразделение для перевода (ID: {department_id}) не найдено")


class ReassignTargetRequiredError(ValidationError):
    """Не указано подразделение для перевода."""

    code: str = "REASSIGN_TARGET_REQUIRED"

    def __init__(self):
        super().__init__("reassign_to_department_id обязателен для режима reassign")
