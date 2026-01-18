"""Constants for Dagster definitions."""

import os
from pathlib import Path

# DuckDB database file for local development and testing (legacy)
DUCKDB_DATABASE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "duckdb.db"

# Trino connection configuration
TRINO_HOST = os.getenv("TRINO_HOST", "localhost")
TRINO_PORT = int(os.getenv("TRINO_PORT", "8080"))
TRINO_USER = os.getenv("TRINO_USER", "dagster")
TRINO_CATALOG = os.getenv("TRINO_CATALOG", "iceberg")
TRINO_SCHEMA = os.getenv("TRINO_SCHEMA", "dagster_assets")

# Iceberg configuration
ICEBERG_WAREHOUSE_PATH = os.getenv(
    "ICEBERG_WAREHOUSE_PATH",
    str(Path(__file__).parent.parent.parent.parent / "data" / "iceberg-warehouse"),
)
