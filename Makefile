.PHONY: lint format typecheck test check dev clean

lint:
	python -m ruff check .

format:
	python -m ruff format .

typecheck:
	python -m mypy backend

test:
	python -m pytest

check: lint typecheck test

dev:
	python dev.py

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').glob('.pytest_cache')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').glob('.mypy_cache')]"
