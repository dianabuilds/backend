.PHONY: setup lint type unit build

setup:  ## install deps
	python -m pip install -U pip
	pip install -r requirements.txt
	pre-commit install

lint:   ## ruff + black --check
	ruff check .
	black --check .

type:   ## mypy/pyright
	mypy apps/backend

unit:   ## fast tests only
	pytest -q -m "not slow" --maxfail=1

build:  ## optional package/build
	python -m build
