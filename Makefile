.PHONY: help install install-dev test test-cov lint format type-check security build run clean docker-build docker-run docker-down mysql-client diff-cov \
	run-staging db-tunnel-staging-start db-tunnel-staging-stop mysql-staging

# Default target
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Local development against STAGING via Bastion SSH tunnel (no Docker)
# ---------------------------------------------------------------------------

# Defaults (override on the command line or environment as needed)
AWS_REGION ?= eu-west-1
STAGING_SECRET_ARN ?= arn:aws:secretsmanager:eu-west-1:534526983272:secret:fastapi-staging-credentials-udrQoU
SSH_BASTION_HOST ?= bastion.trigpointing.uk
SSH_BASTION_USER ?= ec2-user
SSH_KEY_PATH ?= ~/.ssh/trigpointing-bastion.pem
LOCAL_DB_TUNNEL_PORT ?= 3307

# Start an SSH tunnel through the bastion to the staging RDS endpoint
db-tunnel-staging-start: ## Start SSH tunnel to staging RDS on localhost:$(LOCAL_DB_TUNNEL_PORT)
	@command -v aws >/dev/null 2>&1 || { echo "❌ aws CLI not found. Install and configure AWS credentials."; exit 1; }
	@command -v jq >/dev/null 2>&1 || { echo "❌ jq not found. Please install jq."; exit 1; }
	@mkdir -p .ssh
	@echo "🔎 Fetching staging DB host/port from Secrets Manager ($(STAGING_SECRET_ARN))"
	@SECRET_JSON=$$(aws --region $(AWS_REGION) secretsmanager get-secret-value --secret-id $(STAGING_SECRET_ARN) --query SecretString --output text); \
	RDS_HOST=$$(echo "$$SECRET_JSON" | jq -r '.host'); \
	RDS_PORT=$$(echo "$$SECRET_JSON" | jq -r '.port'); \
	echo "🌐 Tunnelling 127.0.0.1:$(LOCAL_DB_TUNNEL_PORT) → $$RDS_HOST:$$RDS_PORT via $(SSH_BASTION_USER)@$(SSH_BASTION_HOST)"; \
	# Reuse an existing control socket if present; otherwise create it and forward the port
	if ssh -S .ssh/fastapi-staging-tunnel -O check $(SSH_BASTION_USER)@$(SSH_BASTION_HOST) 2>/dev/null; then \
	  echo "✅ Tunnel already running"; \
	else \
	  ssh -i $(SSH_KEY_PATH) -o ExitOnForwardFailure=yes -M -S .ssh/fastapi-staging-tunnel -f -N \
	    -L 127.0.0.1:$(LOCAL_DB_TUNNEL_PORT):$$RDS_HOST:$$RDS_PORT \
	    $(SSH_BASTION_USER)@$(SSH_BASTION_HOST) && echo "✅ Tunnel started"; \
	fi

# Stop the SSH tunnel
db-tunnel-staging-stop: ## Stop SSH tunnel to staging RDS if running
	@ssh -S .ssh/fastapi-staging-tunnel -O exit $(SSH_BASTION_USER)@$(SSH_BASTION_HOST) 2>/dev/null || true
	@rm -f .ssh/fastapi-staging-tunnel
	@echo "🛑 Tunnel stopped (if it was running)"

# Run FastAPI locally with live reload, using staging credentials via the tunnel
run-staging: ## Run FastAPI locally against staging DB (requires db-tunnel-staging-start)
	@command -v aws >/dev/null 2>&1 || { echo "❌ aws CLI not found. Install and configure AWS credentials."; exit 1; }
	@command -v jq >/dev/null 2>&1 || { echo "❌ jq not found. Please install jq."; exit 1; }
	@SECRET_JSON=$$(aws --region $(AWS_REGION) secretsmanager get-secret-value --secret-id $(STAGING_SECRET_ARN) --query SecretString --output text); \
	DB_USER=$$(echo "$$SECRET_JSON" | jq -r '.username'); \
	DB_PASSWORD=$$(echo "$$SECRET_JSON" | jq -r '.password'); \
	DB_NAME=$$(echo "$$SECRET_JSON" | jq -r '.dbname // .database'); \
	echo "🚀 Starting FastAPI with hot reload on http://127.0.0.1:8000"; \
	. venv/bin/activate && \
	ENVIRONMENT=development \
	DB_HOST=127.0.0.1 DB_PORT=$(LOCAL_DB_TUNNEL_PORT) \
	DB_USER="$$DB_USER" DB_PASSWORD="$$DB_PASSWORD" DB_NAME="$$DB_NAME" \
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Open a MySQL client to staging via the tunnel
mysql-staging: ## Open MySQL client against staging via tunnel (requires db-tunnel-staging-start)
	@command -v aws >/dev/null 2>&1 || { echo "❌ aws CLI not found. Install and configure AWS credentials."; exit 1; }
	@command -v jq >/dev/null 2>&1 || { echo "❌ jq not found. Please install jq."; exit 1; }
	@command -v mysql >/dev/null 2>&1 || { echo "❌ mysql client not found. Install mysql-client."; exit 1; }
	@SECRET_JSON=$$(aws --region $(AWS_REGION) secretsmanager get-secret-value --secret-id $(STAGING_SECRET_ARN) --query SecretString --output text); \
	DB_USER=$$(echo "$$SECRET_JSON" | jq -r '.username'); \
	DB_PASSWORD=$$(echo "$$SECRET_JSON" | jq -r '.password'); \
	DB_NAME=$$(echo "$$SECRET_JSON" | jq -r '.dbname // .database'); \
	echo "🐬 Connecting mysql to 127.0.0.1:$(LOCAL_DB_TUNNEL_PORT) as $$DB_USER to $$DB_NAME"; \
	mysql -h 127.0.0.1 -P $(LOCAL_DB_TUNNEL_PORT) -u "$$DB_USER" -p"$$DB_PASSWORD" "$$DB_NAME"

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
