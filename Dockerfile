FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Install uv
RUN pip install --no-cache-dir uv

# Copy only dependency files first for layer caching
COPY pyproject.toml .python-version* uv.lock README.md ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src ./src
COPY main.py .

CMD ["python", "-m", "main"]
