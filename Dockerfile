FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy only dependency files first for layer caching
COPY . .

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code

ENTRYPOINT [ "/app/.venv/bin/python" ]
