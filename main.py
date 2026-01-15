"""Sample Dagster project entry point."""

from dagster import Definitions

from sample_dagster import (
    all_assets,
    resources,
)


def get_dagster_definitions() -> Definitions:
    """Get the Dagster definitions for this project."""
    return Definitions(
        assets=all_assets,
        resources=resources,
    )


if __name__ == "__main__":
    # Allow running basic verification
    defs = get_dagster_definitions()
    print(f"Dagster definitions loaded: {len(defs.assets)} assets, {len(defs.jobs)} jobs")
