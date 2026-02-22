FROM python:3.12-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей и установка
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Копирование исходного кода
COPY alembic.ini ./
COPY src/ ./src/

# Запуск приложения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]