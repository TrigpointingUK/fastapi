# Strict Pre-Push Validation Rule

## 🚨 CRITICAL: Pre-Push Validation Required

**MANDATORY**: Before pushing to `main` or `develop` branches, you MUST run and pass ALL of the following checks locally:

### Required Command Sequence
```bash
# ALWAYS run this complete sequence before ANY push to main/develop:
source venv/bin/activate && make ci
```

### What `make ci` Validates
1. **Black Formatting**: `black --check app tests`
2. **Import Sorting**: `isort --check-only app tests`
3. **Linting**: `flake8 app tests`
4. **Type Checking**: `mypy app --ignore-missing-imports` (run twice)
5. **Security Scan**: `bandit -r app`
6. **Dependency Scan**: `safety check` (non-blocking but reported)
7. **Test Suite**: `pytest` (all tests must pass)

### Branch Protection Rules

#### For `main` branch:
- NEVER push directly to main
- All changes must go through develop → main via pull request
- CI must pass completely before merge

#### For `develop` branch:
- MUST run `make ci` locally before every push
- ALL checks must pass (exit code 0) except safety (which is informational)
- If ANY check fails, fix issues before pushing

### Enforcement Actions

#### If you attempt to push without running `make ci`:
1. **STOP** the push immediately
2. Run `make ci` locally
3. Fix ALL reported issues
4. Only then proceed with the push

#### If `make ci` fails:
1. **DO NOT PUSH** until all issues are resolved
2. Fix formatting: `black app tests && isort app tests`
3. Fix linting errors reported by flake8
4. Fix type errors reported by mypy
5. Fix security issues if possible
6. Ensure all tests pass
7. Re-run `make ci` until it passes completely

### Quick Fix Commands

```bash
# Auto-fix formatting and imports
black app tests && isort app tests

# Check what needs manual fixing
flake8 app tests
mypy app --ignore-missing-imports
pytest --tb=short

# Full validation
make ci
```

### Exception Handling
- **NO EXCEPTIONS** for main branch
- **NO EXCEPTIONS** for develop branch
- Emergency hotfixes must still pass basic linting and tests
- If CI is broken, fix CI first, then make changes

### Benefits
- Prevents GitHub Actions failures
- Maintains code quality standards
- Reduces debugging time
- Ensures consistent development experience
- Protects production deployments

## 🔒 This Rule is NON-NEGOTIABLE

Breaking this rule causes:
- ❌ Failed GitHub Actions
- ❌ Blocked deployments
- ❌ Development delays
- ❌ Technical debt accumulation

**Remember**: `make ci` locally = GitHub Actions success ✅
# Test CI enforcement system is working
