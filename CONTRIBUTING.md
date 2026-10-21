# Contributing to UtsavAI

Thank you for your interest in contributing to UtsavAI! We welcome all contributions, bug reports, and suggestions.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MOHDUBES/Utsavai-event-planner.git
   cd Utsavai-event-planner
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

## Code Quality Standards

We enforce strict code quality guidelines:

- **Formatting & Linting:** Code must pass `ruff check .` and `ruff format --check .`.
- **Testing:** All new features or bug fixes must include unit or integration tests in `tests/`.
- **Coverage:** Minimum test coverage is 90% (`pytest --cov=backend`).
- **Modularity:** Keep cyclomatic complexity low (C901 <= 10). Split large functions into single-responsibility helpers.
- **Type Annotations:** All backend code must have full type annotations.

## Running Tests & Checks

```bash
# Run all tests
pytest

# Run linter
ruff check .

# Check code formatting
ruff format --check .
```
