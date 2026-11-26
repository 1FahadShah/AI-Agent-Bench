
from app.auth import authenticate
from app.middleware import require_authentication
from app.session import create_session, is_session_valid, refresh_session


def test_session_is_valid_before_expiration():
    session = create_session("user-1", "session-1", 1000)

    assert is_session_valid(session, 4599) is True


def test_session_is_invalid_at_expiration_boundary():
    session = create_session("user-1", "session-1", 1000)

    assert is_session_valid(session, 4600) is False


def test_authentication_rejects_expired_session():
    session = create_session("user-1", "session-1", 1000)

    assert authenticate(session, 4600) is None


def test_authentication_accepts_valid_session():
    session = create_session("user-1", "session-1", 1000)

    assert authenticate(session, 2000) == "user-1"


def test_middleware_and_authentication_agree():
    session = create_session("user-1", "session-1", 1000)

    middleware_result = require_authentication(session, 2000)
    authenticated_user = authenticate(session, 2000)

    assert middleware_result["authenticated"] is True
    assert middleware_result["user_id"] == authenticated_user


def test_refresh_updates_expiration_from_refresh_time():
    session = create_session("user-1", "session-1", 1000)

    refreshed = refresh_session(session, 2000)

    assert refreshed is not None
    assert refreshed["issued_at"] == 2000
    assert refreshed["expires_at"] == 5600


def test_refresh_preserves_session_and_user_identity():
    session = create_session("user-1", "session-1", 1000)

    refreshed = refresh_session(session, 2000)

    assert refreshed["user_id"] == "user-1"
    assert refreshed["session_id"] == "session-1"


def test_expired_session_cannot_be_refreshed():
    session = create_session("user-1", "session-1", 1000)

    assert refresh_session(session, 4600) is None


def test_refresh_does_not_mutate_original_session():
    session = create_session("user-1", "session-1", 1000)
    original = session.copy()

    refresh_session(session, 2000)

    assert session == original


def test_invalid_session_is_rejected():
    assert is_session_valid({}, 1000) is False


def test_middleware_rejects_expired_session():
    session = create_session("user-1", "session-1", 1000)

    result = require_authentication(session, 4600)

    assert result == {
        "authenticated": False,
        "user_id": None,
    }

def test_middleware_rejects_session_missing_session_id():
    session = {
        "user_id": "user-1",
        "issued_at": 1000,
        "expires_at": 4600,
    }

    authenticated_user = authenticate(session, 2000)
    middleware_result = require_authentication(session, 2000)

    assert authenticated_user is None

    assert middleware_result == {
        "authenticated": False,
        "user_id": None,
    }