# X-Ray and uvloop Compatibility

## Issue

AWS X-Ray SDK's `AsyncContext` is incompatible with **uvloop**, the high-performance event loop implementation used by `uvicorn[standard]`.

## Error

```
TypeError: task_factory() got an unexpected keyword argument 'context'
```

This occurs during application startup when X-Ray tries to configure `AsyncContext` with uvloop.

## Solution

**Two-part solution:**

1. **Use default `ThreadLocalContext`** instead of `AsyncContext` (uvloop compatible)
2. **Use manual segment management** (`begin_segment`/`end_segment`) instead of context managers

### Why This Works

1. **ThreadLocalContext + Manual segment management**: Using `begin_segment()`/`end_segment()` instead of context managers allows ThreadLocalContext to work correctly across async boundaries
2. **FastAPI's request-scoped pattern**: Each HTTP request is handled independently
3. **Middleware creates top-level segments**: `XRayMiddleware` manually manages segment lifecycle
4. **Decorators create subsegments**: Within each request, `@trace_function` and `in_subsegment_safe()` create subsegments
5. **Context manager pattern doesn't work**: The `with xray_recorder.capture()` pattern loses context across `await` in async middleware

### Configuration

**Tracing setup** (`app/core/tracing.py`):
```python
xray_recorder.configure(
    service=settings.XRAY_SERVICE_NAME,
    sampling=True,
    daemon_address=daemon_address,
    # context=AsyncContext(),  # ❌ Incompatible with uvloop
    context_missing="LOG_ERROR",  # Use default ThreadLocalContext ✓
)
```

**Middleware** (`app/core/xray_middleware.py`):
```python
# ❌ DON'T use context manager - loses context in async
# with xray_recorder.capture(segment_name) as segment:
#     response = await call_next(request)

# ✓ DO use manual segment management
segment = xray_recorder.begin_segment(name=service_name)
try:
    response = await call_next(request)
    return response
finally:
    xray_recorder.end_segment()
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
