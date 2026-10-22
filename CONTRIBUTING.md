# Contributing to UtsavAI

Thank you for contributing to UtsavAI! We welcome improvements, bug reports, and optimizations.

## Development Workflow

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mohdubes/utsavai-event-planner.git
   cd utsavai-event-planner
   ```

2. **Set up virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install mypy
   ```

3. **Run development server**:
   ```bash
   python dev.py
   ```

## Code Quality Standards

We enforce strict linting, formatting, and typing standards:
- **Linting**: `python -m ruff check .`
- **Formatting**: `python -m ruff format --check .`
- **Type Checking**: `python -m mypy backend`
- **Testing**: `python -m pytest`
- **Full Check**: `make check` (or run lint, mypy, and pytest)

All pull requests must pass automated CI checks without regressions. Maintain test coverage at or above 85%.
