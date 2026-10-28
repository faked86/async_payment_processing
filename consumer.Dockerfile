FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Обязательно указываем uv ставить пакеты в системный путь
ENV UV_PROJECT_ENVIRONMENT=/usr/local
ENV UV_NO_CACHE=1
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml uv.lock ./

# Ставим только прод-зависимости, игнорируя dev-тесты
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.14-slim

WORKDIR /app

# Гарантируем, что Python будет видеть текущую директорию (/app) и папку src в ней
ENV PYTHONPATH=.

COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Копируем исходный код
COPY src/ ./src

# Запуск FastStream воркера
CMD ["faststream", "run", "src.consumer.app:app"]
