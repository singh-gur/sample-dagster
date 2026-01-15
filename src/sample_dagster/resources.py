"""Resources for Dagster assets."""

from dataclasses import dataclass
from typing import Any

from dagster_duckdb import DuckDBResource


@dataclass
class CustomDuckDBResource(DuckDBResource):
    """Extended DuckDB resource with custom configuration."""

    @property
    def schema_path(self) -> str:
        """Path to schema files for reference."""
        return "/app/schemas"
