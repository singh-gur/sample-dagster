"""Constants for Dagster definitions."""

from pathlib import Path

# DuckDB database file for local development and testing
DUCKDB_DATABASE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "duckdb.db"
