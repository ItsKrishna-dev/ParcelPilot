from fastapi import Header, HTTPException
from app.auth.mock_auth import authenticate, Session


def get_current_session(authorization: str = Header(default="")) -> Session:
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing session token.")
    try:
        return authenticate(token)
    except KeyError:
        raise HTTPException(status_code=401, detail="Unknown session token.")


def require_role(session: Session, allowed_roles: list[str]):
    if session.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=f"Role '{session.role}' is not permitted for this action "
                    f"(requires one of {allowed_roles}).",
        )
