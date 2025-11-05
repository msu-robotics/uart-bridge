FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов
# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=/app/uv.lock \
    --mount=type=bind,source=pyproject.toml,target=/app/pyproject.toml \
    uv sync --locked --no-install-project

COPY src/. .
COPY pyproject.toml .
COPY uv.lock .

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "main.py"]