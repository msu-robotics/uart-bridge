FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY src/. .
COPY pyproject.toml .
COPY uv.lock .

# Sync the project
RUN uv sync --locked

# Открытие порта
EXPOSE 8000

# Запуск приложения
CMD ["python", "main.py"]