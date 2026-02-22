import asyncio
from typing import Any, AsyncGenerator, Generator
from datetime import date
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.db.base import Base, AsyncSessionLocal
from src.db.department_repository import DepartmentRepository
from src.db.employee_repository import EmployeeRepository
from src.main import app
from src.models.department import Department
from src.models.employee import Employee
from src.services.department_service import DepartmentService
from src.services.employee_service import EmployeeService
from src.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with dependency overrides."""
    from src.dependencies import get_db, get_department_service, get_employee_service

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_department_service() -> DepartmentService:
        return DepartmentService(
            department_repo=DepartmentRepository(db_session),
            employee_repo=EmployeeRepository(db_session),
        )

    async def override_get_employee_service() -> EmployeeService:
        return EmployeeService(
            department_repo=DepartmentRepository(db_session),
            employee_repo=EmployeeRepository(db_session),
        )

    app.dependency_overrides = {
        get_db: override_get_db,
        get_department_service: override_get_department_service,
        get_employee_service: override_get_employee_service,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides = {}


@pytest_asyncio.fixture
async def department_repo(db_session: AsyncSession) -> DepartmentRepository:
    """Create department repository fixture."""
    return DepartmentRepository(db_session)


@pytest_asyncio.fixture
async def employee_repo(db_session: AsyncSession) -> EmployeeRepository:
    """Create employee repository fixture."""
    return EmployeeRepository(db_session)


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create mock database session."""
    mock = AsyncMock(spec=AsyncSession)
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.delete = AsyncMock()
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def mock_department_repo() -> AsyncMock:
    """Create mock department repository."""
    mock = AsyncMock(spec=DepartmentRepository)
    return mock


@pytest.fixture
def mock_employee_repo() -> AsyncMock:
    """Create mock employee repository."""
    mock = AsyncMock(spec=EmployeeRepository)
    return mock


@pytest.fixture
def mock_department_service() -> AsyncMock:
    """Create mock department service."""
    mock = AsyncMock(spec=DepartmentService)
    return mock


@pytest.fixture
def mock_employee_service() -> AsyncMock:
    """Create mock employee service."""
    mock = AsyncMock(spec=EmployeeService)
    return mock


@pytest.fixture
def department_create_data() -> dict[str, Any]:
    """Department creation test data."""
    return {
        "name": "Test Department",
        "parent_id": None,
    }


@pytest.fixture
def department_update_data() -> dict[str, Any]:
    """Department update test data."""
    return {
        "name": "Updated Department",
    }


@pytest.fixture
def employee_create_data() -> dict[str, Any]:
    """Employee creation test data."""
    return {
        "full_name": "John Doe",
        "position": "Software Engineer",
        "hired_at": "2024-01-15",
    }


@pytest_asyncio.fixture
async def created_department(
    db_session: AsyncSession,
    department_repo: DepartmentRepository,
) -> Department:
    """Create a test department."""
    department = await department_repo.create(name="Test Department", parent_id=None)
    return department


@pytest_asyncio.fixture
async def created_employee(
    db_session: AsyncSession,
    employee_repo: EmployeeRepository,
    created_department: Department,
) -> Employee:
    """Create a test employee."""
    employee = await employee_repo.create(
        department_id=created_department.id,
        full_name="John Doe",
        position="Software Engineer",
        hired_at=date(2024, 1, 15),
    )
    return employee


@pytest_asyncio.fixture
async def department_tree(
    db_session: AsyncSession,
    department_repo: DepartmentRepository,
) -> dict[int, Department]:
    """Create a tree of departments for testing."""
    root = await department_repo.create(name="Root Department", parent_id=None)
    child1 = await department_repo.create(name="Child Department 1", parent_id=root.id)
    child2 = await department_repo.create(name="Child Department 2", parent_id=root.id)
    grandchild = await department_repo.create(name="Grandchild Department", parent_id=child1.id)

    return {
        "root": root,
        "child1": child1,
        "child2": child2,
        "grandchild": grandchild,
    }


def create_mock_department(
    id: int = 1,
    name: str = "Test Department",
    parent_id: int | None = None,
) -> MagicMock:
    """Helper to create a mock Department."""
    dept = MagicMock(spec=Department)
    dept.id = id
    dept.name = name
    dept.parent_id = parent_id
    dept.created_at = PropertyMock(return_value=None)
    return dept


def create_mock_employee(
    id: int = 1,
    department_id: int = 1,
    full_name: str = "John Doe",
    position: str = "Developer",
) -> MagicMock:
    """Helper to create a mock Employee."""
    emp = MagicMock(spec=Employee)
    emp.id = id
    emp.department_id = department_id
    emp.full_name = full_name
    emp.position = position
    return emp
