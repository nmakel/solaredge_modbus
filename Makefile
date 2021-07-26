all: lint

.PHONY: lint
lint:
	flake8 --ignore=E501,W503

.PHONY: release
release:
	python3 -m build
	python3 -m twine upload dist/*

clean:
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
	rm -rf build
	rm -rf dist
	rm -rf src/*.egg-info