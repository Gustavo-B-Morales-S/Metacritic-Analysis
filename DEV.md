# Development Tools

- Taskipy: Automate repetitive commands
- Ruff: Linter & Formatter (Automated with Pre-Commit)
- Pre-Commit: Verify quality issues before the commit
- Bandit: Find Security Issues (Automated with Pre-Commit)

## Taskipy Usage

The project uses Taskipy to manage development tasks efficiently. Below are some useful commands:

- **Run the scraper**:
  ```bash
  task run
  ```
  - Executes `poetry run python3 src/extraction/spider.py`.
  - Ensures proper virtual environment context.

- **Clean cache files**:
  ```bash
  task del_cache
  ```
  - Removes temporary files like `__pycache__`, `.pyc`, `.pyo`, `.ruff`, and pytest cache.

- **Linting and formatting**:
  ```bash
  task lint
  ```
  - Runs `ruff check .` for static analysis and `ruff format . --diff` to preview format changes.

  ```bash
  task format
  ```
  - Applies auto-fixes and formatting using `ruff`.

- **Run tests with coverage**:
  ```bash
  task test
  ```
  - Runs `pytest` with `--cov` for coverage reporting and `-vv` for extra verbose output.

- **View the coverage report**:
  ```bash
  task cov
  ```
  - Generates and opens the HTML coverage report
