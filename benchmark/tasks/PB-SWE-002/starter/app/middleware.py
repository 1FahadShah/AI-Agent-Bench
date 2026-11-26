def require_authentication(session: dict, now: int) -> dict:
    if not isinstance(session, dict):
        return {
            "authenticated": False,
            "user_id": None,
        }

    # BUG: Middleware implements its own expiration policy.
    # This can diverge from the shared authentication implementation.
    authenticated = (
        "user_id" in session
        and "expires_at" in session
        and now < session["expires_at"]
    )

    return {
        "authenticated": authenticated,
        "user_id": session.get("user_id") if authenticated else None,
    }