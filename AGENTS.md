# AGENTS.md - Development Guidelines for Agentic Coding Agents

This document provides guidelines for agents operating in this Dagster-based project repository.

## Build, Lint, and Test Commands

### Package Management
```bash
uv add <package>              # Add a dependency
uv add --dev <package>        # Add a dev dependency
uv sync                       # Sync dependencies from lockfile
uv pip install -e .           # Install package in editable mode
```

### Code Quality
```bash
ruff check .                  # Run linter on entire project
ruff check <file.py>          # Lint specific file
ruff format .                 # Format entire project
ruff format <file.py>         # Format specific file
```

### Running Tests
```bash
pytest                        # Run all tests
pytest tests/<file>.py        # Run tests in specific file
pytest -k "<test_name>"       # Run tests matching pattern
pytest --cov                  # Run with coverage report
```

### Dagster Development
```bash
dagster dev                   # Start Dagster webserver
dagster-dg generate <name>    # Generate new component
dagster-dg build              # Build Dagster components
```

### Docker Operations
```bash
just build                    # Build Docker image
just push                     # Push Docker image
```

## Code Style Guidelines

### Imports
- Use absolute imports: `from dagster import definitions`
- Group imports: standard library, third-party, local modules
- Do not use wildcard imports (`from module import *`)
- Sort imports alphabetically within groups

### Formatting
- Line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Use Black-compatible formatting (ruff will auto-format)

### Type Hints
- Provide type hints for all function parameters and return values
- Use Python 3.13+ syntax (no `from __future__ import annotations`)
- Example:
  ```python
  from pathlib import Path
  from dagster import Definitions, AssetSelection

  def load_assets(path: Path) -> list[Asset]:
      ...
  ```

### Naming Conventions
- **Variables/functions**: `snake_case` (e.g., `my_asset`, `fetch_data`)
- **Classes**: `PascalCase` (e.g., `MyCustomAsset`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private methods**: `_private_method` (leading underscore)
- **Module names**: `snake_case` (e.g., `asset_pipeline`)

### Error Handling
- Use specific exception types (avoid bare `except:`)
- Propagate exceptions with context: `raise ... from original`
- Log errors before raising:
  ```python
  import structlog

  logger = structlog.get_logger()

  try:
      result = risky_operation()
  except ValueError as e:
      logger.error("Operation failed", error=str(e))
      raise
  ```
- Use Dagster's exception types: `DagsterInvariantViolationError`, `DagsterUserCodeExecutionError`

### Dagster Patterns
- Use `@definitions` decorator for the main definitions function
- Use `load_from_defs_folder` for loading components from a folder structure
- Define assets in separate files under `defs/` directory
- Use descriptive asset names: `prefixed_asset_name`
- Example structure:
  ```
  src/sample_dagster/
  ├── __init__.py
  ├── definitions.py          # Main @definitions entry point
  └── defs/
      └── assets/
          └── my_asset.py
  ```

### File Structure
- Maximum 400 lines per file (split if larger)
- Keep related functionality together
- Use `__init__.py` for public API exports
- Place tests alongside source files: `path/to/module.py` -> `tests/test_module.py`

### Security
- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all inputs (Dagster handles config validation via config schemas)
- Use parameterized queries if interacting with databases

### Git Workflow
- Write meaningful commit messages describing the "why"
- Keep commits atomic and focused
- Create feature branches from `main`
- Squash fixup commits before merging

### Documentation
- Document public APIs with docstrings
- Use Google-style docstrings:
  ```python
  def my_asset(context: AssetExecutionContext) -> None:
      """Process data and emit results.

      Args:
          context: The asset execution context containing run configuration.

      Returns:
          None: Assets don't return values, they materialize outputs.
      """
  ```
- Explain Dagster-specific patterns in comments
