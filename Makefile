.PHONY: help install install-dev test test-cov lint format type-check security build run clean docker-build docker-run docker-down mysql-client diff-cov

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
	pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml:coverage.xml

diff-cov: ## Check diff coverage against origin/main (fail if < 90%)
	@if [ ! -f coverage.xml ]; then \
		echo "Generating coverage.xml via pytest..."; \
		pytest --cov=app --cov-report=xml:coverage.xml >/dev/null; \
	fi
	@BASE_REF=$$(git merge-base HEAD origin/main); \
	echo "Comparing coverage against $$BASE_REF"; \
	diff-cover coverage.xml --compare-branch $$BASE_REF --fail-under=90

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
	-safety check

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

mysql-client: ## Connect to development MySQL database
	@echo "Connecting to development MySQL database..."
	@if docker-compose ps db 2>/dev/null | grep -q "Up"; then \
		echo "Using Docker Compose MySQL instance..."; \
		docker-compose exec db mysql -u fastapi_user -pfastapi_pass fastapi_db; \
	elif docker-compose -f docker-compose.dev.yml ps db 2>/dev/null | grep -q "Up"; then \
		echo "Using Docker Compose dev MySQL instance..."; \
		docker-compose -f docker-compose.dev.yml exec db mysql -u fastapi_user -pfastapi_pass fastapi_db; \
	elif command -v mysql >/dev/null 2>&1; then \
		echo "Using local MySQL client with connection details from environment..."; \
		if [ -f .env ]; then \
			export $$(grep -v '^#' .env | xargs); \
			mysql -h localhost -P 3306 -u fastapi_user -pfastapi_pass fastapi_db; \
		else \
			mysql -h localhost -P 3306 -u fastapi_user -pfastapi_pass fastapi_db; \
		fi; \
	else \
		echo "❌ Error: No MySQL connection available."; \
		echo "Please ensure either:"; \
		echo "  1. Docker Compose is running: make docker-dev"; \
		echo "  2. MySQL client is installed: apt install mysql-client"; \
		exit 1; \
	fi

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
tf-init: ## Initialize Terraform with environment-specific backend (usage: make tf-init env=staging)
	cd terraform && terraform init -backend-config="backend-$(env).conf"

tf-plan: ## Plan Terraform changes (usage: make tf-plan env=staging)
	@if [ ! -f "terraform/cloudflare-cert-trigpointing-$(shell echo $(env) | sed 's/staging/me/;s/production/uk/').tfvars" ]; then \
		echo "🔑 CloudFlare certificate file not found. Using base configuration only..."; \
		cd terraform && terraform plan -var-file="$(env).tfvars"; \
	else \
		echo "🔑 Using CloudFlare certificates for $(env)..."; \
		cd terraform && terraform plan -var-file="$(env).tfvars" -var-file="cloudflare-cert-trigpointing-$(shell echo $(env) | sed 's/staging/me/;s/production/uk/').tfvars"; \
	fi

tf-apply: ## Apply Terraform changes (usage: make tf-apply env=staging)
	@if [ ! -f "terraform/cloudflare-cert-trigpointing-$(shell echo $(env) | sed 's/staging/me/;s/production/uk/').tfvars" ]; then \
		echo "🔑 CloudFlare certificate file not found. Using base configuration only..."; \
		cd terraform && terraform apply -var-file="$(env).tfvars"; \
	else \
		echo "🔑 Using CloudFlare certificates for $(env)..."; \
		cd terraform && terraform apply -var-file="$(env).tfvars" -var-file="cloudflare-cert-trigpointing-$(shell echo $(env) | sed 's/staging/me/;s/production/uk/').tfvars"; \
	fi

tf-destroy: ## Destroy Terraform infrastructure (usage: make tf-destroy env=staging)
	@if [ ! -f "terraform/cloudflare-cert-trigpointing-$(shell echo $(env) | sed 's/staging/me/;s/production/uk/').tfvars" ]; then \
		echo "🔑 CloudFlare certificate file not found. Using base configuration only..."; \
		cd terraform && terraform destroy -var-file="$(env).tfvars"; \
	else \
		echo "🔑 Using CloudFlare certificates for $(env)..."; \
		cd terraform && terraform destroy -var-file="$(env).tfvars" -var-file="cloudflare-cert-trigpointing-$(shell echo $(env) | sed 's/staging/me/;s/production/uk/').tfvars"; \
	fi

tf-validate: ## Validate Terraform configuration
	cd terraform && terraform validate

tf-fmt: ## Format Terraform files
	cd terraform && terraform fmt -recursive

# CI/CD
pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

ci: format-check lint type-check security test ## Run all CI checks
