set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

IMAGE := "regv2.gsingh.io/personal/sample-dagster"
TAG := `git describe --tags --exact-match 2>/dev/null || git rev-parse --short HEAD`
BRANCH := `git rev-parse --abbrev-ref HEAD | tr '/' '-'`

build:
    docker build -t {{IMAGE}}:{{TAG}} -t {{IMAGE}}:{{BRANCH}} -t {{IMAGE}}:latest .

push: build
    docker push {{IMAGE}}:{{TAG}}
    docker push {{IMAGE}}:{{BRANCH}}
    docker push {{IMAGE}}:latest
