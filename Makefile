.PHONY: help install install-dev test test-cov lint format type-check security build run clean docker-build docker-run docker-down

# Default target
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=app --cov-report=term-missing --cov-report=html

# Code quality
lint: ## Run linting
	flake8 app tests
	mypy app --ignore-missing-imports

format: ## Format code
	black app tests
	isort app tests

format-check: ## Check code formatting
	black --check app tests
	isort --check-only app tests

type-check: ## Run type checking
	mypy app --ignore-missing-imports

security: ## Run security checks
	bandit -r app
	safety check

# Application
build: ## Build the application
	docker build -t fastapi-app .

run: ## Run the application locally
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker commands
docker-build: ## Build Docker image
	docker build -t fastapi-app .

docker-run: ## Run application with Docker Compose
	docker-compose up -d

docker-dev: ## Run application in development mode with Docker Compose
	docker-compose -f docker-compose.dev.yml up -d

docker-down: ## Stop Docker containers
	docker-compose down
	docker-compose -f docker-compose.dev.yml down

docker-logs: ## View Docker logs
	docker-compose logs -f

# Database
db-migrate: ## Run database migrations
	alembic upgrade head

db-migration: ## Create new database migration
	alembic revision --autogenerate -m "$(msg)"

# Cleanup
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

# Terraform commands
tf-init: ## Initialize Terraform
	cd terraform && terraform init

tf-plan: ## Plan Terraform changes
	cd terraform && terraform plan -var-file="$(env).tfvars"

tf-apply: ## Apply Terraform changes
	cd terraform && terraform apply -var-file="$(env).tfvars"

tf-destroy: ## Destroy Terraform infrastructure
	cd terraform && terraform destroy -var-file="$(env).tfvars"

# CI/CD
pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

ci: format-check lint type-check security test ## Run all CI checks
