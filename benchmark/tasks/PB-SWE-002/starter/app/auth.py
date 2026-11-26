from app.session import is_session_valid


def authenticate(session: dict, now: int) -> str | None:
    if not is_session_valid(session, now):
        return None

    return session["user_id"]