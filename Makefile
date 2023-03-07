check: ## Check source code issues.
	black --diff --check .
	isort --diff --check .
	mypy --install-types --non-interactive .
	bandit --recursive . --configfile pyproject.toml
	find . -iname "*.py" \
		-not -path "./.git/*" \
		-not -path "./venv/*" \
		-not -path "*/migrations/*" | xargs pylint

deps: ## Install python dependencies
	python -m pip install --upgrade pip
	python -m pip install --requirement requirements.txt

fmt: ## Format code.
	black .
	isort --atomic .

.PHONY: test
test: ## Run tests.
	coverage run --source='.' manage.py test
	coverage report
	coverage xml

help: ## Show this help.
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} { \
		if (/^[a-zA-Z_-]+:.*?##.*$$/) {printf "    %-20s%s\n", $$1, $$2} \
		else if (/^## .*$$/) {printf "  %s\n", substr($$1,4)} \
		}' $(MAKEFILE_LIST)
