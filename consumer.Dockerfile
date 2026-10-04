FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_SYSTEM_PYTHON=1
ENV UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./
RUN uv pip install -r pyproject.toml

FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ ./src

# Запуск FastStream воркера
CMD ["faststream", "run", "src.consumer.app:app"]
