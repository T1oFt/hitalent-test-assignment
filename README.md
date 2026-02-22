# Hitalent Test Assignment

API организационной структуры для управления подразделениями и сотрудниками.

## Оглавление

- [О проекте](#о-проекте)
- [Архитектура проекта](#архитектура-проекта)
- [Быстрый старт](#быстрый-старт)
- [API Endpoints](#api-endpoints)
- [Тестирование](#тестирование)
- [Технологический стек](#технологический-стек)

---

## О проекте

REST API для управления организационной структурой компании с поддержкой:
- Иерархии подразделений (дерево вложенности)
- Управления сотрудниками внутри подразделений
- Каскадного удаления и перевода сотрудников между подразделениями
- Валидации данных и обработки ошибок

---

## Архитектура проекта

Проект следует модульной архитектуре с разделением ответственности:

```
src/
├── api/                    # Слой API (FastAPI routers)
│   ├── departments.py      # Endpoints для подразделений
│   ├── employees.py        # Endpoints для сотрудников
│   ├── exception_handlers.py # Обработчики ошибок
│   └── decorators.py       # Декораторы (ETag, кэширование)
├── models/                 # SQLAlchemy ORM модели
│   ├── department.py       # Модель Department
│   └── employee.py         # Модель Employee
├── schemas/                # Pydantic схемы для валидации
│   ├── department.py       # Схемы подразделений
│   └── employee.py         # Схемы сотрудников
├── services/               # Бизнес-логика
│   ├── department_service.py # Логика работы с подразделениями
│   └── employee_service.py   # Логика работы с сотрудниками
├── db/                     # Репозитории и БД
│   ├── base.py             # Базовый класс SQLAlchemy
│   ├── department_repository.py # Репозиторий подразделений
│   └── employee_repository.py   # Репозиторий сотрудников
├── dependencies/           # FastAPI зависимости (DI)
├── alembic/                # Миграции БД
├── config.py               # Конфигурация приложения
└── main.py                 # Точка входа FastAPI
```

### Слои архитектуры

| Слой | Описание |
|------|----------|
| **API** | HTTP endpoints, валидация запросов, сериализация ответов |
| **Services** | Бизнес-логика, валидация правил предметной области |
| **Repositories** | Работа с базой данных, CRUD операции |
| **Models** | ORM модели SQLAlchemy |
| **Schemas** | Pydantic схемы для валидации входных/выходных данных |

### Модель данных

```
Department (1) ────< (N) Department (рекурсивная связь через parent_id)
    │
    │ 1:N
    ▼
Employee
```

**Department:**
- `id` — первичный ключ
- `name` — название (1-200 символов, trim пробелов)
- `parent_id` — ссылка на родительское подразделение (nullable)
- `created_at` — дата создания

**Employee:**
- `id` — первичный ключ
- `department_id` — FK на Department
- `full_name` — ФИО (1-200 символов)
- `position` — должность (1-200 символов)
- `hired_at` — дата приёма на работу (nullable)
- `created_at` — дата создания

---

## Быстрый старт

### Требования

- Docker и Docker Compose
- Python 3.12+ (для локальной разработки)

### Запуск через start.sh

Проект включает удобный скрипт `start.sh` для управления запуском.

#### 1. Запуск приложения (production/development)

```bash
./start.sh
```

Скрипт:
- Собирает Docker-образы
- Запускает PostgreSQL и приложение через `docker-compose`
- Автоматически применяет миграции Alembic
- Приложение доступно по адресу: `http://localhost:8080`

#### 2. Запуск тестов

```bash
./start.sh --test
```

Опции для тестирования:
```bash
./start.sh --test --report-file report.html --coverage-dir ./coverage
```

| Опция | Описание |
|-------|----------|
| `--test` | Запустить тестовое окружение |
| `--report-file FILE` | Путь к файлу отчёта тестов (по умолчанию: `test-report.html`) |
| `--coverage-dir DIR` | Директория для отчётов coverage (по умолчанию: `coverage-report`) |
| `-h, --help` | Показать справку |

#### 3. Ручной запуск через Docker Compose

```bash
# Запуск приложения
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d

# Просмотр логов
docker-compose logs -f app

# Остановка
docker-compose down
```

### Переменные окружения

Скопируйте `.env.example` в `.env` и настройте при необходимости:

```bash
cp .env.example .env
```

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql+asyncpg://postgres:postgres@postgres:5432/hitalent` |
| `DEBUG` | Режим отладки | `True` |

---

## API Endpoints

Полная документация OpenAPI доступна после запуска:
- **Swagger UI:** http://localhost:8080/docs
- **ReDoc:** http://localhost:8080/redoc

### Подразделения (Departments)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/v1/departments/` | Создать подразделение |
| `GET` | `/api/v1/departments/{id}` | Получить подразделение с деревом |
| `PATCH` | `/api/v1/departments/{id}` | Обновить/переместить подразделение |
| `DELETE` | `/api/v1/departments/{id}` | Удалить подразделение |

### Сотрудники (Employees)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `POST` | `/api/v1/departments/{id}/employees/` | Создать сотрудника в подразделении |