FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy only dependency files first for layer caching
COPY pyproject.toml .python-version* uv.lock README.md ./
COPY sample_dagster ./sample_dagster

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY main.py .

CMD ["python", "-m", "main"]
