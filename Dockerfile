FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy application code
COPY . .

# Install the package with dependencies
RUN pip install --no-cache-dir .

# Create non-root user for security
RUN groupadd -r dagster && \
    useradd -r -g dagster -u 1000 dagster

# Create Dagster home directory and copy configuration
RUN mkdir -p /opt/dagster/dagster_home/storage && \
    cp dagster.yaml /opt/dagster/dagster_home/dagster.yaml && \
    chown -R dagster:dagster /opt/dagster && \
    chown -R dagster:dagster /app

# Switch to non-root user
USER dagster

# Set Dagster home environment variable
ENV DAGSTER_HOME=/opt/dagster/dagster_home

# Expose gRPC port
EXPOSE 3030

# The Helm chart will override this with dagster api grpc commands
# But we provide a sensible default for local testing
CMD ["dagster", "api", "grpc", "--module-name", "sample_dagster", "--host", "0.0.0.0", "--port", "3030"]
