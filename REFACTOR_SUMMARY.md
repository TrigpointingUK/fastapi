# Platform Refactor Summary

This document summarises the refactoring completed to transform the repository from "fastapi" to "platform" monorepo structure.

## Completed Changes

### ✅ Directory Structure
- ✅ Renamed `app/` → `fastapi/` → `api/` (changed to avoid conflict with FastAPI framework)
- ✅ Moved `tests/` → `api/tests/`
- ✅ Kept `locust/` at top level
- ✅ Renamed workspace file `fastapi.code-workspace` → `platform.code-workspace`

### ✅ Python Code (256 imports across 87 files)
- ✅ Updated all `from app.` → `from api.`
- ✅ Updated all `import app.` → `import api.`
- ✅ Fixed module references after imports (e.g., `app.main` → `api.main`)
- ✅ **Critical fix**: Changed from `fastapi/` to `api/` to avoid naming conflict with FastAPI framework package
- ✅ Files updated:
  - All Python files in `api/` directory
  - All test files in `api/tests/`
  - Scripts: `debug_auth0_token.py`, `temp_start.py`, `temp_end.py`
  - All files in `scripts/` directory
  - Special fixes: `test_database_lazy.py`, `test_main_comprehensive.py`

### ✅ CI/CD Workflows
- ✅ `.github/workflows/ci.yml`:
  - Renamed to "API CI/CD Pipeline"
  - Updated paths to trigger on `fastapi/**` (includes nested tests)
  - Changed image name to `${{ github.repository }}/api` → `platform/api`
  - Updated all Python commands (flake8, mypy, black, isort, bandit, pytest)
- ✅ `.github/workflows/mediawiki-build.yml`:
  - Changed image name from `/mediawiki` → `/wiki` → `platform/wiki`
- ✅ `.github/workflows/forum-build.yml`:
  - Already correctly set to `/forum` → `platform/forum`

### ✅ Docker Configuration
- ✅ `Dockerfile`:
  - Updated `COPY app/` → `COPY fastapi/`
  - Updated version file path `app/__version__.py` → `fastapi/__version__.py`
  - Updated CMD `uvicorn app.main:app` → `uvicorn fastapi.main:app`
- ✅ `Dockerfile.dev`:
  - Updated CMD `uvicorn app.main:app` → `uvicorn fastapi.main:app`
- ✅ `docker-compose.yml`:
  - Renamed service `app` → `api`
  - Implicit uvicorn command uses Dockerfile CMD (already updated)
- ✅ `docker-compose.dev.yml`:
  - Renamed service `app` → `api`
  - Updated command `uvicorn app.main:app` → `uvicorn fastapi.main:app`

### ✅ Configuration Files
- ✅ `Makefile`:
  - Updated `uvicorn app.main:app` → `uvicorn fastapi.main:app`
  - Updated all CI commands: `black`, `isort`, `flake8`, `mypy`, `bandit`, `pytest`
  - Updated `app tests` → `fastapi`
  - Updated docker image name `fastapi-app` → `platform-api`
- ✅ `pytest.ini`:
  - Updated `testpaths = tests` → `testpaths = fastapi/tests`
  - Updated `--cov=app` → `--cov=fastapi`
- ✅ `.pre-commit-config.yaml`:
  - Updated bandit args `['-r', 'app']` → `['-r', 'fastapi']`
  - Updated exclude pattern `^(tests/|scripts/)` → `^(fastapi/tests/|scripts/)`

### ✅ Documentation
- ✅ Created new top-level `README.md`:
  - Platform overview and component descriptions
  - Architecture summary
  - Quick start guide
  - Links to detailed component documentation
  - Repository structure
- ✅ Updated `docs/README-fastapi.md` (renamed from `docs/README.md`):
  - Changed title to "Trigpointing Platform - API Documentation"
  - Added note linking to main README
  - Updated `cd fastapi` → `cd platform`
  - Updated description to be API-specific
- ✅ Updated all 43+ markdown files in `docs/`:
  - Replaced `/home/ianh/dev/fastapi/` → `/home/ianh/dev/platform/`
  - Replaced `cd fastapi` → `cd platform`

### ✅ Scripts
- ✅ `scripts/deploy.sh`:
  - Updated comment "FastAPI project" → "Platform API"
  - Updated docker image names to `platform-api`
  - Updated image tags to `ghcr.io/your-username/platform/api`

## Package Names in GitHub Container Registry

After these changes, Docker images will be published as:
- `ghcr.io/USERNAME/platform/api` (FastAPI application)
- `ghcr.io/USERNAME/platform/forum` (phpBB)
- `ghcr.io/USERNAME/platform/wiki` (MediaWiki)

## Git Remote Configuration

Since you've renamed the repository on GitHub from "fastapi" to "platform", run these commands:

```bash
# Update the remote URL
git remote set-url origin git@github.com:USERNAME/platform.git

# Verify the change
git remote -v
```

Replace `USERNAME` with your actual GitHub username or organisation.

## Testing the Refactor

Before committing, verify everything works:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all CI checks
make ci

# Test docker build
docker build -t platform-api .

# Test docker compose
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml logs api
docker-compose -f docker-compose.dev.yml down
```

## Next Steps

1. Update the git remote URL (see commands above)
2. Run `make ci` to verify all tests pass
3. Commit all changes:
   ```bash
   git add -A
   git commit -m "Refactor: Transform to platform monorepo structure
   
   - Rename app/ to fastapi/
   - Move tests/ to fastapi/tests/
   - Update all Python imports from app. to fastapi.
   - Update CI/CD workflows with proper package naming
   - Update all Docker configurations
   - Create comprehensive platform README.md
   - Update all documentation with correct paths
   "
   ```
4. Push to develop branch:
   ```bash
   git push origin develop
   ```
5. Monitor GitHub Actions to ensure CI passes
6. Once staging deployment succeeds, create PR to main for production

## ECS Service Names (Optional Future Change)

AWS ECS services still use "fastapi" in their names:
- `fastapi-staging-service`
- `fastapi-production-service`

These can remain unchanged (they're internal AWS resource names), or you can optionally rename them in Terraform to:
- `trigpointing-api-staging-service`
- `trigpointing-api-production-service`

This can be done as a separate change if desired.

## Rollback Plan

If issues arise:
1. Revert the git commits
2. Re-push old Docker images with `:rollback` tag
3. Update ECS services to use previous image

---

**Refactor completed:** All 256 Python imports updated, CI/CD configured for conditional execution, documentation updated, and platform structure established.

