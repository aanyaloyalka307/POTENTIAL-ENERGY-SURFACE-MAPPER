.PHONY: help setup verify test scan analyse compare landscape viewer all clean

PY ?= .venv/bin/python
PIP ?= .venv/bin/pip

help:
	@echo "make setup    create .venv and install dependencies"
	@echo "make verify   Phase 0 - prove the environment works"
	@echo "make test     run the test suite"
	@echo "make scan     Phase 4 - run the geometry scan (~2 min)"
	@echo "make analyse  Phase 5 - extract observables and plot"
	@echo "make compare  Phase 6 - ansatz comparison (~15 min)"
	@echo "make landscape  the 3D E(R,theta) surface (~25 s)"
	@echo "make viewer   open that surface interactively"
	@echo "make all      verify, test, scan, analyse"

setup:
	python3 -m venv .venv
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt
	@echo "done - now run: make verify"

verify:
	$(PY) verify_env.py

test:
	$(PY) -m pytest tests/ -q

scan:
	$(PY) scan.py

analyse:
	$(PY) analyse.py

compare:
	$(PY) compare_ansatz.py

landscape:
	$(PY) landscape.py

viewer:
	$(PY) viewer.py

all: verify test scan analyse

clean:
	rm -rf __pycache__ tests/__pycache__ .pytest_cache
	rm -f data/*.npz
