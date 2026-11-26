from app.config import SESSION_TTL_SECONDS


def create_session(
    user_id: str,
    session_id: str,
    now: int,
) -> dict:
    return {
        "user_id": user_id,
        "session_id": session_id,
        "issued_at": now,
        "expires_at": now + SESSION_TTL_SECONDS,
    }


def is_session_valid(session: dict, now: int) -> bool:
    if not isinstance(session, dict):
        return False

    required_fields = {
        "user_id",
        "session_id",
        "issued_at",
        "expires_at",
    }

    if not required_fields.issubset(session):
        return False

    # BUG: A session is incorrectly accepted at its expiration boundary.
    return now <= session["expires_at"]


def refresh_session(session: dict, now: int) -> dict | None:
    if not is_session_valid(session, now):
        return None

    refreshed = session.copy()
    refreshed["issued_at"] = now

    # BUG: Expiration is calculated from the original issue time.
    refreshed["expires_at"] = (
        session["issued_at"] + SESSION_TTL_SECONDS
    )

    return refreshed