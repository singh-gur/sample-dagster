from pathlib import Path

from dagster import Definitions, load_from_defs_folder

from .defs.io_managers import TrinoIOManager

# Load all definitions from the defs folder
loaded_defs = load_from_defs_folder(path_within_project=Path(__file__).parent / "defs")

# Configure Trino IO Manager for all assets
defs = Definitions.merge(
    loaded_defs,
    Definitions(
        resources={
            "io_manager": TrinoIOManager(),
        }
    ),
)
