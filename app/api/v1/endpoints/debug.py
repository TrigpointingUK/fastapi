from typing import Optional

from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import auth0_validator, extract_scopes
from app.crud.user import get_user_by_auth0_id, get_user_by_email, get_user_by_name
from app.schemas.user import Auth0UserInfo
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.get("/auth0", response_model=Auth0UserInfo)
def get_auth0_debug(
    credentials=Depends(security),
    db: Session = Depends(get_db),
):
    """
    Debug Auth0 token: echoes token claims and related DB mapping info.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = auth0_validator.validate_auth0_token(credentials.credentials)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type = token_payload.get("token_type", "auth0")
    auth0_user_id = token_payload.get("auth0_user_id") or token_payload.get("sub", "")

    database_user_found = False
    database_user_id: Optional[int] = None
    database_username: Optional[str] = None
    database_email: Optional[str] = None

    if token_type == "auth0" and auth0_user_id:  # nosec B105
        user = get_user_by_auth0_id(db, auth0_user_id=auth0_user_id)
        if user:
            database_user_found = True
            database_user_id = int(user.id)
            database_username = str(user.name)
            database_email = str(user.email) if user.email else None
        else:
            email = token_payload.get("email")
            display_name = token_payload.get("nickname") or token_payload.get("name")
            if email:
                user = get_user_by_email(db, email)
                if user:
                    database_user_found = True
                    database_user_id = int(user.id)
                    database_username = str(user.name)
                    database_email = str(user.email) if user.email else None
            if not database_user_found and display_name:
                user = get_user_by_name(db, display_name)
                if user:
                    database_user_found = True
                    database_user_id = int(user.id)
                    database_username = str(user.name)
                    database_email = str(user.email) if user.email else None

    return Auth0UserInfo(
        auth0_user_id=auth0_user_id,
        email=token_payload.get("email"),
        # Removed username field; rely on nickname/name
        nickname=token_payload.get("nickname"),
        name=token_payload.get("name"),
        given_name=token_payload.get("given_name"),
        family_name=token_payload.get("family_name"),
        email_verified=token_payload.get("email_verified"),
        token_type=token_type,
        audience=token_payload.get("aud"),
        issuer=token_payload.get("iss"),
        expires_at=token_payload.get("exp"),
        scopes=list(extract_scopes(token_payload)) if token_payload else [],
        database_user_found=database_user_found,
        database_user_id=database_user_id,
        database_username=database_username,
        database_email=database_email,
    )


@router.get("/xray")
def debug_xray():
    """
    Debug X-Ray tracing functionality under /v1/debug/xray.
    Requires OAuth2 unless disabled by OpenAPI config.
    """
    xray_enabled = settings.XRAY_ENABLED

    if not xray_enabled:
        return {"error": "X-Ray is not enabled"}

    debug_info = {
        "xray_enabled": xray_enabled,
        "service_name": settings.XRAY_SERVICE_NAME,
        "sampling_rate": settings.XRAY_SAMPLING_RATE,
        "daemon_address": settings.XRAY_DAEMON_ADDRESS,
    }

    try:
        from aws_xray_sdk.core import xray_recorder

        # Get recorder info
        debug_info["recorder_type"] = type(xray_recorder).__name__
        debug_info["recorder_service"] = getattr(xray_recorder, "service", "not_set")
        debug_info["recorder_daemon_address"] = getattr(
            xray_recorder, "daemon_address", "not_set"
        )

        # Try to create a simple trace manually
        segment = xray_recorder.begin_segment("debug_xray_test")

        if segment:
            segment.put_annotation("test", "debug")
            segment.put_metadata(
                "debug_info",
                {
                    "service_name": settings.XRAY_SERVICE_NAME,
                    "sampling_rate": settings.XRAY_SAMPLING_RATE,
                    "daemon_address": settings.XRAY_DAEMON_ADDRESS,
                },
            )

            result = {
                "status": "success",
                "message": "X-Ray trace created successfully",
                "trace_id": segment.trace_id,
                "segment_id": segment.id,
                "debug_info": debug_info,
            }

            xray_recorder.end_segment()
            return result
        else:
            return {"error": "No segment created", "debug_info": debug_info}

    except Exception as e:  # pragma: no cover - debug-only endpoint
        return {
            "error": f"X-Ray error: {str(e)}",
            "type": type(e).__name__,
            "debug_info": debug_info,
        }
