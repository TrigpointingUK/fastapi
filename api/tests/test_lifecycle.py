"""
Tests for lifecycle helper headers and OpenAPI extras.
"""

from fastapi import APIRouter, FastAPI

from api.api.lifecycle import lifecycle, openapi_lifecycle


def _build_app():
    app = FastAPI()
    router = APIRouter()

    @router.get(
        "/alpha",
        dependencies=[lifecycle("alpha", note="try it")],
        openapi_extra=openapi_lifecycle("alpha", note="try it"),
    )
    def alpha():
        return {"ok": True}

    @router.get(
        "/deprecated",
        dependencies=[lifecycle("deprecated", sunset="Wed, 21 Oct 2026 07:28:00 GMT")],
        openapi_extra=openapi_lifecycle(
            "deprecated", sunset="Wed, 21 Oct 2026 07:28:00 GMT"
        ),
    )
    def deprecated():
        return {"ok": True}

    app.include_router(router)
    return app


def test_lifecycle_headers_and_openapi():
    from fastapi.testclient import TestClient

    app = _build_app()
    client = TestClient(app)

    # Alpha endpoint: check headers and OpenAPI extras
    r = client.get("/alpha")
    assert r.status_code == 200
    assert r.headers.get("X-API-Lifecycle") == "alpha"
    assert r.headers.get("X-API-Lifecycle-Note") == "try it"

    schema = client.get("/openapi.json").json()
    alpha_get = schema["paths"]["/alpha"]["get"]
    assert alpha_get.get("x-lifecycle") == "alpha"
    assert alpha_get.get("x-lifecycle-note") == "try it"

    # Deprecated endpoint: Deprecation + Sunset headers and OpenAPI x-sunset
    r2 = client.get("/deprecated")
    assert r2.status_code == 200
    assert r2.headers.get("X-API-Lifecycle") == "deprecated"
    assert r2.headers.get("Deprecation") == "true"
    assert r2.headers.get("Sunset") == "Wed, 21 Oct 2026 07:28:00 GMT"

    dep_get = schema["paths"]["/deprecated"]["get"]
    assert dep_get.get("x-lifecycle") == "deprecated"
    assert dep_get.get("x-sunset") == "Wed, 21 Oct 2026 07:28:00 GMT"
