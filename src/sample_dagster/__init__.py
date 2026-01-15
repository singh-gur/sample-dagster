"""Dagster definitions for sample-dagster project."""

from dagster import Definitions, load_assets_from_modules
from dagster_duckdb import DuckDBResource

from . import assets

# Load all assets from the assets module
all_assets = load_assets_from_modules([assets])

# Define resources
resources = {
    "duckdb": DuckDBResource(
        database="sample_dagster.duckdb",
    ),
}

# Define the full Dagster definitions
definitions = Definitions(
    assets=all_assets,
    resources=resources,
)
