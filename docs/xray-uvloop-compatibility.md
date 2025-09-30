# X-Ray and uvloop Compatibility

## Issue

AWS X-Ray SDK's `AsyncContext` is incompatible with **uvloop**, the high-performance event loop implementation used by `uvicorn[standard]`.

## Error

```
TypeError: task_factory() got an unexpected keyword argument 'context'
```

This occurs during application startup when X-Ray tries to configure `AsyncContext` with uvloop.

## Solution

**Use the default `ThreadLocalContext`** instead of `AsyncContext`.

### Why This Works

1. **FastAPI's request-scoped pattern**: Each HTTP request is handled independently
2. **Middleware creates top-level segments**: `XRayMiddleware` creates a segment per request
3. **Decorators create subsegments**: Within each request, `@trace_function` and `in_subsegment_safe()` create subsegments
4. **No complex async patterns**: We're not doing cross-thread context passing or fan-out patterns that would require AsyncContext

### Configuration

```python
xray_recorder.configure(
    service=settings.XRAY_SERVICE_NAME,
    sampling=True,
    daemon_address=daemon_address,
    # context=AsyncContext(),  # ❌ Incompatible with uvloop
    context_missing="LOG_ERROR",  # Use default ThreadLocalContext ✓
)
```

## Tradeoffs

### Benefits
- ✅ **uvloop compatibility**: Keeps 30-40% performance improvement
- ✅ **Simple solution**: No complex conditional logic
- ✅ **Proven pattern**: ThreadLocalContext is the X-Ray SDK default
- ✅ **Defensive code**: All our tracing code checks for `current_segment()` and degrades gracefully

### Limitations
- ⚠️ **Background tasks**: Context won't flow to background tasks spawned from requests (but we don't do this currently)
- ⚠️ **Cross-thread operations**: Context is thread-local (but FastAPI handles requests in single threads)
- ⚠️ **Fan-out patterns**: Won't work with complex async fan-out patterns (not applicable to our use case)

## Testing

Verified that tracing works correctly:
- [x] HTTP requests create segments
- [x] Subsegments nest properly (DB queries, image operations)
- [x] Async endpoints work correctly
- [x] No context loss within single request
- [x] Graceful degradation when segment unavailable

## Future Considerations

If we need more sophisticated async tracing in the future, consider:

1. **OpenTelemetry**: Modern standard with better async support and uvloop compatibility
2. **Custom context manager**: Implement a uvloop-compatible async context (complex)
3. **Disable uvloop**: Only as last resort (significant performance cost)

## References

- [AWS X-Ray SDK Documentation](https://docs.aws.amazon.com/xray-sdk-for-python/latest/reference/)
- [uvloop GitHub](https://github.com/MagicStack/uvloop)
- FastAPI runs requests in ThreadPoolExecutor for sync endpoints, asyncio for async endpoints
