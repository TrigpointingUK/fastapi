# Performance Profiling with pyinstrument

This FastAPI application includes integrated performance profiling using [pyinstrument](https://github.com/joerick/pyinstrument).

## Overview

The profiling middleware allows you to profile any API endpoint to identify performance bottlenecks and optimise your code. It supports two output formats:

1. **HTML** - Quick, interactive profiling report for immediate viewing
2. **Speedscope JSON** - Detailed flamegraph data for visualisation in [speedscope.app](https://www.speedscope.app/)

## Security

**Important:** Profiling is **only enabled in development and staging environments** for security reasons. The middleware automatically prevents profiling in production, even if the `PROFILING_ENABLED` setting is set to `true`.

Allowed environments:
- `development`
- `staging`
- `local`

Disabled environments:
- `production`
- Any other environment name

## Configuration

Add these environment variables to your `.env` file:

```bash
# Enable profiling middleware
PROFILING_ENABLED=true

# Default output format: "html" or "speedscope"
PROFILING_DEFAULT_FORMAT=html
```

## Usage

### Quick HTML Report

Add `?profile=1` (or `?profile=html`) to any API endpoint:

```bash
# Example: Profile the trigs endpoint
curl "http://localhost:8000/v1/trigs?profile=1"

# Example: Profile a specific trig endpoint
curl "http://localhost:8000/v1/trigs/12345?profile=html"
```

This returns an interactive HTML page showing:
- Call hierarchy
- Time spent in each function
- Percentage of total time
- Line-by-line profiling data

### Speedscope JSON (Flamegraph)

Add `?profile=speedscope` (or `?profile=json`) to any API endpoint:

```bash
# Example: Get speedscope JSON
curl "http://localhost:8000/v1/trigs?profile=speedscope" -o profile.speedscope.json

# Upload to https://www.speedscope.app/ to visualise
```

The speedscope format provides:
- Interactive flamegraphs
- Time-series visualisation
- Function call stacks
- Statistical summaries

### Using with Other Query Parameters

Profiling parameters can be combined with other query parameters:

```bash
# Profile a search query
curl "http://localhost:8000/v1/trigs?limit=10&offset=0&profile=1"

# Profile with authentication
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/users/me?profile=speedscope"
```

## Local Development

1. **Enable profiling** in your `.env`:
   ```bash
   PROFILING_ENABLED=true
   ENVIRONMENT=development
   ```

2. **Start the development server**:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

3. **Profile an endpoint** in your browser:
   ```
   http://localhost:8000/v1/trigs?profile=1
   ```

## Staging Environment

Profiling can also be enabled in staging for pre-production performance testing:

1. Set environment variables:
   ```bash
   PROFILING_ENABLED=true
   ENVIRONMENT=staging
   ```

2. Access with the profile parameter as shown above

## Production

Profiling is **disabled in production** regardless of the `PROFILING_ENABLED` setting. If you attempt to enable it, you'll see a warning in the logs:

```
Profiling disabled in production environment for security
```

## Interpreting Results

### HTML Output

The HTML report shows:
- **Function names** - What code was running
- **Time (seconds)** - How long each function took
- **% of total** - Proportion of total request time
- **Call hierarchy** - Parent/child function relationships

Look for:
- Functions taking >10% of total time
- Unexpected function calls
- Deep call stacks (possible recursion issues)
- Database query patterns

### Speedscope Flamegraph

Upload the JSON file to https://www.speedscope.app/ and:
- **Wider bars** = more time spent
- **Stack height** = call depth
- **Colour** = different files/modules
- Use the timeline view to see execution over time

## Best Practices

1. **Profile realistic workloads** - Use representative data sizes and query patterns
2. **Profile multiple times** - Results can vary; look for consistent patterns
3. **Profile before and after** - Measure improvements from optimisations
4. **Don't profile in production** - Use staging for pre-deployment testing
5. **Use speedscope for complex issues** - The flamegraph view is excellent for deep analysis

## Examples

### Finding Slow Database Queries

```bash
# Profile a complex query
curl "http://localhost:8000/v1/trigs?limit=100&profile=1" > profile.html
```

Look for time spent in:
- SQLAlchemy query construction
- Database connection/execution
- Result serialisation

### Finding Memory Hotspots

```bash
# Profile an endpoint that returns large datasets
curl "http://localhost:8000/v1/photos?limit=1000&profile=speedscope" -o photos.json
```

Upload to speedscope and look for:
- Repeated object creation
- Large data transformations
- JSON serialisation overhead

### Comparing Endpoints

```bash
# Profile two similar endpoints
curl "http://localhost:8000/v1/trigs/12345?profile=1" > trig-old.html
# ... make optimisations ...
curl "http://localhost:8000/v1/trigs/12345?profile=1" > trig-new.html
```

## Troubleshooting

### Profiling Not Working

1. Check environment variable:
   ```bash
   echo $PROFILING_ENABLED
   ```

2. Verify environment is allowed:
   ```bash
   echo $ENVIRONMENT
   ```

3. Check application logs for warnings

### Performance Impact

Profiling adds overhead (typically 10-30%). This is acceptable for development/staging but **must not** be used in production with real user traffic.

### Large Profile Data

For very long-running requests, profile data can be large (several MB). Consider:
- Profiling specific parts of the code
- Using shorter test cases
- Downloading instead of viewing in browser

## Further Reading

- [pyinstrument documentation](https://pyinstrument.readthedocs.io/)
- [speedscope.app guide](https://github.com/jlfwong/speedscope)
- [Python profiling guide](https://docs.python.org/3/library/profile.html)
