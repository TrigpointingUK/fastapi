# Always Run CI Checks Before Committing

## CRITICAL RULE: Local CI Validation Required

Before making **any** git commit, you MUST follow this sequence:

### 1. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2. Run Complete CI Suite
```bash
make ci
```

### 3. Only Commit if All Checks Pass
The `make ci` command must complete successfully with:
- ✅ **black** - Code formatting
- ✅ **isort** - Import sorting
- ✅ **flake8** - Code linting
- ✅ **mypy** - Type checking
- ✅ **bandit** - Security scanning
- ⚠️ **safety** - Dependency vulnerabilities (warnings allowed)
- ✅ **pytest** - All tests passing

### 4. Why This Rule Exists
- **Prevents CI failures** in GitHub Actions
- **Maintains code quality** standards
- **Saves time** by catching issues early
- **Ensures consistency** between local and CI environments

### 5. No Exceptions
This rule applies to:
- Feature commits
- Bug fixes
- Documentation changes
- Configuration updates
- Any code modification

**Always run `make ci` before `git commit`** - no exceptions!
