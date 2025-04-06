# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Testing Commands

- Install dependencies: `uv pip install -e .`
- Run linter: `ruff check src/ tests/`
- Run formatter: `ruff format src/ tests/`
- Run all tests: `pytest`
- Run a single test: `pytest tests/test_file.py::test_function`
- Run with coverage: `pytest --cov=intake_document`
- Type checking: `mypy src/`

## Coding Style Guidelines

- Python 3.13+ compatibility required
- Use 4 spaces for indentation; 79 char line limit
- Follow Google-style docstrings
- Import order: stdlib → 3rd party → local
- Naming: functions/variables (snake_case), classes (PascalCase), constants (UPPER_SNAKE_CASE)
- Use type hints for all functions and methods
- Handle errors explicitly; use specific exceptions
- Use Pydantic for data validation
- Write tests for all code using pytest (Arrange-Act-Assert pattern)
- Follow separation of concerns: separate CLI, config, business logic
- Prioritize readability over optimization