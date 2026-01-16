from pathlib import Path

from dagster import Definitions, load_from_defs_folder

# Load all definitions from the defs folder
defs = Definitions.merge(load_from_defs_folder(path_within_project=Path(__file__).parent / "defs"))
