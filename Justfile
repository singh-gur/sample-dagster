set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

IMAGE := "regv2.gsingh.io/personal/sample-dagster"
TAG := `git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD`
BRANCH := `git rev-parse --abbrev-ref HEAD | tr '/' '-'`

# ============================================================================
# Development Commands
# ============================================================================

# Install dependencies
install:
    uv sync
    uv pip install -e .

# Sync dependencies from lockfile
sync:
    uv sync

# Run all linters and formatters
lint: format check
    @echo "Linting complete!"

# Run ruff format
format:
    ruff format .

# Run ruff check
check:
    ruff check .

# Run tests
test:
    .venv/bin/pytest --cov

# Run tests with coverage report
test-cov:
    .venv/bin/pytest --cov=src --cov-report=term-missing --cov-report=html

# Run a single test file
test-file FILE:
    .venv/bin/pytest {{ FILE }}

# Run tests matching a pattern
test-name PATTERN:
    .venv/bin/pytest -k "{{ PATTERN }}"

# Watch mode for tests (requires pytest-watch)
test-watch:
    .venv/bin/ptw --ignore=src/sample_dagster/defs

# Start Dagster webserver for development
dev:
    .venv/bin/dagster dev

# Start Dagster webserver with reload on file changes
dev-watch:
    .venv/bin/dagster dev --reload

# Build Dagster components
build-dagster:
    .venv/bin/dagster-dg build

# Generate a new Dagster component
generate NAME TYPE="asset":
    .venv/bin/dagster-dg generate {{ TYPE }} {{ NAME }}

# Run type checking with mypy (if installed)
type-check:
    .venv/bin/mypy src/

# Audit dependencies for security vulnerabilities
audit:
    .venv/bin/pip-audit

# Show dependency tree
deps-tree:
    uv tree

# Show outdated dependencies
outdated:
    uv pip list --outdated

# ============================================================================
# Docker Commands
# ============================================================================

# Build docker image
build-img:
    docker build --load -t {{ IMAGE }}:{{ TAG }} -t {{ IMAGE }}:{{ BRANCH }} -t {{ IMAGE }}:latest .

# Push docker image
push-img: build-img
    docker push {{ IMAGE }}:{{ TAG }}
    docker push {{ IMAGE }}:{{ BRANCH }}
    docker push {{ IMAGE }}:latest

# Build and run locally with Docker
run-local: build-img
    docker run --rm -p 3000:3000 {{ IMAGE }}:latest

# ============================================================================
# Cleanup Commands
# ============================================================================

# Remove Python cache files
clean-cache:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove all generated files
clean: clean-cache
    rm -rf .pytest_cache .ruff_cache htmlcov .coverage coverage.xml 2>/dev/null || true
    rm -rf .venv 2>/dev/null || true

# Remove DAGster generated files
clean-dagster:
    rm -rf .dagster 2>/dev/null || true

# Full cleanup
distclean: clean clean-dagster
    @echo "Full cleanup complete!"

# ============================================================================
# Concourse CI/CD Commands
# ============================================================================

# Set Concourse pipeline
ci-set-pipeline TARGET:
    ci/set-pipeline.sh {{ TARGET }}

# Trigger test job
ci-trigger-test TARGET:
    fly -t {{ TARGET }} trigger-job -j sample-dagster/test

# Trigger build-and-push job
ci-trigger-build TARGET:
    fly -t {{ TARGET }} trigger-job -j sample-dagster/build-and-push

# Trigger release job
ci-trigger-release TARGET:
    fly -t {{ TARGET }} trigger-job -j sample-dagster/release

# Watch build-and-push job
ci-watch-build TARGET:
    fly -t {{ TARGET }} watch -j sample-dagster/build-and-push

# Destroy pipeline
ci-destroy TARGET:
    fly -t {{ TARGET }} destroy-pipeline -p sample-dagster

# ============================================================================
# Utility Commands
# ============================================================================

# Show project info
info:
    @echo "Project: sample-dagster"
    @.venv/bin/python --version | sed 's/^/Python: /'
    @uv --version | sed 's/^/UV: /'
    @.venv/bin/python -c 'import dagster; print("Dagster:", dagster.__version__)'

# Show all available just recipes
list:
    just --list

# Activate virtual environment
activate:
    @echo "source .venv/bin/activate"
