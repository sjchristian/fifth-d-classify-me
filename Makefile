SHELL := /bin/bash

.PHONY: deps

deps:
	python -m venv venv; \
	source venv/bin/activate; \
	pip install --upgrade pip; \
	pip install --upgrade pip-tools; \
	pip-compile --upgrade --output-file requirements.txt requirements.in && \
	pip install --upgrade -r requirements.txt
