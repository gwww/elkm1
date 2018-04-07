.PHONY: install clean isort lint debug test status

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf build dist *.egg-info

install:
	pip install -e .

isort:
	sh -c "isort --skip-glob=.tox --recursive . "

lint:
	pylint --msg-template='{msg_id}({symbol}):{line:3d},{column}: {obj}: {msg}' elkm1

debug:
	python -m pdb temp/test.py

run:
	bin/elk -i

status:
	bin/mkdoc

test:
	pytest
