.PHONY: help docs docs-build clean install install-full lint typecheck fmt format test test-cov build publish-test publish
.DEFAULT_GOAL := help

help:
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

docs: ## Serve the Material documentation site
	uv run --group docs mkdocs serve

docs-build: ## Build the Material documentation site strictly
	uv run --group docs mkdocs build --strict

clean: ## Removing cached python compiled files
	find . -name \*pyc  | xargs  rm -fv
	find . -name \*pyo | xargs  rm -fv
	find . -name \*~  | xargs  rm -fv
	find . -name __pycache__  | xargs  rm -rfv
	find . -name .ruff_cache  | xargs  rm -rfv

install: ## Install every dependency group into the local environment
	uv sync --group dev --group tests --group docs

install-full:install ## Install dependencies with pre-commit
	uv run pre-commit install -f

lint: ## Run code linters
	uv run ruff check --ignore F401 src tests examples

typecheck: ## Run the type checker over the shipped package
	uv run pyrefly check src

fmt format: ## Run code formatters
	uv run ruff format src tests examples
	uv run ruff check --fix src tests examples

test: ## Run tests and documentation doctests
	uv run --group tests pytest

test-cov: ## Run tests with coverage
	uv run --group tests pytest --cov=django_modern_schemas --cov-report term-missing

build:clean ## Build the sdist and the wheel into dist/
	rm -rf dist
	uv build

publish-test:build ## Upload to TestPyPI (needs UV_PUBLISH_TOKEN of test.pypi.org)
	uv publish --index testpypi

publish:build ## Upload to PyPI (needs UV_PUBLISH_TOKEN of pypi.org)
	uv publish
