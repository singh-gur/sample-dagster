set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

IMAGE := "regv2.gsingh.io/personal/sample-dagster"
TAG := `git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD`
BRANCH := `git rev-parse --abbrev-ref HEAD | tr '/' '-'`

# Show all available recipes
[group('help')]
default:
    @just --list

# Show project info
[group('help')]
info:
    @echo "Project: sample-dagster"
    @.venv/bin/python --version | sed 's/^/Python: /'
    @uv --version | sed 's/^/UV: /'
    @.venv/bin/python -c 'import dagster; print("Dagster:", dagster.__version__)'

# Install dependencies and setup project
[group('setup')]
install:
    uv sync
    uv pip install -e .

# Sync dependencies from lockfile
[group('setup')]
sync:
    uv sync

# Show dependency tree
[group('setup')]
deps-tree:
    uv tree

# Show outdated dependencies
[group('setup')]
outdated:
    uv pip list --outdated

# Run all linters and formatters
[group('quality')]
lint: format check
    @echo "✅ Linting complete!"

# Format code with ruff
[group('quality')]
format:
    ruff format .

# Check code with ruff
[group('quality')]
check:
    ruff check .

# Run type checking with mypy
[group('quality')]
type-check:
    .venv/bin/mypy src/

# Audit dependencies for security vulnerabilities
[group('quality')]
audit:
    .venv/bin/pip-audit

# Run all tests with coverage
[group('test')]
test:
    .venv/bin/pytest --cov

# Run tests with detailed coverage report
[group('test')]
test-cov:
    .venv/bin/pytest --cov=src --cov-report=term-missing --cov-report=html

# Run a single test file
[group('test')]
test-file FILE:
    .venv/bin/pytest {{ FILE }}

# Run tests matching a pattern
[group('test')]
test-name PATTERN:
    .venv/bin/pytest -k "{{ PATTERN }}"

# Watch mode for tests (requires pytest-watch)
[group('test')]
test-watch:
    .venv/bin/ptw --ignore=src/sample_dagster/defs

# Start Dagster webserver
[group('dagster')]
dev:
    .venv/bin/dagster dev

# Start Dagster webserver with auto-reload
[group('dagster')]
dev-watch:
    .venv/bin/dagster dev --reload

# Build Dagster components
[group('dagster')]
build-dagster:
    .venv/bin/dagster-dg build

# Generate a new Dagster component
[group('dagster')]
generate NAME TYPE="asset":
    .venv/bin/dagster-dg generate {{ TYPE }} {{ NAME }}

# Build docker image
[group('docker')]
build-img:
    docker build --load -t {{ IMAGE }}:{{ TAG }} -t {{ IMAGE }}:{{ BRANCH }} -t {{ IMAGE }}:latest .

# Push docker image to registry
[group('docker')]
push-img: build-img
    docker push {{ IMAGE }}:{{ TAG }}
    docker push {{ IMAGE }}:{{ BRANCH }}
    docker push {{ IMAGE }}:latest

# Build and run locally with Docker
[group('docker')]
run-local: build-img
    docker run --rm -p 3000:3000 {{ IMAGE }}:latest

# Set Concourse pipeline
[group('ci')]
ci-set TARGET:
    ci/set-pipeline.sh {{ TARGET }}

# Trigger test job
[group('ci')]
ci-test TARGET:
    fly -t {{ TARGET }} trigger-job -j sample-dagster/test

# Trigger build job
[group('ci')]
ci-build TARGET:
    fly -t {{ TARGET }} trigger-job -j sample-dagster/build-and-push

# Trigger release job
[group('ci')]
ci-release TARGET:
    fly -t {{ TARGET }} trigger-job -j sample-dagster/release

# Watch build job logs
[group('ci')]
ci-watch TARGET:
    fly -t {{ TARGET }} watch -j sample-dagster/build-and-push

# Destroy pipeline
[group('ci')]
ci-destroy TARGET:
    fly -t {{ TARGET }} destroy-pipeline -p sample-dagster

# Remove Python cache files
[group('cleanup')]
clean-cache:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Remove all generated files
[group('cleanup')]
clean: clean-cache
    rm -rf .pytest_cache .ruff_cache htmlcov .coverage coverage.xml 2>/dev/null || true
    rm -rf .venv 2>/dev/null || true

# Remove Dagster generated files
[group('cleanup')]
clean-dagster:
    rm -rf .dagster 2>/dev/null || true

# Full cleanup (cache + venv + dagster)
[group('cleanup')]
distclean: clean clean-dagster
    @echo "✅ Full cleanup complete!"

# Activate virtual environment (print command to eval)
[group('help')]
activate:
    @echo "source .venv/bin/activate"
