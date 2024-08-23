.PHONY: clean setup format check lint run status status

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	find . -name '.cache' -exec rm -rf {} +
	find . -name '.mypy_cache' -exec rm -rf {} +
	find . -name '.pytest_cache' -exec rm -rf {} +
	find . -name '.ruff_cache' -exec rm -rf {} +
	rm -rf build dist *.egg-info

setup:
	uv sync

format:
	ruff format

check:
	ruff check --no-fix

lint:
	pylint --msg-template='{msg_id}({symbol}):{line:3d},{column}: {obj}: {msg}' elkm1_lib

run:
	bin/elk -i

status:
	bin/mkdoc

test:
	pytest
