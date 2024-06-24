python3 -m bubble.cli -f code.py

### tests

PYTHONPATH=. pytest tests/
PYTHONPATH=. pytest tests/ --disable-warnings

ruff check --select I --fix
ruff format
