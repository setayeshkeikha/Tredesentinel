"""
Pure unit tests for the security module — no DB, no FastAPI app needed.
The critical property under test is the type isolation between access and
refresh tokens: a refresh token must never be usable as an access token
even though both are signed with the same secret, and vice versa.
"""
import time

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_decodes_to_subject():
    token = create_access_token(subject="user-123")
    assert decode_access_token(token) == "user-123"


def test_refresh_token_decodes_to_subject():
    token = create_refresh_token(subject="user-123")
    assert decode_refresh_token(token) == "user-123"


def test_refresh_token_rejected_as_access_token():
    refresh = create_refresh_token(subject="user-123")
    assert decode_access_token(refresh) is None


def test_access_token_rejected_as_refresh_token():
    access = create_access_token(subject="user-123")
    assert decode_refresh_token(access) is None


def test_expired_access_token_is_rejected():
    # expires_minutes accepts a float in practice via timedelta; use a
    # negative value to produce an already-expired token deterministically
    # instead of sleeping in the test.
    token = create_access_token(subject="user-123", expires_minutes=-1)
    assert decode_access_token(token) is None


def test_garbage_token_is_rejected():
    assert decode_access_token("not.a.valid.jwt") is None
    assert decode_refresh_token("") is None
